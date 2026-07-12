import datetime
import random

# This crackme (SafeCracker 3) uses three edit boxes (part1, part2, part3)
# and checkboxes. The serial is split into three 2-digit parts.
#
# Constraints derived from the Generate procedure:
#   part1[0] = '2' or '9'   (1st digit)
#   part1[1] = ah  where ah in [0..7], stored as ah+0x30  (2nd digit char)
#   part2[0] = ah2 where ah2 in [2..9], stored as ah2+0x30  (3rd digit char)
#   part2[1] = '7' if part1[0]=='2', else '0'              (4th digit char)
#   part3[0] = bl  = 7 - (part1[1]-0x30), stored as bl+0x30 (5th digit char)
#   part3[1] = bh  = 11 - (part2[0]-0x30), stored as bh+0x30 (6th digit char)
#
# Invariants:
#   (part1[1]-0x30) + (part3[0]-0x30) = 7   (2nd + 5th digit sum = 7)
#   (part2[0]-0x30) + (part3[1]-0x30) = 11  (3rd + 6th digit sum = 11)
#   part1[0] + part2[1] = either ('2','7') or ('9','0')
#     i.e. 1st digit + 4th digit = 9
#
# The crackme does NOT use a name field; serial is just the three pairs.
# There is no name->serial mapping; any combination satisfying the above is valid.
#
# Checkboxes: Left=checked, Mid=checked, None=unchecked,
#   Right = checked unless day_of_week in {3,4,6} (Wed, Thu, Sat)
#
# ASSUMPTION: The target crackme validates exactly these constraints on the
# three edit box values and the checkbox states. The exact validation code
# in the crackme binary is not shown; we reconstruct from the keygen source.

def _valid_parts(p1_0, p1_1_val, p2_0_val):
    """
    Given:
      p1_0: '2' or '9' (string char)
      p1_1_val: integer 0-7  (raw value before +0x30)
      p2_0_val: integer 2-9  (raw value before +0x30)
    Returns (part1, part2, part3) as 2-char strings.
    """
    p2_1 = '7' if p1_0 == '2' else '0'
    p1_1 = chr(p1_1_val + 0x30)
    p2_0 = chr(p2_0_val + 0x30)
    p3_0_val = 7 - p1_1_val
    p3_1_val = 11 - p2_0_val
    p3_0 = chr(p3_0_val + 0x30)
    p3_1 = chr(p3_1_val + 0x30)
    part1 = p1_0 + p1_1
    part2 = p2_0 + p2_1
    part3 = p3_0 + p3_1
    return part1, part2, part3

def verify(name, serial):
    """
    serial expected as 'AABBCC' (6 chars) or 'AA-BB-CC' (8 chars with dashes)
    name is ignored (crackme does not use name).
    ASSUMPTION: validation checks the three-part numeric constraints only.
    """
    # Normalize: remove dashes/spaces
    s = serial.replace('-', '').replace(' ', '')
    if len(s) != 6:
        return False
    # Each character must be a printable digit (0x30-0x3F range at least)
    # From the algo they end up in 0x30..0x39 range (digits 0-9)
    for c in s:
        if not c.isdigit():
            return False

    p1 = s[0:2]
    p2 = s[2:4]
    p3 = s[4:6]

    d1 = int(p1[0])  # 1st digit: must be 2 or 9
    d2 = int(p1[1])  # 2nd digit: 0-7
    d3 = int(p2[0])  # 3rd digit: 2-9
    d4 = int(p2[1])  # 4th digit: 0 or 7
    d5 = int(p3[0])  # 5th digit
    d6 = int(p3[1])  # 6th digit

    # Constraint 1: 1st digit is 2 or 9
    if d1 not in (2, 9):
        return False

    # Constraint 2: 2nd digit in 0..7
    if d2 < 0 or d2 > 7:
        return False

    # Constraint 3: 3rd digit in 2..9
    if d3 < 2 or d3 > 9:
        return False

    # Constraint 4: 1st+4th = 9  (either 2+7 or 9+0)
    if d1 + d4 != 9:
        return False

    # Constraint 5: 2nd + 5th = 7
    if d2 + d5 != 7:
        return False

    # Constraint 6: 3rd + 6th = 11
    if d3 + d6 != 11:
        return False

    return True

def keygen(name):
    """
    Generate a valid serial. Name is ignored.
    Returns serial as 'AABBCC'.
    """
    # Pick random values within valid ranges
    p1_0 = random.choice(['2', '9'])
    p1_1_val = random.randint(0, 7)   # 2nd digit value
    p2_0_val = random.randint(2, 9)   # 3rd digit value
    part1, part2, part3 = _valid_parts(p1_0, p1_1_val, p2_0_val)
    return part1 + part2 + part3

def keygen_all():
    """Generate all valid serials."""
    for p1_0 in ['2', '9']:
        for p1_1_val in range(0, 8):    # 0..7
            for p2_0_val in range(2, 10):  # 2..9
                part1, part2, part3 = _valid_parts(p1_0, p1_1_val, p2_0_val)
                yield part1 + part2 + part3


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
