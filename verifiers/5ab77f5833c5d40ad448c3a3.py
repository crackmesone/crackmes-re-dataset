import random

# BrainKiller KeyGenMe by mouradprat4re
# Serial format: AAA-BBBB-CCCC-DDDD (18 characters total)
#
# Rules derived from writeup:
# 1. Serial length = 18 characters
# 2. Characters 4, 9, 14 (1-indexed) must be '-'
# 3. Groups: [1..3]-[5..8]-[10..13]-[15..18]
# 4. Each character is parsed with atoi (digits 1-9 map to their value, others map to 0)
# 5. Sum of digits in group2 (positions 5-8) must equal 8
# 6. Sum of digits in group3 (positions 10-13) must equal 19
# 7. Sum of digits in group4 (positions 15-18) must equal 12
# 8. First and second characters must NOT be the same digit
# 9. Third character encodes license type:
#      3 = Professional, 2 = Standard
#    (from canonical69's keygen: serial_group1 = [4,1,license])
# 10. ASSUMPTION: First char and second char differ; exact constraint on char[1] and char[2]
#     is only partially described (writeup was truncated). We use the pattern [4,1,license]
#     from the reference keygen as the first group.

def _split_sum(total, n, min_val=0, max_val=9):
    """Generate n random digits (0-9) that sum to total."""
    digits = [0] * n
    remaining = total
    for i in range(n - 1):
        # Choose a random value for digit i
        lo = max(min_val, remaining - max_val * (n - 1 - i))
        hi = min(max_val, remaining - min_val * (n - 1 - i))
        if lo > hi:
            raise ValueError(f"Cannot split {total} into {n} digits")
        v = random.randint(lo, hi)
        digits[i] = v
        remaining -= v
    digits[n - 1] = remaining
    return digits

def keygen(name, license_type=3):
    """
    Generate a valid serial. license_type=3 for Professional, 2 for Standard.
    NOTE: The name is not used in the algorithm as described (no name-based check found).
    ASSUMPTION: name is not part of the serial computation based on available writeup.
    """
    # Group 1: three digits, pattern [4, 1, license_type], first != second
    g1 = [4, 1, license_type]
    # Verify first != second (4 != 1, so OK)

    # Group 2: four digits summing to 8
    g2 = _split_sum(8, 4)

    # Group 3: four digits summing to 19
    # Max single digit is 9, so minimum of 4 digits summing to 19 works (e.g. 9+9+1+0 not enough)
    # Actually 9*3+1=28 > 19, and minimum is 0*4=0, so feasible
    # But note: sum=19 with max digit 9 and 4 slots: 9+9+1+0=19 OK
    g3 = _split_sum(19, 4)

    # Group 4: four digits summing to 12
    g4 = _split_sum(12, 4)

    serial = (
        ''.join(str(d) for d in g1) + '-' +
        ''.join(str(d) for d in g2) + '-' +
        ''.join(str(d) for d in g3) + '-' +
        ''.join(str(d) for d in g4)
    )
    return serial

def verify(name, serial):
    """
    Verify a serial against the BrainKiller KeyGenMe checks.
    ASSUMPTION: name is not used in validation (not described in writeup).
    """
    # Check 1: length must be 18
    if len(serial) != 18:
        return False

    # Check 2: dashes at positions 3, 8, 13 (0-indexed)
    if serial[3] != '-' or serial[8] != '-' or serial[13] != '-':
        return False

    # Split into groups
    g1_str = serial[0:3]   # characters 1-3
    g2_str = serial[4:8]   # characters 5-8
    g3_str = serial[9:13]  # characters 10-13
    g4_str = serial[14:18] # characters 15-18

    # atoi-like parsing: each character parsed individually
    # Non-digit or non-1..9 characters yield 0
    def to_int(ch):
        try:
            return int(ch)
        except ValueError:
            return 0

    g1 = [to_int(c) for c in g1_str]
    g2 = [to_int(c) for c in g2_str]
    g3 = [to_int(c) for c in g3_str]
    g4 = [to_int(c) for c in g4_str]

    # Check 3: sum checks
    if sum(g2) != 8:
        return False
    if sum(g3) != 19:
        return False
    if sum(g4) != 12:
        return False

    # Check 4: first and second character must NOT be the same
    if g1[0] == g1[1]:
        return False

    # Check 5: third character must be a valid license type
    # ASSUMPTION: based on canonical69's keygen, license type is 2 or 3
    if g1[2] not in (2, 3):
        return False

    return True


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
