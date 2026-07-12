def _asc(c):
    """Return the ASCII/ordinal value of a character (matches VB's Asc())."""
    return ord(c)

def keygen(name: str) -> str:
    """
    Generates the serial for the given username.
    VB source (GenSerial):
        For i = 1 To Len(Username)
            Part1 = Part1 & Left(Asc(Mid(Username, i, 1)), 1)
            Part2 = Part2 & Right(Asc(Mid(Username, i, 1)), 1)
        Next i
        GenSerial = Part2 & "-1337-" & Part1

    In VB, Asc() returns an Integer (e.g. 65 for 'A').
    Left(str(n), 1) takes the LEFTMOST digit of the decimal string.
    Right(str(n), 1) takes the RIGHTMOST digit of the decimal string.
    """
    name = name.strip()
    if len(name) < 5:
        return "Your username must be at least 5 characters."
    part1 = ""
    part2 = ""
    for ch in name:
        asc_val = str(_asc(ch))  # e.g. 65, 97, 48 ...
        part1 += asc_val[0]      # Left(..., 1)  -> first digit
        part2 += asc_val[-1]     # Right(..., 1) -> last digit
    return part2 + "-1337-" + part1

def verify(name: str, serial: str) -> bool:
    """
    Returns True if the serial matches the one generated for the given name.
    """
    name = name.strip()
    if len(name) < 5:
        return False
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
