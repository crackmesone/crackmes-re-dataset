def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Requirements: len(name) >= 4
    Algorithm (1-based index, matching Pascal/Delphi source):
      for i in 1..len(name):
        bl = ord(name[i-1]) XOR i
        j  = i OR 3
        bl = bl + j
        mid_serial += chr(bl).upper()
      serial = 'LL2TF-' + mid_serial + '-ALFIGH'
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long.")

    mid_serial = ""
    for i in range(1, len(name) + 1):  # 1-based index
        bl = ord(name[i - 1]) ^ i      # name[i] XOR i
        j  = i | 3                      # i OR 3
        bl = bl + j                     # bl + j
        mid_serial += chr(bl).upper()   # upcase

    serial = "LL2TF-" + mid_serial + "-ALFIGH"
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that the given serial matches the name.
    The crackme does a case-insensitive comparison after uppercasing the serial.
    """
    if len(name) < 4:
        return False
    expected = keygen(name)
    # The crackme uppercases the generated serial before comparing
    return serial.upper() == expected.upper()



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
