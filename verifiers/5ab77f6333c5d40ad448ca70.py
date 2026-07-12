import struct

def _name_calc(name):
    """
    Compute the name checksum as described in the tutorial:
    Loop from index = len(name) down to 1 (1-based, decrementing),
    summing char_value + index for each character (iterating backward).
    Returns a 32-bit unsigned value.
    """
    total = 0
    n = len(name)
    for i in range(n, 0, -1):  # i goes from n down to 1
        ch = ord(name[i - 1])
        total += ch + i
    return total & 0xFFFFFFFF


def _hex8(val):
    """Format a 32-bit value as 8 uppercase hex characters."""
    return '{:08X}'.format(val & 0xFFFFFFFF)


def keygen(name):
    """
    Generate a valid serial for the given name.

    Requirements derived from the writeups:
      1. Name length must be >= 6 and even.
      2. Serial must be exactly 17 characters long.
      3. Serial format: Key1(8 hex chars) + ANY_CHAR + Key2(8 hex chars)
         where:
           Key1 = (name_calc(name) + 0xDDCCBBAA) & 0xFFFFFFFF
           Key2 = (Key1 * 2) & 0xFFFFFFFF
      4. The 9th character (index 8) is ignored by the crackme (replaced with 0x00
         before checking), so it can be anything.
    """
    if len(name) < 6 or len(name) % 2 != 0:
        raise ValueError('Name must be at least 6 characters long and have even length.')

    eax = _name_calc(name)

    # ASSUMPTION: The magic constant 0xDDCCBBAA is added to the name checksum
    # to produce Key1, as shown in both solution 1 (invalid_usernames.cpp) and
    # solution 2 (Form1.cs: uint iKey = 0xDDCCBBAA; Key1 = (uint)EAX + iKey)
    key1 = (eax + 0xDDCCBBAA) & 0xFFFFFFFF

    # Key2 = Key1 * 2 (from Form1.cs: uint Key2 = Key1 * 2)
    key2 = (key1 * 2) & 0xFFFFFFFF

    # Serial = Key1 as 8 hex chars + separator char (ignored) + Key2 as 8 hex chars
    # ASSUMPTION: The separator (9th char, index 8) can be any printable character;
    # we use '-' for readability.
    separator = '-'

    serial = _hex8(key1) + separator + _hex8(key2)
    assert len(serial) == 17
    return serial


def verify(name, serial):
    """
    Verify a (name, serial) pair.

    Checks:
      1. Name length >= 6 and even.
      2. Serial length == 17.
      3. serial[0:8] == hex(Key1) and serial[9:17] == hex(Key2),
         where the 9th character (serial[8]) is ignored.
    """
    if len(name) < 6 or len(name) % 2 != 0:
        return False
    if len(serial) != 17:
        return False

    eax = _name_calc(name)
    key1 = (eax + 0xDDCCBBAA) & 0xFFFFFFFF
    key2 = (key1 * 2) & 0xFFFFFFFF

    # The 9th character (index 8) is ignored by the crackme
    part1 = serial[0:8]
    # serial[8] is the ignored separator
    part2 = serial[9:17]

    try:
        s_key1 = int(part1, 16)
        s_key2 = int(part2, 16)
    except ValueError:
        return False

    # ASSUMPTION: Comparison is case-insensitive for hex digits
    return s_key1 == key1 and s_key2 == key2



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
