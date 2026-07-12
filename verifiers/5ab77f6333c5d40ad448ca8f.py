def keygen(name: str) -> str:
    """
    Algorithm (from multiple writeups):
    1. For each character in the name, concatenate its ASCII decimal value.
    2. Take the first 15 characters of that concatenated string.
    3. Split as: chars 1-5, '-', chars 6-10, '-', chars 11-15
       => serial = first5 + '-' + next5 + '-' + last5

    Name must be between 5 and 20 characters long.
    If the concatenated ASCII string is shorter than 15 chars the remaining
    positions will be whatever partial digits exist (the crackme truncates to
    whatever is available up to 15).
    """
    if len(name) < 5 or len(name) > 20:
        raise ValueError("Name must be between 5 and 20 characters")

    # Step 1: concatenate ASCII decimal values of each character
    a = ''.join(str(ord(ch)) for ch in name)

    # Step 2: take first 15 characters
    b = a[:15]

    # Step 3: split into three groups of 5 and join with '-'
    c = b[0:5]
    d = b[5:10]
    e = b[10:15]

    serial = c + '-' + d + '-' + e
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the expected serial for the given name.
    """
    try:
        expected = keygen(name)
    except ValueError:
        return False
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
