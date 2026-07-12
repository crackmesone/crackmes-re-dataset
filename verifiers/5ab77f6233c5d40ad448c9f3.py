import struct
import hashlib

# Modified SHA-1 with custom initialization constants
# ASSUMPTION: Only the H0-H4 initialization constants are changed; the rest of SHA-1 is standard
# Custom init constants (from writeup):
# H0 = 0xD76AA478, H1 = 0xE8C7B756, H2 = 0x242070DB, H3 = 0xC1BDCEEE, H4 = 0xF57C0FAF
# Standard SHA-1 round constants K are still used: 5A827999, 6ED9EBA1, 8F1BBCDC, CA62C1C6

def rotl32(n, b):
    return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF

def modified_sha1(data: bytes) -> str:
    # Custom initialization constants
    h0 = 0xD76AA478
    h1 = 0xE8C7B756
    h2 = 0x242070DB
    h3 = 0xC1BDCEEE
    h4 = 0xF57C0FAF

    # Standard SHA-1 pre-processing
    msg = bytearray(data)
    orig_len = len(data) * 8  # bit length
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('>Q', orig_len)

    # Process each 512-bit (64-byte) chunk
    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        w = list(struct.unpack('>16I', chunk))
        for j in range(16, 80):
            w.append(rotl32(w[j-3] ^ w[j-8] ^ w[j-14] ^ w[j-16], 1))

        a, b, c, d, e = h0, h1, h2, h3, h4

        for j in range(80):
            if 0 <= j <= 19:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif 20 <= j <= 39:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif 40 <= j <= 59:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:
                f = b ^ c ^ d
                k = 0xCA62C1D6  # ASSUMPTION: standard 0xCA62C1D6; writeup says CA62C1C6 but standard is CA62C1D6
                # Actually writeup mentions CA62C1C6 as a search constant; standard SHA-1 uses CA62C1D6
                # Using standard SHA-1 value here
                k = 0xCA62C1D6

            temp = (rotl32(a, 5) + f + e + k + w[j]) & 0xFFFFFFFF
            e = d
            d = c
            c = rotl32(b, 30)
            b = a
            a = temp

        h0 = (h0 + a) & 0xFFFFFFFF
        h1 = (h1 + b) & 0xFFFFFFFF
        h2 = (h2 + c) & 0xFFFFFFFF
        h3 = (h3 + d) & 0xFFFFFFFF
        h4 = (h4 + e) & 0xFFFFFFFF

    return '%08X%08X%08X%08X%08X' % (h0, h1, h2, h3, h4)


def compute_hashes(name: str) -> tuple:
    """
    Compute the 5 hashes used in serial generation.
    Steps from writeup:
      hash1 = modified_sha1(name)
      take first len(name) chars of hash1, repeat 2 times -> hash2 input
      hash2 = modified_sha1(hash1[:n] * 2)
      take first len(name) chars of hash2, repeat 4 times -> hash3 input
      hash3 = modified_sha1(hash2[:n] * 4)
      take first len(name) chars of hash3, repeat 8 times -> hash4 input
      hash4 = modified_sha1(hash3[:n] * 8)
      take first len(name) chars of hash4, repeat 16 times -> hash5 input
      hash5 = modified_sha1(hash4[:n] * 16)
    """
    n = len(name)
    hash1 = modified_sha1(name.encode('ascii'))
    seg1 = hash1[:n]

    hash2 = modified_sha1((seg1 * 2).encode('ascii'))
    seg2 = hash2[:n]

    hash3 = modified_sha1((seg2 * 4).encode('ascii'))
    seg3 = hash3[:n]

    hash4 = modified_sha1((seg3 * 8).encode('ascii'))
    seg4 = hash4[:n]

    hash5 = modified_sha1((seg4 * 16).encode('ascii'))

    return hash1, hash2, hash3, hash4, hash5


def keygen(name: str) -> str:
    """
    Generate serial for a given name.
    Serial format: rhash1-rhash2-rhash3-rhash4-rhash5
    
    rhash1 = hash1[0:8]          (first 8 chars)
    rhash2 = hash2[8:16]         (8 chars from position 8)
    rhash3 = hash3[9:17][::-1]   (8 chars from position 9, reversed)
    rhash4 = hash4[24:32]        (8 chars from position 24)
    rhash5 = hash5[25:33][::-1]  (8 chars from position 25, reversed)
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long")

    hash1, hash2, hash3, hash4, hash5 = compute_hashes(name)

    rhash1 = hash1[0:8]
    rhash2 = hash2[8:16]
    rhash3 = hash3[9:17][::-1]
    rhash4 = hash4[24:32]
    rhash5 = hash5[25:33][::-1]

    serial = '%s-%s-%s-%s-%s' % (rhash1, rhash2, rhash3, rhash4, rhash5)
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    if len(name) < 4:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
    return serial.upper() == expected.upper()



# ===== standardized CLI (auto-added) =====
def _cli_norm(_x):
    if isinstance(_x, bytes):
        return _x.hex()
    if isinstance(_x, (list, tuple)):
        return " ".join(_cli_norm(_i) for _i in _x)
    return str(_x)


def _cli_main():
    import sys
    _SAMPLE = ['alice', 'bob', 'Kevin', 'test123', 'admin', 'crackme', 'john_doe', 'w1nner', 'root', 'dragon']
    argv = sys.argv[1:]
    mode = argv[0] if argv else ""
    if mode == "keygen":
        n = 0
        for _nm in _SAMPLE:
            _s = None
            for _call in (lambda: keygen(_nm), lambda: keygen()):
                try:
                    _s = _call()
                    break
                except TypeError:
                    continue
                except Exception:
                    _s = None
                    break
            if _s is None:
                continue
            _sv = _cli_norm(_s)
            print(_nm, _sv)
            n += 1
            if n >= 10:
                break
    elif mode == "verify":
        try:
            print("1" if verify(*argv[1:]) else "0")
        except Exception:
            print("0")
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\n".format(sys.argv[0]))
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
