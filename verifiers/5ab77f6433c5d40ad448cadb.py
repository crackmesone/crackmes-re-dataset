import random
import struct

# Hash table used in HashData
hashTbl = [
    0xBC, 0x2A, 0x66, 0x57, 0x95, 0x14, 0x6A, 0x11,
    0xDE, 0x3F, 0x0A, 0x0A, 0xB0, 0xEB, 0x57, 0xA8,
    0x6B, 0x69, 0xD3, 0x88, 0x01, 0x82, 0x77, 0x73,
    0xE8, 0x20, 0xF7, 0xC5, 0x21, 0x13, 0x4D, 0xB5,
    0x92, 0xAD, 0xED, 0xD3, 0x78, 0x2F, 0x7B, 0xDF,
    0x42, 0x15, 0xCF, 0xB3, 0xBA, 0xE2, 0x24, 0x81,
    0x54, 0xC8, 0xE6, 0xD0, 0x11, 0xC4, 0x10, 0xF8,
    0xE7, 0xD1, 0x71, 0x3A, 0xA6, 0xCB, 0x64, 0xB4,
    0x77, 0x6A, 0x3A, 0xC8, 0x85, 0x35, 0xFC, 0xD4,
    0x07, 0x07, 0xA1, 0x07, 0x38, 0x69, 0x26, 0x9A,
    0x71, 0x0E, 0x86, 0x36, 0xD1, 0x80, 0xE0, 0xE3,
    0x42, 0xAE, 0xE3, 0xBC, 0x94, 0x80, 0xE4, 0xD0,
    0x23, 0x42, 0xBE, 0x72, 0xE7, 0xE0, 0xE8, 0x94,
    0x2F, 0x5E, 0xBC, 0x30, 0xC9, 0x1D, 0x83, 0x46,
    0x2E, 0x97, 0x8E, 0x58, 0xC0, 0x15, 0x59, 0x06,
    0xAC, 0x6A, 0x6E, 0x84, 0x7C, 0x25, 0x01, 0xC3,
    0x6B, 0x93, 0xAA, 0x18, 0x0F, 0x96, 0x0F, 0x4E,
    0xC5, 0xFA, 0x00, 0x07, 0xA9, 0x87, 0x9B, 0x77,
    0x26, 0x6D, 0xD1, 0x47, 0x81, 0xC0, 0x5D, 0x31,
    0x9E, 0x0E, 0xB7, 0xB8, 0x4A, 0x6B, 0xD7, 0xC4,
    0xF3, 0x69, 0x36, 0x34, 0x8A, 0xBA, 0x5A, 0x94,
    0x9C, 0xCA, 0x5D, 0x49, 0x97, 0x8A, 0x8C, 0x1B,
    0xA3, 0xF7, 0x53, 0xB0, 0x83, 0xDB, 0x88, 0x47,
    0xF2, 0x88, 0x97, 0x90, 0x3D, 0x66, 0xDE, 0xA8,
    0x96, 0x61, 0x48, 0x2F, 0xB1, 0x0D, 0x96, 0xE3,
    0x75, 0x53, 0xB3, 0x94, 0x27, 0xDC, 0xAC, 0x97,
    0x7D, 0xE9, 0xEC, 0x99, 0xA3, 0x75, 0xAD, 0xB6,
    0x8B, 0x7B, 0x5C, 0xC6, 0x29, 0x0E, 0x92, 0x0A,
    0x3A, 0xCD, 0x46, 0x74, 0x94, 0xE1, 0x4B, 0x50,
    0x1B, 0xBC, 0xD3, 0x67, 0x7E, 0x2D, 0xA0, 0x65,
    0x84, 0xD1, 0xDD, 0x30, 0x4A, 0x52, 0x62, 0xC4,
    0x4E, 0x8F, 0xE2, 0x37, 0x28, 0x62, 0x12, 0x65
]

# Custom base64 lookup table
b64Table = "36rygbKMOph8vnNjFRwxQzeT/i1s*DPkJHmfWX9AUG2l0Ia7quoLc5dZV4SYtCEB"

