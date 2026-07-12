#!/usr/bin/env python3

def sum1(name):
    s = 0
    for c in name:
        s += ord(c)
    return s

def sum2(name):
    s = 0
    i = 1
    for c in name:
        s += (ord(c) * i) ^ i
        i += 1
    return s

def sum3(name):
    return sum1(name) + sum2(name)

def keygen(name):
    """Generate a valid serial for the given name."""
    u1 = sum1(name) % 499
    u2 = sum2(name) % 499
    u3 = sum3(name) % 499

    # Solve the linear system mod 499:
    # 15*s1 + 18*s2 + 21*s3 = u1
    # 14*s1 + 17*s2 + 20*s3 = u2
    # 16*s1 + 18*s2 + 19*s3 = u3
    # Solution (mod 499, where 3*333 = 999 = 2*499+1 = 1 mod 499):
    S1 =  37 * u1 - 36 * u2 - 3 * u3
    S2 = -54 * u1 + 51 * u2 + 6 * u3
    S3 =  20 * u1 - 18 * u2 - 3 * u3

    s1 = (S1 * 333) % 499
    s2 = (S2 * 333) % 499
    s3 = (S3 * 333) % 499

    return "%04X-%04X-%04X" % (s1, s2, s3)

def verify(name, serial):
    """Verify that the given serial is valid for the given name."""
    # Parse serial: three hex parts separated by '-'
    parts = serial.strip().split('-')
    if len(parts) != 3:
        return False
    try:
        s1 = int(parts[0], 16)
        s2 = int(parts[1], 16)
        s3 = int(parts[2], 16)
    except ValueError:
        return False

    u1 = sum1(name) % 499
    u2 = sum2(name) % 499
    u3 = sum3(name) % 499

    # Compute linear combinations from serial parts
    c1 = (15 * s1 + 18 * s2 + 21 * s3) % 499
    c2 = (14 * s1 + 17 * s2 + 20 * s3) % 499
    c3 = (16 * s1 + 18 * s2 + 19 * s3) % 499

    # XOR each pair and sum; must equal zero mod 499
    result = ((c1 ^ u1) + (c2 ^ u2) + (c3 ^ u3)) % 499
    return result == 0


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
