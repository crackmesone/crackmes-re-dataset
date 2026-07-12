import random


def digit_to_num(c):
    """Convert char to int digit, return -1 if not a digit."""
    if '0' <= c <= '9':
        return int(c)
    return -1


def sum_digits_range(s, start, length):
    """Sum 'length' digits starting at index 'start'. Return -1 if any non-digit found."""
    total = 0
    for i in range(start, start + length):
        d = digit_to_num(s[i])
        if d == -1:
            return -1
        total += d
    return total


def verify(name, serial):
    """
    Verify a serial key. The 'name' parameter is not used in the algorithm
    (the check is purely serial-based).

    Format: XXX-YYYYYYYYY  (13 chars, position 3 is hyphen)
    Groups: prefix = serial[0:3], g1 = serial[4:7], g2 = serial[7:10], g3 = serial[10:13]

    For i in [4, 7, 10]:
        sumb = sum of 3 digits at position i
        n    = digit at position (i-4)//3  (i.e. serial[0], serial[1], serial[2])
        check: (n ^ (suma % 3)) == sumb % 9

    Where suma = sum of first 3 digits (serial[0:3]).
    """
    s = serial
    # Must be 13 characters long and 4th char (index 3) must be '-'
    if len(s) != 13 or s[3] != '-':
        return False

    # Sum the first 3 digits
    suma = sum_digits_range(s, 0, 3)
    if suma == -1:
        return False

    # Loop through groups starting at indices 4, 7, 10
    for i in range(4, 13, 3):  # i = 4, 7, 10
        sumb = sum_digits_range(s, i, 3)
        if sumb == -1:
            return False
        # Digit from the prefix corresponding to this group
        n = digit_to_num(s[(i - 4) // 3])
        if n == -1:
            return False
        # Core check: (n XOR (suma % 3)) must equal (sumb % 9)
        if (n ^ (suma % 3)) != (sumb % 9):
            return False

    return True


def keygen(name=None):
    """
    Generate a valid serial key.

    Strategy (from solution writeup by kejcao):
      - Pick 3 prefix digits (0-7 to avoid overflow issues, though 0-9 works too).
      - Compute suma = sum of prefix digits.
      - For each prefix digit d[i], find 3 digits whose sum % 9 == (d[i] ^ (suma % 3)).
      - Concatenate as 'XYZ-ABCDEFGHI'.
    """
    while True:
        # Pick prefix digits (0-7 keeps things safe, but 0-9 is fine)
        prefix = [random.randint(0, 9) for _ in range(3)]
        suma = sum(prefix)

        groups = []
        valid = True
        for i in range(3):
            target = prefix[i] ^ (suma % 3)  # target for sumb % 9
            # Find 3 digits summing to target mod 9
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            # z = (target - x - y) mod 9, but we need z in [0..9]
            # Since target < 9 (it's a XOR result of single digit and 0-2),
            # we solve modularly
            z_mod = (target - (x + y)) % 9
            # z_mod is in [0,8], which is a valid digit
            z = z_mod
            groups.append([x, y, z])

        # Build serial string
        serial = ''.join(str(d) for d in prefix) + '-'
        for g in groups:
            serial += ''.join(str(d) for d in g)

        # Verify before returning
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
            print(_sv)
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
