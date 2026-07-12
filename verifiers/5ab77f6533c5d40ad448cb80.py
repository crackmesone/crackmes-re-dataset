import struct

# ============================================================
# sibesas_crackme_1  --  4-level serial / name+serial checker
# ============================================================
# All logic is derived from the writeup.  Where the writeup
# was truncated or ambiguous a '# ASSUMPTION:' comment marks
# the gap.
# ============================================================

# ----------------------------------------------------------
# Helper: convert an 8-char decimal string to an integer
# (the crackme calls a routine at 0x4014EC described as
#  "converts the passed number into 8-byte hex", i.e. it
#  parses the ASCII decimal string to a 32-bit integer)
# ----------------------------------------------------------
def _parse_num(s8: str) -> int:
    # ASSUMPTION: 0x4014EC simply does atoi / strtoul on
    # the 8-character decimal string.
    try:
        return int(s8) & 0xFFFFFFFF
    except ValueError:
        return 0


# ----------------------------------------------------------
# Level 1
# Serial must start with 'Bravo!!!' (first 8 bytes).
# Algorithm:
#   serial[0:4] XOR 0x53544F50  == 0x25353D12
#   serial[4:8] XOR 0x52554C45  == 0x73746D2A
# Remaining characters are not checked.
# ----------------------------------------------------------
_L1_KEY1  = 0x53544F50
_L1_CMP1  = 0x25353D12
_L1_KEY2  = 0x52554C45
_L1_CMP2  = 0x73746D2A

def _level1_expected() -> str:
    # XOR reverses itself: expected = CMP XOR KEY
    v1 = _L1_CMP1 ^ _L1_KEY1   # little-endian DWORD
    v2 = _L1_CMP2 ^ _L1_KEY2
    # pack as little-endian 32-bit integers -> bytes -> string
    b = struct.pack('<II', v1, v2)
    return b.decode('latin-1')

def verify_level1(serial: str) -> bool:
    if len(serial) < 8:
        return False
    raw = serial[:8].encode('latin-1')
    v1, v2 = struct.unpack_from('<II', raw, 0)
    return (v1 ^ _L1_KEY1 == _L1_CMP1) and (v2 ^ _L1_KEY2 == _L1_CMP2)

def keygen_level1(name: str = '') -> str:
    # name is not used in level 1
    expected = _level1_expected()
    return expected  # == 'Bravo!!!'


# ----------------------------------------------------------
# Level 2
# Format: AAAAAAAA-BBBBBBBB  (exactly 17 chars, '-' at pos 8)
# Algorithm:
#   val_a = parse(AAAAAAAA)
#   val_b = parse(BBBBBBBB)
#   (val_a XOR val_b) + 0x474F4F44  == 0x53544F50
#   => val_a XOR val_b == 0x53544F50 - 0x474F4F44 == 0x0C05000C
# ----------------------------------------------------------
_L2_TARGET = (0x53544F50 - 0x474F4F44) & 0xFFFFFFFF  # 0x0C05000C

def verify_level2(serial: str) -> bool:
    if len(serial) != 17:
        return False
    if serial[8] != '-':
        return False
    part_a = serial[0:8]
    part_b = serial[9:17]
    va = _parse_num(part_a)
    vb = _parse_num(part_b)
    return ((va ^ vb) + 0x474F4F44) & 0xFFFFFFFF == 0x53544F50

def keygen_level2(name: str = '') -> str:
    # Choose part_a = 0, then part_b must equal _L2_TARGET
    va = 0
    vb = va ^ _L2_TARGET  # 0x0C05000C = 201392140
    return f'{va:08d}-{vb:08d}'


# ----------------------------------------------------------
# Level 3  (name + serial)
# The writeup was truncated before full details were given.
# ASSUMPTION: some name-based transformation produces a key
# that the serial is checked against; exact algorithm unknown.
# ----------------------------------------------------------
def verify_level3(name: str, serial: str) -> bool:
    # ASSUMPTION: algorithm not fully described in the writeup.
    raise NotImplementedError('Level 3 algorithm not fully recovered from writeup')

def keygen_level3(name: str) -> str:
    raise NotImplementedError('Level 3 keygen not fully recovered from writeup')


# ----------------------------------------------------------
# Level 4  (name + serial)
# ASSUMPTION: algorithm not described in the writeup.
# ----------------------------------------------------------
def verify_level4(name: str, serial: str) -> bool:
    # ASSUMPTION: algorithm not described in the writeup.
    raise NotImplementedError('Level 4 algorithm not recovered from writeup')

def keygen_level4(name: str) -> str:
    raise NotImplementedError('Level 4 keygen not recovered from writeup')


# ----------------------------------------------------------
# Generic entry points (default to level 1 / level 2)
# ----------------------------------------------------------
def verify(name: str, serial: str, level: int = 1) -> bool:
    """Verify serial for the given level (1-4)."""
    if level == 1:
        return verify_level1(serial)
    elif level == 2:
        return verify_level2(serial)
    elif level == 3:
        return verify_level3(name, serial)
    elif level == 4:
        return verify_level4(name, serial)
    return False

def keygen(name: str, level: int = 1) -> str:
    """Generate a valid serial for the given level."""
    if level == 1:
        return keygen_level1(name)
    elif level == 2:
        return keygen_level2(name)
    elif level == 3:
        return keygen_level3(name)
    elif level == 4:
        return keygen_level4(name)
    raise ValueError(f'Unknown level {level}')


# ----------------------------------------------------------
# Self-test
# ----------------------------------------------------------

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
