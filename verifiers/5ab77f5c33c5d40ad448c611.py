import struct
import hashlib

# AES Rijndael S-Box
SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
]

# Translate table used in returnTransform (96 bytes, indices 0..95)
TRANSLATE_TABLE = [
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0x1E,0xFF,0x1D,0x1C,0xFF,0x1B,0x1A,0x19,0xFF,0x18,0x17,0x16,0x15,0x14,0xFF,
    0x13,0x12,0x11,0xFF,0x10,0x0F,0x0E,0x0D,0x0C,0x0B,0x0A,0xFF,0xFF,0xFF,0xFF,0xFF
]

MASK32 = 0xFFFFFFFF

def rol32(x, n):
    n = n & 31
    return ((x << n) | (x >> (32 - n))) & MASK32

def ror32(x, n):
    n = n & 31
    return ((x >> n) | (x << (32 - n))) & MASK32

def bswap32(x):
    return (((x << 24) & 0xFF000000) |
            ((x <<  8) & 0x00FF0000) |
            ((x >>  8) & 0x0000FF00) |
            ((x >> 24) & 0x000000FF))

def return_transform(t):
    """Given a value 0..30 (hash6 mod 0x1F), return the ASCII character."""
    for k in range(len(TRANSLATE_TABLE)):
        if t == TRANSLATE_TABLE[k]:
            return k
    return 0

def compute_serial(name):
    # Step 1: MD5 of name
    md5 = hashlib.md5(name.encode('latin-1')).digest()

    # Step 2: Unpack as 4 little-endian DWORDs (standard Python MD5 layout)
    d0, d1, d2, d3_orig = struct.unpack('<4I', md5)

    # Step 3: MD5sum = sum of all 4 dwords (mod 2^32)
    md5sum = (d0 + d1 + d2 + struct.unpack('<I', md5[12:16])[0]) & MASK32

    # Step 4: Setup serialHash
    sh = [0]*4
    sh[0] = d0
    sh[1] = d1
    sh[2] = d2
    sh[3] = (0xDEADC0DE - sh[0] - sh[1] - sh[2]) & MASK32

    # Step 5: XOR with MD5sum
    for i in range(4):
        sh[i] ^= md5sum

    # Step 6: S-Box substitution on each byte
    raw = bytearray()
    for i in range(4):
        raw += struct.pack('<I', sh[i])
    for i in range(16):
        raw[i] = SBOX[raw[i]]
    for i in range(4):
        sh[i] = struct.unpack('<I', bytes(raw[i*4:(i+1)*4]))[0]

    # Step 7: Apply reversed transform to each DWORD
    # Original asm forward:
    #   rol eax, 4
    #   xor eax, 0xDEADF00D
    #   bswap eax
    #   xor eax, 0xFF00FF00
    #   rol eax, 0x16
    #   xor eax, 0x12345678
    #   xor eax, 0xABCDEF00
    #   rol eax, 8
    # Reversed C: ROR(BSWAP(ROR(ROR(x,8)^0xABCDEF00^0x12345678, 0x16)^0xFF00FF00)^0xDEADF00D, 4)
    for i in range(4):
        x = sh[i]
        x = ror32(x, 8)
        x = (x ^ 0xABCDEF00 ^ 0x12345678) & MASK32
        x = ror32(x, 0x16)
        x = (x ^ 0xFF00FF00) & MASK32
        x = bswap32(x)
        x = (x ^ 0xDEADF00D) & MASK32
        x = ror32(x, 4)
        sh[i] = x

    # Step 8: Big-integer base conversion (divide 128-bit number by 0x34E63B41 repeatedly)
    DIVISOR = 0x34E63B41

    # Treat sh[0..3] as a 128-bit number with sh[0] as most-significant DWORD (after bswap)
    # The C code does BSWAP on each before using as dividend high part
    # Reconstruct the 128-bit value from bswapped dwords in sequence
    # Round 1: get hash6_1..hash6_5 from 5 divisions

    def div128_step(high32, low32, divisor):
        """Treat (high32 << 32 | low32) as 64-bit, divide by divisor, return (quotient64, remainder)"""
        val = (high32 << 32) | low32
        q = val // divisor
        r = val % divisor
        return q, r  # quotient may be 64-bit

    # The C code processes bswapped values sequentially
    # finalHash starts as BSWAP(sh[0]) (32-bit, so high=0)
    fh = bswap32(sh[0])  # 32-bit value
    sh0_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | bswap32(sh[1])
    sh1_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | bswap32(sh[2])
    sh2_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | bswap32(sh[3])
    sh3_new = fh // DIVISOR
    hash6_1 = fh % DIVISOR

    sh[0] = sh0_new & MASK32
    sh[1] = sh1_new & MASK32
    sh[2] = sh2_new & MASK32
    sh[3] = sh3_new & MASK32

    # Second pass
    fh = (sh[0] << 32) | sh[1]
    sh0_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | sh[2]
    sh1_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | sh[3]
    sh2_new = fh // DIVISOR
    hash6_2 = fh % DIVISOR

    sh[0] = sh0_new & MASK32
    sh[1] = sh1_new & MASK32
    sh[2] = sh2_new & MASK32

    # Third pass
    fh = (sh[0] << 32) | sh[1]
    sh0_new = fh // DIVISOR
    rem = fh % DIVISOR

    fh = (rem << 32) | sh[2]
    sh1_new = fh // DIVISOR
    hash6_3 = fh % DIVISOR

    sh[0] = sh0_new & MASK32
    sh[1] = sh1_new & MASK32

    # Fourth pass
    fh = (sh[0] << 32) | sh[1]
    hash6_5 = fh // DIVISOR
    hash6_4 = fh % DIVISOR

    hash_table = [hash6_1, hash6_2, hash6_3, hash6_4, hash6_5]

    # Step 9: Convert each hash to 6 base-31 digits, map via returnTransform
    serial_chars = []
    for i in range(5):
        h = hash_table[i]
        group = []
        for _ in range(6):
            group.append(chr(return_transform(h % 0x1F)))
            h //= 0x1F
        serial_chars.extend(group)
        if i < 4:
            serial_chars.append('-')

    return ''.join(serial_chars)


def keygen(name):
    return compute_serial(name)


def verify(name, serial):
    expected = compute_serial(name)
    return serial == expected



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
