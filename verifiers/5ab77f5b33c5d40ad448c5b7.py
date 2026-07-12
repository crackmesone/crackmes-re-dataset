import struct

# arr1 from the assembly (crc_index in keygen.cpp)
arr1 = [
    0x00,0x41,0xC3,0x82,0x86,0xC7,0x45,0x04,0x4D,0x0C,0x8E,0xCF,0xCB,0x8A,0x08,0x49,
    0x9A,0xDB,0x59,0x18,0x1C,0x5D,0xDF,0x9E,0xD7,0x96,0x14,0x55,0x51,0x10,0x92,0xD3,
    0x75,0x34,0xB6,0xF7,0xF3,0xB2,0x30,0x71,0x38,0x79,0xFB,0xBA,0xBE,0xFF,0x7D,0x3C,
    0xEF,0xAE,0x2C,0x6D,0x69,0x28,0xAA,0xEB,0xA2,0xE3,0x61,0x20,0x24,0x65,0xE7,0xA6,
    0xEA,0xAB,0x29,0x68,0x6C,0x2D,0xAF,0xEE,0xA7,0xE6,0x64,0x25,0x21,0x60,0xE2,0xA3,
    0x70,0x31,0xB3,0xF2,0xF6,0xB7,0x35,0x74,0x3D,0x7C,0xFE,0xBF,0xBB,0xFA,0x78,0x39,
    0x9F,0xDE,0x5C,0x1D,0x19,0x58,0xDA,0x9B,0xD2,0x93,0x11,0x50,0x54,0x15,0x97,0xD6,
    0x05,0x44,0xC6,0x87,0x83,0xC2,0x40,0x01,0x48,0x09,0x8B,0xCA,0xCE,0x8F,0x0D,0x4C,
    0x95,0xD4,0x56,0x17,0x13,0x52,0xD0,0x91,0xD8,0x99,0x1B,0x5A,0x5E,0x1F,0x9D,0xDC,
    0x0F,0x4E,0xCC,0x8D,0x89,0xC8,0x4A,0x0B,0x42,0x03,0x81,0xC0,0xC4,0x85,0x07,0x46,
    0xE0,0xA1,0x23,0x62,0x66,0x27,0xA5,0xE4,0xAD,0xEC,0x6E,0x2F,0x2B,0x6A,0xE8,0xA9,
    0x7A,0x3B,0xB9,0xF8,0xFC,0xBD,0x3F,0x7E,0x37,0x76,0xF4,0xB5,0xB1,0xF0,0x72,0x33,
    0x7F,0x3E,0xBC,0xFD,0xF9,0xB8,0x3A,0x7B,0x32,0x73,0xF1,0xB0,0xB4,0xF5,0x77,0x36,
    0xE5,0xA4,0x26,0x67,0x63,0x22,0xA0,0xE1,0xA8,0xE9,0x6B,0x2A,0x2E,0x6F,0xED,0xAC,
    0x0A,0x4B,0xC9,0x88,0x8C,0xCD,0x4F,0x0E,0x47,0x06,0x84,0xC5,0xC1,0x80,0x02,0x43,
    0x90,0xD1,0x53,0x12,0x16,0x57,0xD5,0x94,0xDD,0x9C,0x1E,0x5F,0x5B,0x1A,0x98,0xD9
]

# Standard CRC32 table (reflected polynomial 0xEDB88320)
crc_table = [0] * 256
for i in range(256):
    c = i
    for _ in range(8):
        if c & 1:
            c = 0xEDB88320 ^ (c >> 1)
        else:
            c >>= 1
    crc_table[i] = c


def index_of_index(target):
    """Find i such that arr1[i] == target"""
    for i in range(256):
        if arr1[i] == target:
            return i
    raise ValueError(f"index_of_index: target {target} not found")


def crc_forward(C, key):
    """
    Implements the forward CRC pass as described in keygen.cpp crc_forward().
    Given a 4-byte input 'C' (the name integer) and the constant key 0xBA55E732,
    produce the 4-byte output (the serial/code).
    
    The asm loop:
      dl=4 iterations, eax starts at esp+3 (highest byte of key dword on stack)
      each iteration:
        cl = arr1[output[i+3]]
        output[i-1] ^= cl                  (but stored as index)
        output[i..i+3] ^= crc_table[cl]
      working from byte 3 down to byte 0 of the key word
    """
    # Layout: [key(4 bytes)][C(4 bytes)] => output[0..7]
    # key is little-endian at output[0..3], C at output[4..7]
    output = bytearray(8)
    struct.pack_into('<I', output, 0, key & 0xFFFFFFFF)
    struct.pack_into('<I', output, 4, C & 0xFFFFFFFF)

    for i in range(4, 0, -1):
        index = arr1[output[i + 3]]
        xorval = crc_table[index]
        dword = struct.unpack_from('<I', output, i)[0]
        dword ^= xorval
        struct.pack_into('<I', output, i, dword & 0xFFFFFFFF)
        output[i - 1] ^= index

    return struct.unpack_from('<I', output, 0)[0]


def crc_reverse(M, key):
    """
    Implements the reverse CRC pass as described in keygen.cpp crc_reverse().
    Given a 4-byte value M and constant key, produce the 4-byte result.
    This inverts crc_forward.
    """
    output = bytearray(8)
    struct.pack_into('<I', output, 0, M & 0xFFFFFFFF)

    kb = struct.pack('<I', key & 0xFFFFFFFF)

    for i in range(1, 5):
        index = kb[i - 1] ^ output[i - 1]
        output[i - 1] ^= index  # restores to kb[i-1]

        dword = struct.unpack_from('<I', output, i)[0]
        dword ^= crc_table[index]
        struct.pack_into('<I', output, i, dword & 0xFFFFFFFF)

        recovered = index_of_index(index)
        output[i + 3] = recovered

    return struct.unpack_from('<I', output, 4)[0]


def compute_serial(name_int):
    """
    The crackme takes the name as an integer (GetDlgItemInt),
    pushes 0xBA55E732 as the magic constant, then runs the loop,
    producing the serial code (also displayed as integer via SetDlgItemInt).
    
    Based on the asm, the operation is crc_forward with name=C and key=0xBA55E732.
    The result is the code displayed in the CODE field.
    """
    KEY = 0xBA55E732
    return crc_forward(name_int, KEY)


def verify(name, serial):
    """
    'name' is interpreted as an integer string (the crackme uses GetDlgItemInt).
    'serial' is the expected integer output.
    Both can be int or str.
    """
    try:
        name_int = int(name) & 0xFFFFFFFF
        serial_int = int(serial) & 0xFFFFFFFF
    except (ValueError, TypeError):
        return False
    expected = compute_serial(name_int)
    # SetDlgItemInt uses signed interpretation; mask to 32-bit for comparison
    return (expected & 0xFFFFFFFF) == (serial_int & 0xFFFFFFFF)


def keygen(name):
    """
    Given a name (integer as int or str), returns the corresponding serial integer.
    """
    name_int = int(name) & 0xFFFFFFFF
    result = compute_serial(name_int)
    return result



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
