import random

def verify(serial1: str, serial2: str) -> bool:
    """
    The crackme reads two integers (serial1 and serial2) and checks:
        serial1 + serial2 == 0x691A  (26906 decimal)
    Both inputs are treated as plain integers (long/int).
    NOTE: 'name' is not used by this crackme; only the two serials matter.
    """
    try:
        s1 = int(serial1)
        s2 = int(serial2)
    except (ValueError, TypeError):
        return False
    return (s1 + s2) == 0x691A


def verify_pair(s1: int, s2: int) -> bool:
    """Convenience wrapper accepting integers directly."""
    return (s1 + s2) == 0x691A


def keygen(name: str = "") -> tuple:
    """
    Generate a valid (serial1, serial2) pair.
    'name' is ignored because the algorithm does not depend on a username.
    Returns a tuple (serial1, serial2) such that serial1 + serial2 == 26906.
    """
    TARGET = 0x691A  # 26906
    s1 = random.randint(0, TARGET)
    s2 = TARGET - s1
    return (s1, s2)


def all_pairs():
    """Generator that yields every non-negative integer pair summing to 26906."""
    TARGET = 0x691A
    for s1 in range(TARGET + 1):
        yield (s1, TARGET - s1)



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
