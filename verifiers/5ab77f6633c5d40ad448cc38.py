def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair for Sonkite crackme #1."""
    if not name:
        return False
    tot = 0
    for i in range(len(name)):
        temp = ord(name[i])  # Asc(Mid(N, i, 1))
        tot += temp          # Add ASCII values
    tot = tot * 232354       # tot * 232354
    tot = tot * 653435       # product * 653435
    try:
        return int(serial) == tot
    except (ValueError, TypeError):
        return False


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if not name:
        raise ValueError('Name must not be empty')
    tot = 0
    for i in range(len(name)):
        temp = ord(name[i])
        tot += temp
    tot = tot * 232354
    tot = tot * 653435
    return str(tot)



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
