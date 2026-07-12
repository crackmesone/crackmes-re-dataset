#!/usr/bin/env python3
# Reverse-engineered keygen/verifier for j777X by josamont
# Based on solution writeup by acruel
#
# Algorithm summary:
#   1. Compute checksum1 from the username: sum of (ord(c) & 0x5F) for every other
#      character (even-indexed), plus a base of 0x92.
#   2. The serial must satisfy a format check (first half: digits 0-9 and '_' only;
#      all chars in range 0x20..0x7A).
#   3. Compute checksum2 from the serial (sum of every other character of the serial).
#   4. The condition: checksum2 - byte_804E1B9 - checksum1 == 0
#      The writeup does not fully explain byte_804E1B9; ASSUMPTION: it is 0 or
#      already folded into the keygen logic below.
#
# The keygen from the writeup (ported to Python 3):

import sys

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    sum1 = 0x92
    for c in name[::2]:
        sum1 += (ord(c) & 0x5F)

    r = sum1 % 0x5F

    # ASSUMPTION: integer division behaviour matches Python 2 // for positive ints
    if r < 0x1C:
        # pad with '__' groups, then a character in the underscore range
        serial = '__' * (sum1 // 0x5F - 1) + chr(0x5F + r)
    elif r < 0x21:
        # use a digit string in first half, then 'z' as last char
        serial = '__' * (sum1 // 0x5F - 2) + ('%d000' % (r - 0x1B - 1)) + 'z'
    else:
        serial = '__' * (sum1 // 0x5F) + chr(r)

    return serial


def _serial_checksum(serial: str) -> int:
    """Checksum2: sum of every other character of the serial."""
    # ASSUMPTION: same stride (every other char, index 0, 2, 4, ...) as username
    total = 0
    for c in serial[::2]:
        total += ord(c)
    return total


def _name_checksum(name: str) -> int:
    """Checksum1: 0x92 + sum of (ord(c) & 0x5F) for even-indexed chars."""
    total = 0x92
    for c in name[::2]:
        total += (ord(c) & 0x5F)
    return total


def _valid_chars(s: str) -> bool:
    """All characters must be in range 0x20..0x7A inclusive."""
    return all(0x20 <= ord(c) <= 0x7A for c in s)


def _valid_first_half(s: str) -> bool:
    """First half of serial: only digits (0-9) and underscore '_'."""
    half = s[:len(s) // 2]
    return all(c.isdigit() or c == '_' for c in half)


def verify(name: str, serial: str) -> bool:
    """Return True if the serial is valid for the given name."""
    # Basic character range check
    if not _valid_chars(name) or not _valid_chars(serial):
        return False

    # ASSUMPTION: first-half format check applies; exact split point unknown.
    # The writeup says 'first half of the serial' uses only digits and '_'.
    if not _valid_first_half(serial):
        return False

    checksum1 = _name_checksum(name)
    checksum2 = _serial_checksum(serial)

    # From disassembly: checksum2 - byte_804E1B9 - checksum1 == 0
    # ASSUMPTION: byte_804E1B9 == 0 (not determined from the writeup)
    byte_804E1B9 = 0  # ASSUMPTION
    return (checksum2 - byte_804E1B9 - checksum1) == 0



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
