def keygen(name: str) -> str:
    """
    Generate serial for a given name.
    Algorithm (from keygen.cpp in the solution):
      For each group of 6 characters (by index offset within the loop),
      the offsets applied are:
        position % 6 == 0: char - 4
        position % 6 == 1: char + 6
        position % 6 == 2: char + 1
        position % 6 == 3: char + 7
        position % 6 == 4: char + 0
        position % 6 == 5: char + 2
    The serial has the same length as the name.
    Name must be at least 2 characters.
    """
    if len(name) < 2:
        raise ValueError("Name must be 2 or more characters")
    
    offsets = [-4, +6, +1, +7, 0, +2]
    serial = []
    for i, ch in enumerate(name):
        new_ord = ord(ch) + offsets[i % 6]
        serial.append(chr(new_ord))
    return ''.join(serial)


def verify(name: str, serial: str) -> bool:
    """
    Verify that the provided serial matches the expected serial for the name.
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
