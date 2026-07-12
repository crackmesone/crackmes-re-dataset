def _check(s, idx=0):
    """
    Recursive validation function mirroring the assembly at 0xC61000.
    s: the serial string (bytes or str)
    idx: current index into the string
    """
    if isinstance(s, str):
        s = s.encode('latin-1')

    # Load first byte (str[idx]) as signed-extended value
    if idx >= len(s):
        return 0
    firstchar = s[idx]  # treated as unsigned byte, but arithmetic may go negative

    # Load second byte (str[idx+1])
    if idx + 1 >= len(s):
        secondchar = 0
    else:
        secondchar = s[idx + 1]

    if secondchar == 0:  # null terminator or end
        return firstchar

    # Recurse with pointer advanced by 2
    recursive_result = _check(s, idx + 2)

    if secondchar & 1:  # odd -> add
        return firstchar + recursive_result
    else:               # even -> subtract
        return firstchar - recursive_result


def verify(name, serial):
    """
    Verify a serial number.
    Note: 'name' is not used in the algorithm - this crackme only checks the serial.
    Rules:
      1. Length must be between 5 and 11 (inclusive)
      2. Length must be odd
      3. _check(serial) must return 0
    """
    n = len(serial)
    if n < 5 or n > 11:
        return False
    if n % 2 == 0:  # must be odd
        return False
    result = _check(serial)
    return result == 0


def keygen(name):
    """
    Generate a valid serial.
    Strategy: pick an odd-length serial (e.g. length 7).
    Positions are 0-indexed: chars at even indices (0,2,4,6) are 'value' chars,
    chars at odd indices (1,3,5) are 'operator' chars (even ASCII = subtract, odd ASCII = add).

    With all operator chars even (subtract), the recursion computes:
      result = char[0] - (char[2] - (char[4] - char[6]))
    We need this == 0, so:
      char[0] = char[2] - char[4] + char[6]

    We pick char[2]=100 ('d'), char[4]=60 ('<'), char[6]=40 ('('),
    then char[0] = 100 - 60 + 40 = 80 ('P').
    Operator chars (all even ASCII): '0' = 48.
    Serial: P0d0<0(
    Let's verify and use a cleaner approach with simple characters.
    """
    # We'll generate serials of length 7 with all even operator chars (subtract mode)
    # result = c0 - (c2 - (c4 - c6)) = 0
    # => c0 = c2 - c4 + c6
    # Choose printable ASCII values that satisfy this

    op = ord('0')  # 48, even -> subtract for all operator positions

    # Pick c2, c4, c6 such that c0 = c2 - c4 + c6 is in printable range [33,126]
    import random
    for _ in range(10000):
        c2 = random.randint(80, 120)
        c4 = random.randint(33, c2 - 1)
        c6 = random.randint(33, 90)
        c0 = c2 - c4 + c6
        if 33 <= c0 <= 126:
            serial = chr(c0) + chr(op) + chr(c2) + chr(op) + chr(c4) + chr(op) + chr(c6)
            if verify(name, serial):
                return serial

    # Fallback: known good serial from comments
    return '1010101'


# --- Self-test ---

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
