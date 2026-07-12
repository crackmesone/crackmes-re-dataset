def keygen(name: str) -> str:
    """
    Algorithm from keygen.pas by luucorp:

    first = (ord(name[0]) * 2) + 3
    last  = (ord(name[1]) * 2) - 3

    middle = reverse of [chr(ord(c)+2) for c in name]
    (the loop prepends each chr(ord(name[i])+2) to serial,
     effectively reversing the transformed name)

    serial = chr(first) + middle + chr(last)
    """
    if len(name) < 2:
        raise ValueError("Name must be at least 2 characters long")

    first = (ord(name[0]) * 2) + 3
    last  = (ord(name[1]) * 2) - 3

    # Build middle: loop i=1..len, each step prepends chr(ord(name[i-1])+2)
    # This produces the reversed, shifted string of name
    middle = ''
    for ch in name:
        middle = chr(ord(ch) + 2) + middle  # prepend => reversal

    serial = chr(first) + middle + chr(last)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify by regenerating the expected serial and comparing.
    """
    if len(name) < 2:
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
