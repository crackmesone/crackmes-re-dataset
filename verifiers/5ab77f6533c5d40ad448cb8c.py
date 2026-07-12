import os

def keygen(name: str) -> str:
    """
    Algorithm (from the solution write-up):
      1. Take the username.
      2. Convert it to upper case.
      3. Reverse it.
      4. Concatenate with '-V4V-' and the length of the original username.

    The resulting string IS the password (serial). The program then hashes
    both sides with the same hash function, so the hash comparison is
    equivalent to a plain-string comparison of the constructed value.
    """
    upper = name.upper()
    reversed_upper = upper[::-1]
    serial = '{}-V4V-{}'.format(reversed_upper, len(name))
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Check whether the provided serial matches the one that would be generated
    for the given username.
    """
    return serial == keygen(name)



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
