def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given name.
    Algorithm recovered from Solution 1 writeup (C pseudocode).
    """
    p1 = len(name)
    if p1 < 2:
        return False
    p2 = 0
    p3 = 0
    for i in range(p1):
        p2 += ord(name[i]) * 0x539
        p3 += ord(name[i])
    expected = "{}-{}-{}".format(p1, p2, p3)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    p1 = len(name)
    if p1 < 2:
        raise ValueError("Name must be at least 2 characters long.")
    p2 = 0
    p3 = 0
    for i in range(p1):
        p2 += ord(name[i]) * 0x539
        p3 += ord(name[i])
    return "{}-{}-{}".format(p1, p2, p3)



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