# Build reverse lookup for base64 decoding
b64Reverse = {ch: i for i, ch in enumerate(b64Table)}


def hash_data(data):
    """Custom hash function over 12 bytes of data."""
    hash_val = 0xE399F10A
    tmp = 0x80
    mask_tbl = [0xFFFFFF00, 0xFFFF00FF, 0xFF00FFFF, 0x00FFFFFF]

    for i in range(1001):
        for b in data:
            idx = (tmp ^ b ^ (hash_val & 0xFF)) & 0xFF
            for j in range(4):
                tmp = hashTbl[idx]
                val = ((tmp + 5) & 0xFF) ^ idx ^ (hash_val & 0xFF)
                hash_val = (hash_val & mask_tbl[j]) | (val << (8 * j))
                hash_val = (hash_val >> 1) & 0xFFFFFFFF

    return hash_val & 0xFFFFFFFF


def custom_b64_encode(data):
    """Custom base64 encode 12 bytes -> 16 chars."""
    # data must be exactly 12 bytes (divisible by 3, no padding)
    result = []
    n = len(data) // 3
    for i in range(n):
        b0 = data[i * 3]
        b1 = data[i * 3 + 1]
        b2 = data[i * 3 + 2]
        idx0 = b0 >> 2
        idx1 = ((b0 & 3) << 4) | (b1 >> 4)
        idx2 = ((b1 & 0xF) << 2) | (b2 >> 6)
        idx3 = b2 & 0x3F
        result.append(b64Table[idx0])
        result.append(b64Table[idx1])
        result.append(b64Table[idx2])
        result.append(b64Table[idx3])
    return ''.join(result)


def custom_b64_decode(s):
    """Decode 16-char custom base64 string back to 12 bytes."""
    if len(s) != 16:
        return None
    data = []
    for i in range(4):
        c0 = b64Reverse.get(s[i * 4])
        c1 = b64Reverse.get(s[i * 4 + 1])
        c2 = b64Reverse.get(s[i * 4 + 2])
        c3 = b64Reverse.get(s[i * 4 + 3])
        if None in (c0, c1, c2, c3):
            return None
        b0 = ((c0 << 2) | (c1 >> 4)) & 0xFF
        b1 = (((c1 & 0xF) << 4) | (c2 >> 2)) & 0xFF
        b2 = (((c2 & 3) << 6) | c3) & 0xFF
        data.extend([b0, b1, b2])
    return data


def verify(name, serial):
    """
    Verify a serial key.
    The serial (key file content) format is:
      [8 hex chars][1 separator char][16 custom-base64 chars]
    Total length = 25 characters.
    The name parameter is not used in the algorithm (key is standalone / name-independent).
    """
    # ASSUMPTION: name is not used in the validation; the key is self-contained
    if len(serial) != 25:
        return False

    part1 = serial[:8]   # 8 hex chars = hash
    # serial[8] is separator (any char)
    part2 = serial[9:]   # 16 chars = custom base64 encoded 12 bytes

    # Validate part1 is valid hex
    try:
        claimed_hash = int(part1, 16)
    except ValueError:
        return False

    # Decode part2 back to 12 bytes
    data = custom_b64_decode(part2)
    if data is None:
        return False

    # Compute hash of the decoded data
    computed_hash = hash_data(data)

    return claimed_hash == computed_hash


def keygen(name):
    """
    Generate a valid serial key.
    The name parameter is ignored (algorithm is name-independent).
    """
    # ASSUMPTION: name is not used; key is standalone
    # Generate 12 random bytes
    data = [random.randint(0, 0xFF) for _ in range(12)]

    # Encode data with custom base64 -> 16 chars
    part2 = custom_b64_encode(data)

    # Hash data -> 8 hex chars
    part1 = "%08X" % hash_data(data)

    # Separator: any printable character
    separator = chr(random.randint(0x20, 0x7E))

    return part1 + separator + part2



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
