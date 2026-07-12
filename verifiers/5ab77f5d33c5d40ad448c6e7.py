import hashlib
import struct

# Custom MD5 implementation with modified initialization constants
# Based on solution writeup by HMX0101

# Standard MD5 constants (T table) - same as RFC 1321
# The modification is ONLY in the initialization IVs and possibly some transform constants

# Modified initialization constants (from solution 2):
# Standard MD5: 67452301, EFCDAB89, 98BADCFE, 10325476
# Custom:        96E1038F, 1EB65134, 41F97CFF, 0BEFA17A

MOD32 = 0x100000000

def left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def F(x, y, z):
    return (x & y) | (~x & z)

def G(x, y, z):
    return (x & z) | (y & ~z)

def H(x, y, z):
    return x ^ y ^ z

def I(x, y, z):
    return y ^ (x | ~z)

# Standard MD5 T-table constants
T = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
    0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
    0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
    0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
    0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
    0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
    0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
    0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391,
]

# ASSUMPTION: The crackme uses the same T constants as standard MD5 but with
# modified FF round constants from the writeup. The writeup shows some modified
# T values for the FF round. We use those where shown.
# Modified FF T constants from solution writeup (first 16 FF operations):
FF_T = [
    0xA76AA478, 0xE847B756, 0x24B070DB, 0xC1EDCEEE,
    0xF57B0FAF, 0x4787C02A, 0xA8304D13, 0xFD469F01,
    0x698A98D8, 0x8B4AF7AF, 0xFFFC5BB1, 0x895CDEBE,
    0x6B901F22, 0xFB987193, 0xA67D438E, 0x49BE0821,
]

# ASSUMPTION: GG, HH, II rounds use standard T constants (not fully shown in writeup)
GG_T = [
    0xF61E2C62, 0xCA40B340, 0x265e5a51, 0xe9b6c7aa,
    0xd62f105d, 0x2441453,  0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
    0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
]

HH_T = T[32:48]  # ASSUMPTION: standard
II_T = T[48:64]  # ASSUMPTION: standard

def custom_md5(message):
    """Custom MD5 with modified init constants and some modified T values."""
    # Modified init constants
    a0 = 0x96E1038F
    b0 = 0x1EB65134
    c0 = 0x41F97CFF
    d0 = 0x0BEFA17A

    # Pre-processing: adding padding bits
    msg = bytearray(message)
    orig_len_bits = len(message) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)

    # Process each 512-bit (64-byte) chunk
    for chunk_start in range(0, len(msg), 64):
        chunk = msg[chunk_start:chunk_start + 64]
        M = struct.unpack('<16I', chunk)

        A, B, C, D = a0, b0, c0, d0

        # Round 1 (FF)
        shifts = [7, 12, 17, 22] * 4
        for i in range(16):
            f = F(B, C, D)
            temp = (A + f + M[i] + FF_T[i]) & 0xFFFFFFFF
            temp = left_rotate(temp, shifts[i])
            temp = (temp + B) & 0xFFFFFFFF
            A, B, C, D = D, temp, B, C

        # Round 2 (GG)
        shifts2 = [5, 9, 14, 20] * 4
        gg_indices = [(5*i + 1) % 16 for i in range(16)]
        for i in range(16):
            g = G(B, C, D)
            temp = (A + g + M[gg_indices[i]] + GG_T[i]) & 0xFFFFFFFF
            temp = left_rotate(temp, shifts2[i])
            temp = (temp + B) & 0xFFFFFFFF
            A, B, C, D = D, temp, B, C

        # Round 3 (HH)
        shifts3 = [4, 11, 16, 23] * 4
        hh_indices = [(3*i + 5) % 16 for i in range(16)]
        for i in range(16):
            h = H(B, C, D)
            temp = (A + h + M[hh_indices[i]] + HH_T[i]) & 0xFFFFFFFF
            temp = left_rotate(temp, shifts3[i])
            temp = (temp + B) & 0xFFFFFFFF
            A, B, C, D = D, temp, B, C

        # Round 4 (II)
        shifts4 = [6, 10, 15, 21] * 4
        ii_indices = [(7*i) % 16 for i in range(16)]
        for i in range(16):
            ii = I(B, C, D)
            temp = (A + ii + M[ii_indices[i]] + II_T[i]) & 0xFFFFFFFF
            temp = left_rotate(temp, shifts4[i])
            temp = (temp + B) & 0xFFFFFFFF
            A, B, C, D = D, temp, B, C

        a0 = (a0 + A) & 0xFFFFFFFF
        b0 = (b0 + B) & 0xFFFFFFFF
        c0 = (c0 + C) & 0xFFFFFFFF
        d0 = (d0 + D) & 0xFFFFFFFF

    digest = struct.pack('<4I', a0, b0, c0, d0)
    return digest

def digest_to_hex(digest):
    return digest.hex().upper()

def keygen(name):
    """Generate a valid serial for the given name.
    Serial format: 8chars-8chars-8chars-8chars (35 chars total including dashes)
    The dashes are at positions 8, 17, 26 (0-indexed).
    From the writeup: serial[8] + serial[17] + serial[26] == 0x87, all must be '-' (0x2D).
    0x2D * 3 = 0x87. So dashes at positions index 8,17,26.
    The serial is derived from the custom MD5 hash of the name (32 hex chars).
    We insert dashes to form the 35-char serial.
    """
    name_bytes = name.encode('latin-1')
    digest = custom_md5(name_bytes)
    hex_hash = digest_to_hex(digest)  # 32 hex chars
    # Insert dashes every 8 characters
    serial = hex_hash[0:8] + '-' + hex_hash[8:16] + '-' + hex_hash[16:24] + '-' + hex_hash[24:32]
    return serial

def verify(name, serial):
    """Verify name/serial pair."""
    # Check name length > 1
    if len(name) <= 1:
        return False
    # Check serial length == 35
    if len(serial) != 35:
        return False
    # Check serial format: dashes at positions 8, 17, 26
    if serial[8] != '-' or serial[17] != '-' or serial[26] != '-':
        return False
    # Verify the sum of chars at positions 8,17,26 (all '-' = 0x2D) == 0x87
    # (This is the crackme's check, already verified by dash check above)
    dash_sum = ord(serial[8]) + ord(serial[17]) + ord(serial[26])
    if dash_sum != 0x87:
        return False
    # Compute expected serial from custom MD5 of name
    expected = keygen(name)
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
