def verify(name: str, serial) -> bool:
    return keygen(name) == int(serial)

def keygen(name: str) -> int:
    s = name.lower()
    n = len(s)
    iName = [0] * n

    for i in range(n):
        if n % 2 == 0:
            # Even length name
            if i % 2 == 0:
                iName[i] = ord(s[i]) + i
            else:
                iName[i] = ord(s[i]) + (i >> 1)
        else:
            # Odd length name
            if i % 2 == 0:
                iName[i] = ord(s[i]) + (i >> 1) + 10
            else:
                iName[i] = ord(s[i]) + i + 5

    iSerial = sum(v * 0x8E for v in iName)
    return iSerial


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
