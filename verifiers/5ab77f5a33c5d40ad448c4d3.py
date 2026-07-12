import struct

# XOR table at 0x51509C (8 entries, indices 1..8)
# Derived by reversing: table[i] XOR 'CHUPACHU'[i-1] = 'DEADCODE'[i-1]
# i.e. table[i] = ord('CHUPACHU'[i-1]) ^ ord('DEADCODE'[i-1])
# 'CHUPACHU' vs 'DEADCODE':
# C^D=0x07, H^E=0x0D, U^A=0x14, P^D=0x1C, A^C=0x02, C^O=0x0C, H^D=0x0C, U^E=0x70
TABLE = [
    ord('C') ^ ord('D'),  # index 1 -> 0x07
    ord('H') ^ ord('E'),  # index 2 -> 0x0D
    ord('U') ^ ord('A'),  # index 3 -> 0x14
    ord('P') ^ ord('D'),  # index 4 -> 0x1C
    ord('A') ^ ord('C'),  # index 5 -> 0x02
    ord('C') ^ ord('O'),  # index 6 -> 0x0C
    ord('H') ^ ord('D'),  # index 7 -> 0x0C
    ord('U') ^ ord('E'),  # index 8 -> 0x70
]

# ASSUMPTION: The table values above are derived purely from the writeup statement
# that XOR-ing 'DEADCODE' with the table gives 'CHUPACHU'. The actual table bytes
# at 0x51509C are not explicitly listed, but can be deduced this way.


def _crypt_part_a(s8: str) -> str:
    """XOR each of the 8 bytes with the corresponding table entry."""
    result = []
    for i in range(8):
        b = ord(s8[i]) ^ TABLE[i]
        result.append(chr(b & 0xFF))
    return ''.join(result)


def _check_part_a(key: str) -> bool:
    """PartA: CryptFunc(first 8 chars) == 'CHUPACHU'"""
    if len(key) < 8:
        return False
    return _crypt_part_a(key[:8]) == 'CHUPACHU'


def _check_separator(key: str) -> bool:
    """9th byte check: (byte XOR 0x22) & 0xFF + 0xF0F0 == 0xF0FF"""
    # Solving: ((c ^ 0x22) & 0xFF) == 0xF0FF - 0xF0F0 == 0x0F
    # c ^ 0x22 == 0x0F  =>  c == 0x0F ^ 0x22 == 0x2D == '-'
    if len(key) < 9:
        return False
    c = ord(key[8])
    val = ((c ^ 0x22) & 0xFF) + 0xF0F0
    return val == 0xF0FF


def _check_part_b_length(key: str) -> bool:
    """After '-', there must be exactly 4 characters."""
    # key format: 8 chars + '-' + 4 chars = 13 total
    return len(key) == 13


def _check_part_b_sum(key: str) -> bool:
    """1st byte + 4th byte (0-indexed) of the suffix == 0x66"""
    if len(key) < 13:
        return False
    suffix = key[9:13]  # 4 chars after '-'
    return (ord(suffix[0]) + ord(suffix[3])) == 0x66


def _check_length_hash(key: str) -> bool:
    """
    The 'WRONG ID!' check based on the serial length.
    Assembly:
      ECX = 0xDEADC0DE
      EAX = len(key)
      BSWAP EAX
      ROL EAX, 6
      XOR EAX, ECX
      BL = AL
      BL XOR= CL
      AL = BL
      store -> var
      var XOR= 0xB00
      CMP var, 0xB000C0DE
    The brute-force result from bf.c: length = 0x2FB4BA79 (800373369 decimal)
    BUT the writeup says we DON'T need to pass this check to get 'GOOD' -- there are
    3 jumps to the final XOR EAX,EAX point. The JE here is just one path.
    We simulate it anyway for completeness.
    """
    # ASSUMPTION: The 'WRONG ID!' block does NOT prevent success; it's bypassed
    # by the other jump targets. We always return True here.
    return True


def _rol32(value: int, count: int) -> int:
    count &= 31
    return ((value << count) | (value >> (32 - count))) & 0xFFFFFFFF


def _bswap32(value: int) -> int:
    return struct.unpack('<I', struct.pack('>I', value & 0xFFFFFFFF))[0]


def _length_hash_passes(length: int) -> bool:
    """Simulate the length-hash check."""
    ECX = 0xDEADC0DE
    EAX = length & 0xFFFFFFFF
    EAX = _bswap32(EAX)
    EAX = _rol32(EAX, 6)
    EAX = (EAX ^ ECX) & 0xFFFFFFFF
    BL = EAX & 0xFF
    CL = ECX & 0xFF
    BL = (BL ^ CL) & 0xFF
    EAX = (EAX & 0xFFFFFF00) | BL
    var = EAX
    var = (var ^ 0xB00) & 0xFFFFFFFF
    return var == 0xB000C0DE


def verify(name: str, serial: str) -> bool:
    """
    Validates the serial. The 'name' parameter is not used in the algorithm
    (crackme only checks the serial field).
    ASSUMPTION: name is ignored; only serial matters.
    Serial format: DEADCODE-XYZW
      - first 8 chars XOR table == 'CHUPACHU'
      - 9th char == '-'
      - suffix is exactly 4 chars
      - ord(suffix[0]) + ord(suffix[3]) == 0x66
    The WRONG ID check (length hash) is a separate display path and does not
    prevent the GOOD message per the writeup.
    """
    if not _check_part_a(serial):
        return False
    if not _check_separator(serial):
        return False
    if not _check_part_b_length(serial):
        return False
    if not _check_part_b_sum(serial):
        return False
    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial.
    Part A is always 'DEADCODE' (fixed, since the XOR table is constant).
    Separator is '-'.
    Part B: 4 chars where first + last == 0x66.
    We pick printable characters. '1' (0x31) + '5' (0x35) == 0x66. => '1235'
    Other valid examples: '3' + '3' => '3333', '1' + '5' => '1235', etc.
    ASSUMPTION: Part B middle two bytes can be anything (no check on them);
    we use '23' as arbitrary fillers.
    """
    part_a = 'DEADCODE'
    sep = '-'
    # suffix[0] + suffix[3] == 0x66
    # choose suffix[0]='1' (0x31), suffix[3]='5' (0x35): 0x31+0x35=0x66
    part_b = '1235'
    return part_a + sep + part_b



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
