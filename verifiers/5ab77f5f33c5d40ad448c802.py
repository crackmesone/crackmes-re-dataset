import struct
import hashlib
from Crypto.Cipher import DES

# ASSUMPTION: The 'challenge key' is a random 64-bit value displayed by the crackme to the user.
# The keygen takes that challenge key + a name, and produces a serial.
# We cannot fully replicate the crackme's verify() without knowing the challenge key it uses.
# However, we implement the full keygen logic as described.

# The custom SHA1-like hash from the writeup.
# NOTE: The writeup shows a SHA1 implementation with a BSWAP applied to each word[j] BEFORE
# the SHA1 round function, then BSWAP applied to h0..h4 at the end, then sums them.
# This is a modified/broken SHA1, not standard.

def bswap32(x):
    x = x & 0xFFFFFFFF
    return ((x >> 24) & 0xFF) | (((x >> 8) & 0xFF00)) | (((x << 8) & 0xFF0000)) | ((x << 24) & 0xFF000000)

def rotleft32(x, n):
    x = x & 0xFFFFFFFF
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def do_hash(name_str):
    """Custom broken SHA1 from the writeup: bswap each word, bswap final h values, return sum mod 2^32."""
    if isinstance(name_str, str):
        data = name_str.encode('latin-1')
    else:
        data = bytes(name_str)

    h0 = 0x67452301
    h1 = 0xEFCDAB89
    h2 = 0x98BADCFE
    h3 = 0x10325476
    h4 = 0xC3D2E1F0

    original_length = len(data)

    # Padding
    msg = bytearray(data)
    msg.append(0x80)
    # pad zeros until length % 64 == 56
    while len(msg) % 64 != 56:
        msg.append(0x00)
    # append 8-byte big-endian bit length
    bit_length = original_length * 8
    # writeup uses 6 zeros + 2 bytes (high byte then low byte of bit_length)
    # which matches standard SHA1 big-endian 64-bit length
    msg += b'\x00' * 6
    msg.append((bit_length >> 8) & 0xFF)
    msg.append(bit_length & 0xFF)

    number_of_chunks = len(msg) // 64

    for i in range(number_of_chunks):
        chunk = msg[i*64:(i+1)*64]
        word = [0]*80
        for j in range(16):
            w = (chunk[j*4+0] << 24) | (chunk[j*4+1] << 16) | (chunk[j*4+2] << 8) | chunk[j*4+3]
            # BSWAP each word before rounds (as in the writeup 'modmod!')
            word[j] = bswap32(w)
        for j in range(16, 80):
            word[j] = rotleft32(word[j-3] ^ word[j-8] ^ word[j-14] ^ word[j-16], 1)

        a, b, c, d, e = h0, h1, h2, h3, h4

        for m in range(80):
            if m <= 19:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif m <= 39:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif m <= 59:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:
                f = b ^ c ^ d
                k = 0xCA62C1D6

            temp = (rotleft32(a, 5) + f + e + k + word[m]) & 0xFFFFFFFF
            e = d
            d = c
            c = rotleft32(b, 30)
            b = a
            a = temp

        h0 = (h0 + a) & 0xFFFFFFFF
        h1 = (h1 + b) & 0xFFFFFFFF
        h2 = (h2 + c) & 0xFFFFFFFF
        h3 = (h3 + d) & 0xFFFFFFFF
        h4 = (h4 + e) & 0xFFFFFFFF

    # BSWAP final values
    h0 = bswap32(h0)
    h1 = bswap32(h1)
    h2 = bswap32(h2)
    h3 = bswap32(h3)
    h4 = bswap32(h4)

    return (h0 + h1 + h2 + h3 + h4) & 0xFFFFFFFF


PERMUTE_SEEDS = [
    0x0A20D521, 0x1800F711, 0x25E11901, 0x33C13AF1,
    0x41A15CE1, 0x4F817ED1, 0x5D61A0C1, 0x6B41C2B1,
    0x7921E4A1, 0x87020691, 0x94E22881, 0xA2C24A71,
    0xB0A26C61, 0xBE828E51, 0xCC62B041, 0xDA42D231,
    0xE822F421, 0xF6031611
]

SMAK_CONST = struct.unpack('<I', b'krmS')[0]  # little-endian 'krmS' as DWORD


def des_encrypt_ecb(block8, key8):
    """DES ECB encrypt 8-byte block with 8-byte key using pycryptodome."""
    cipher = DES.new(key8, DES.MODE_ECB)
    return cipher.encrypt(block8)


def keygen(name, challenge_key_hex, permute_seed_index=0):
    """
    Generate a serial given:
      - name: the user's name string
      - challenge_key_hex: 16 hex chars (64-bit challenge key shown by crackme)
      - permute_seed_index: index into PERMUTE_SEEDS (0..17), keygen uses GetTickCount()%18
    Returns: base64-encoded serial string
    """
    import base64

    # Parse challenge key from hex
    key_bytes = bytes.fromhex(challenge_key_hex)
    if len(key_bytes) != 8:
        raise ValueError("Challenge key must be 8 bytes (16 hex chars)")

    # Byte-swap the key (reverse first 4 pairs)
    key_list = list(key_bytes)
    for i in range(4):
        key_list[i], key_list[7-i] = key_list[7-i], key_list[i]
    key_bytes = bytes(key_list)

    # Compute hash of name
    hash_val = do_hash(name)

    # Choose permute seed
    permute_seed = PERMUTE_SEEDS[permute_seed_index % 18]

    # Form 8-byte plaintext
    left = (permute_seed ^ hash_val) & 0xFFFFFFFF
    right = (SMAK_CONST ^ hash_val) & 0xFFFFFFFF

    # Pack as little-endian DWORDs
    plaintext = struct.pack('<II', left, right)

    # DES encrypt
    ciphertext = des_encrypt_ecb(plaintext, key_bytes)

    # Base64 encode
    serial = base64.b64encode(ciphertext).decode('ascii')
    return serial


def verify(name, serial, challenge_key_hex=None):
    """
    Verify a serial for a given name.
    ASSUMPTION: The crackme generates a random challenge key and displays it to the user.
    To verify, we need the same challenge key. Without it, we try all permute seeds.
    If challenge_key_hex is provided, checks all 18 permute seeds.
    Returns True if any permute seed produces the given serial.
    """
    if challenge_key_hex is None:
        # ASSUMPTION: Cannot verify without the challenge key
        raise ValueError("Challenge key required for verification")

    import base64
    for idx in range(18):
        try:
            expected = keygen(name, challenge_key_hex, idx)
            if expected == serial:
                return True
        except Exception:
            pass
    return False



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
