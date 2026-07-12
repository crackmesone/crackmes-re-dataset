import math

def verify(name: str, serial: str) -> bool:
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    return keygen(name) == serial_int

def keygen(name: str) -> int:
    n = len(name)
    c = [ord(ch) for ch in name]

    if n == 1:
        password = c[0]
    elif n == 2:
        password = c[1] * c[0]
    elif n == 3:
        # ((name[1] + name[0]) * name[2] - name[0]) * name[2]
        # NOTE: solution 3 computes name[1]*name[0]*name[2]-name[0]*name[2]
        # which differs from solution 1. Solution 1 (C source) is authoritative.
        password = ((c[1] + c[0]) * c[2] - c[0]) * c[2]
    elif n == 4:
        # ((name[3] - name[1]*name[2]) * name[3]) - (name[0]*name[0])
        password = ((c[3] - c[1] * c[2]) * c[3]) - (c[0] * c[0])
    elif n == 5:
        # ((name[4]*name[4] - name[0]) + name[2]) * name[3]
        password = ((c[4] * c[4] - c[0]) + c[2]) * c[3]
    elif n == 6:
        # (name[2] + ((name[5]*name[0]) / (name[4]*name[1]))) * name[3]
        # integer (truncating) division as shown in C source and solution 3
        password = (c[2] + math.trunc((c[5] * c[0]) / (c[4] * c[1]))) * c[3]
    elif n == 7:
        # ((name[3] - name[0]*name[5]*name[4]) * name[0] + name[5]) * name[6] + name[2]
        password = ((c[3] - c[0] * c[5] * c[4]) * c[0] + c[5]) * c[6] + c[2]
    elif n == 8:
        # name[7] / name[5] * name[6] - name[0]  (truncating division)
        password = math.trunc(c[7] / c[5]) * c[6] - c[0]
    elif n == 9:
        # (name[0] + name[0]) / name[8] * name[7] * name[6]  (truncating division)
        password = math.trunc((c[0] + c[0]) / c[8]) * c[7] * c[6]
    else:
        # length >= 10, uses first 10 chars
        # (name[9]*name[2] - name[8]*name[3] + name[5]) * name[3] * name[0]
        password = (c[9] * c[2] - c[8] * c[3] + c[5]) * c[3] * c[0]

    return password


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
