# Reverse-engineered from the keygen source (main.cpp) provided in the write-up.
# The write-up is truncated before showing the full HashName() and Generate()/Test() logic,
# but enough is visible to reconstruct the core algorithm.

# The four hash tables (4 rows x 36 chars each) are fully given.
# ASSUMPTION: HashName() sums character values of the name and the result indexes into
#             the hash table rows / columns to produce serial characters.
# ASSUMPTION: The serial format and exact indexing logic are partially inferred from
#             the table structure and common patterns in similar crackmes.

HASH_TABLE = [
    # Row 0: AGMSY4BHNTZ5CIOU06DJPV17EKQW28FLRX39
    bytes([
        0x41,0x47,0x4D,0x53,0x59,0x34,0x42,0x48,0x4E,0x54,0x5A,0x35,
        0x43,0x49,0x4F,0x55,0x30,0x36,0x44,0x4A,0x50,0x56,0x31,0x37,
        0x45,0x4B,0x51,0x57,0x32,0x38,0x46,0x4C,0x52,0x58,0x33,0x39
    ]),
    # Row 1: BHNTZ5CIOU06DJPV17EKQW28FLRX39AGMSY4
    bytes([
        0x42,0x48,0x4E,0x54,0x5A,0x35,0x43,0x49,0x4F,0x55,0x30,0x36,
        0x44,0x4A,0x50,0x56,0x31,0x37,0x45,0x4B,0x51,0x57,0x32,0x38,
        0x46,0x4C,0x52,0x58,0x33,0x39,0x41,0x47,0x4D,0x53,0x59,0x34
    ]),
    # Row 2: CIOU06DJPV17EKQW28FLRX39AGMSY4BHNTZ5
    bytes([
        0x43,0x49,0x4F,0x55,0x30,0x36,0x44,0x4A,0x50,0x56,0x31,0x37,
        0x45,0x4B,0x51,0x57,0x32,0x38,0x46,0x4C,0x52,0x58,0x33,0x39,
        0x41,0x47,0x4D,0x53,0x59,0x34,0x42,0x48,0x4E,0x54,0x5A,0x35
    ]),
    # Row 3: DJPV17EKQW28FLRX39AGMSY4BHNTZ5CIOU06
    bytes([
        0x44,0x4A,0x50,0x56,0x31,0x37,0x45,0x4B,0x51,0x57,0x32,0x38,
        0x46,0x4C,0x52,0x58,0x33,0x39,0x41,0x47,0x4D,0x53,0x59,0x34,
        0x42,0x48,0x4E,0x54,0x5A,0x35,0x43,0x49,0x4F,0x55,0x30,0x36
    ]),
]

# ASSUMPTION: HashName sums all character ASCII values of the name.
def hash_name(name: str) -> int:
    h = 0
    for c in name:
        h += ord(c)
    return h

# ASSUMPTION: The serial is built by taking the hash value, splitting it into
# nibbles or bytes, and looking each up in successive rows of the hash table.
# Each index is taken mod 36 (table width) and the row cycles through 0-3.
# The number of serial characters is not explicitly stated; 8 is a common choice.
# ASSUMPTION: serial length = 8 characters, each derived from successive bytes
# of the hash (using big-endian 4-byte representation, 2 nibbles per byte).
def keygen(name: str) -> str:
    h = hash_name(name)
    serial_chars = []
    # ASSUMPTION: use 4 bytes of the hash, 2 chars per byte, 8 total chars
    # Each byte's high nibble and low nibble index into successive table rows.
    for i in range(4):
        byte_val = (h >> (8 * (3 - i))) & 0xFF
        hi = (byte_val >> 4) & 0xF
        lo = byte_val & 0xF
        row_hi = (2 * i) % 4
        row_lo = (2 * i + 1) % 4
        # ASSUMPTION: nibble indexes directly into the table (mod 36 for safety)
        serial_chars.append(chr(HASH_TABLE[row_hi][hi % 36]))
        serial_chars.append(chr(HASH_TABLE[row_lo][lo % 36]))
    return ''.join(serial_chars)

def verify(name: str, serial: str) -> bool:
    expected = keygen(name)
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
