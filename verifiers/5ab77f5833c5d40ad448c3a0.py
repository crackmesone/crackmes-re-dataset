import math

def _round_vb(x):
    """VB banker's rounding (round half to even), but kao's keygen uses
    Python/Delphi Round which rounds half away from zero for odd results.
    The keygen comment says it's 'wrong but won't fail' - we replicate it."""
    import math
    r = round(x)  # Python uses banker's rounding; Delphi Round rounds half-away
    # Replicate Delphi Round: round half away from zero
    if x - math.floor(x) == 0.5:
        r = math.floor(x) + 1
    return r

def _keygen_internal(name):
    strlen = len(name)
    if strlen < 5:
        raise ValueError('At least 5 characters required!')

    q = _round_vb(strlen / 2)

    strL = name[:q]
    strR = name[strlen - q:]

    # LEFTSUM: sum of ASCII values of left half
    LEFTSUM = sum(ord(c) for c in strL)

    # SUMX: for each char in right half, add LEFTSUM + char_value
    SUMX = sum(LEFTSUM + ord(c) for c in strR)

    # RIGHTSUM
    RIGHTSUM = SUMX * LEFTSUM

    # TEMPMAGIC
    m1 = round(SUMX * math.sqrt(strlen ^ LEFTSUM))  # Delphi Round (standard)
    TEMPMAGIC = RIGHTSUM ^ m1

    # MAGIC
    MAGIC = TEMPMAGIC ^ (TEMPMAGIC + ord(name[0]))

    # MAGIC2
    MAGIC2 = LEFTSUM ^ SUMX

    # SERIAL = decimal(RIGHTSUM) + hex(MAGIC) + hex(MAGIC2)  (no 0x prefix, lowercase)
    # In Delphi FORMAT('%d%x%x', ...) produces decimal then lowercase hex without prefix
    serial = '{}{:x}{:x}'.format(RIGHTSUM, MAGIC & 0xFFFFFFFF, MAGIC2 & 0xFFFFFFFF)
    return serial

def verify(name, serial):
    try:
        expected = _keygen_internal(name)
        return serial == expected
    except Exception:
        return False

def keygen(name):
    return _keygen_internal(name)


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
