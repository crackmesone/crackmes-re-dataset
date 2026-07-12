# Reverse-engineered from crackme_5_by_rewolf writeup by Tymon
# Protection: Modified MD5 (only H function used) + MD4
#
# The writeup describes the algorithm at a high level but does NOT provide
# the full implementation details needed to reproduce it from scratch.
# Key findings from the writeup:
#
# 1. NAME is hashed with a modified MD5 (only H function, garbage obfuscation)
#    over a fake CAST-128 sbox (2*0x37 = 110 bytes)
# 2. SN is used to fill the MD5 initial values (MD5_CTX)
# 3. The following system of equations must hold:
#    ace - bdf = ef(c-d)
#    hf - ge = c - d
#    gce - hdf = 0
#    bf - ae = 0
# 4. The solution is:
#    e = b
#    f = a
#    d = g*b
#    c = h*a
# where (for block i):
#    a = NAME_HASH[0+i]  (byte)
#    b = NAME_HASH[1+i]  (byte)
#    g = NAME_HASH[2+i]  (byte)
#    h = NAME_HASH[3+i]  (byte)
#    c = SN_HASH[0+i]    (word)
#    d = SN_HASH[2+i]    (word)
#    e = SN_HASH[5+i]    (byte)
#    f = SN_HASH[4+i]    (byte)

import hashlib
import struct

# ASSUMPTION: Standard Python MD5 is used as a placeholder for the
# 'modified MD5 with only H function'. The real crackme uses a
# heavily modified MD5 that we cannot reproduce without the binary.
# The CAST-128 sbox data is also not provided in the writeup.

# ASSUMPTION: We use standard MD5 as approximation of NAME hashing.
# The real crackme hashes 110 bytes of CAST-128 sbox with MD5_CTX
# initialized from the serial - this inversion is not fully described.

def name_hash_approx(name: str) -> bytes:
    """Approximate name hash using standard MD5 (16 bytes).
    ASSUMPTION: Real implementation uses modified MD5 with CAST-128 sbox data."""
    return hashlib.md5(name.encode('ascii')).digest()

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: This is a structural approximation only.
    Without the actual modified MD5 binary implementation and
    CAST-128 sbox data, full verification cannot be implemented.
    
    The check verifies the equation system solution:
      e = b, f = a, d = g*b (mod 2^16), c = h*a (mod 2^16)
    for each 4-byte block of the name hash.
    """
    # ASSUMPTION: serial is hex-encoded bytes of the SN hash (16 bytes = 32 hex chars)
    try:
        sn_bytes = bytes.fromhex(serial.replace('-', '').replace(' ', ''))
    except Exception:
        return False
    
    if len(sn_bytes) < 8:
        return False

    nh = name_hash_approx(name)  # 16 bytes
    
    # Check for block i=0 (the writeup describes blocks but doesn't specify count)
    # ASSUMPTION: We check the first block only (i=0)
    i = 0
    a = nh[0 + i]
    b = nh[1 + i]
    g = nh[2 + i]
    h = nh[3 + i]
    
    if len(sn_bytes) < 6:
        return False
    
    # c = word ptr SN_HASH[0+i], d = word ptr SN_HASH[2+i]
    c = struct.unpack_from('<H', sn_bytes, 0 + i)[0]
    d = struct.unpack_from('<H', sn_bytes, 2 + i)[0]
    # f = byte ptr SN_HASH[4+i], e = byte ptr SN_HASH[5+i]
    f = sn_bytes[4 + i]
    e = sn_bytes[5 + i]
    
    # Solution from writeup: e=b, f=a, d=g*b, c=h*a
    # ASSUMPTION: multiplication is standard integer (no modular reduction specified)
    expected_e = b
    expected_f = a
    expected_d = (g * b) & 0xFFFF
    expected_c = (h * a) & 0xFFFF
    
    return (e == expected_e and f == expected_f and
            c == expected_c and d == expected_d)

def keygen(name: str) -> str:
    """
    Generate serial for given name.
    ASSUMPTION: Uses approximate name hash (standard MD5 instead of modified MD5).
    ASSUMPTION: Serial is 6+ bytes encoded as hex.
    """
    nh = name_hash_approx(name)  # 16 bytes
    
    # For block i=0:
    a = nh[0]
    b = nh[1]
    g = nh[2]
    h = nh[3]
    
    # Solution: e=b, f=a, d=g*b, c=h*a
    e = b
    f = a
    d = (g * b) & 0xFFFF
    c = (h * a) & 0xFFFF
    
    # Pack as: c (word LE), d (word LE), f (byte), e (byte)
    sn_bytes = struct.pack('<HHbb', c, d, f, e)
    
    # ASSUMPTION: Pad to 16 bytes with zeros for remaining blocks
    sn_bytes = sn_bytes + b'\x00' * (16 - len(sn_bytes))
    
    return sn_bytes.hex().upper()


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
