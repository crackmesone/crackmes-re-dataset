def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair for wt0vremrs_1 crackme.
    Rules:
      - name must be more than 4 characters (length > 4, i.e. at least 5)
      - serial = 'KL19-IY7D' + str(len(name) * 2011) + '-GA4S-OD1T-B6RE-' + str(len(name) * 1102)
    """
    # Name must have more than 4 characters (CMP EAX, 4 / JLE means strictly greater than 4)
    if len(name) <= 4:
        return False
    n = len(name)
    part1 = n * 0x7DB  # 2011 decimal
    part2 = n * 0x44E  # 1102 decimal
    expected = 'KL19-IY7D' + str(part1) + '-GA4S-OD1T-B6RE-' + str(part2)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Raises ValueError if name is too short.
    """
    if len(name) <= 4:
        raise ValueError('Name must be more than 4 characters long.')
    n = len(name)
    part1 = n * 0x7DB  # 2011 decimal
    part2 = n * 0x44E  # 1102 decimal
    return 'KL19-IY7D' + str(part1) + '-GA4S-OD1T-B6RE-' + str(part2)



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
