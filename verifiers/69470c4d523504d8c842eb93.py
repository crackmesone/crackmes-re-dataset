import re
import random
import string

SERIAL_PATTERN = re.compile(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', re.IGNORECASE)
TARGET_SUM = 24


def _digit_sum(serial: str) -> int:
    """Sum the numeric digits in the serial, non-digit characters (including '-') count as 0."""
    return sum(int(ch) for ch in serial if ch.isdigit())


def verify(name: str, serial: str) -> bool:
    """
    Validate a serial for the WinAPI GUI Crackme by janicious.

    Rules (from writeup / comments):
      1. Serial must be exactly 14 characters long.
      2. Characters at index 4 and 9 must be '-'.
      3. The remaining 12 positions form three groups of 4 separated by '-'.
      4. The sum of all digit characters in the serial must equal 24.
         (Letters and '-' contribute 0.)
    """
    # Length check
    if len(serial) != 14:
        return False

    # Dash positions
    if serial[4] != '-' or serial[9] != '-':
        return False

    # Pattern: XXXX-XXXX-XXXX (alphanumeric groups)
    if not SERIAL_PATTERN.match(serial):
        return False

    # Digit sum must equal 24
    return _digit_sum(serial) == TARGET_SUM


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    The name is not used in the algorithm (serial is name-independent).

    Strategy: fill positions randomly with letters/digits, then adjust
    the last few digit slots to reach the target sum of 24.
    """
    CHARS = string.ascii_uppercase + string.digits
    LETTERS = string.ascii_uppercase

    while True:
        # Build 12 payload characters (positions 0-3, 5-8, 10-13)
        # We will place digits whose sum we can control.
        # Simple approach: pick 3 random digits for first two groups,
        # then compute remainder for last group.

        # First group: 4 random alphanumeric chars
        g1 = [random.choice(CHARS) for _ in range(4)]
        # Second group: 4 random alphanumeric chars
        g2 = [random.choice(CHARS) for _ in range(4)]
        # Third group: start with 2 random letters, then fill 2 digits
        g3_prefix = [random.choice(LETTERS) for _ in range(2)]

        current_sum = (_digit_sum(''.join(g1)) +
                       _digit_sum(''.join(g2)) +
                       _digit_sum(''.join(g3_prefix)))

        remainder = TARGET_SUM - current_sum

        if remainder < 0 or remainder > 18:  # max two digits can give 0..18
            continue

        # Split remainder into two digits d1, d2 where d1+d2 == remainder, each 0-9
        d1 = random.randint(max(0, remainder - 9), min(9, remainder))
        d2 = remainder - d1

        if d2 < 0 or d2 > 9:
            continue

        g3 = g3_prefix + [str(d1), str(d2)]
        serial = '{}-{}-{}'.format(''.join(g1), ''.join(g2), ''.join(g3))

        # Final verification
        if verify(name, serial):
            return serial



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
