import string

ENCODAGE = 'AJXGRFV6BKOW3Y9TM4S2ZU I70H5Q81PDECLNAJXGRFV6BKOW3Y9TM4S2ZU I70H5Q81PDECLNAJXGRFV6BKOW3Y9TM4S2ZU I70H5Q81PDECLN'


def _find_second_occurrence(s, ch):
    """Find the index of the second occurrence of ch in s."""
    first = s.find(ch)
    if first == -1:
        return -1
    second = s.find(ch, first + 1)
    return second


def verify(name: str, serial: str) -> bool:
    """
    Reimplementation of the crackme validation loop.
    name is uppercased before processing (matching strupr in C code).
    serial must be exactly 12 chars.
    """
    name = name.upper()
    if len(name) < 4:
        return False
    if len(serial) < 12:
        return False

    encodage = ENCODAGE
    result = 0

    ii = 0
    while ii <= 3:
        z = len(name) // 4
        t1 = z * ii + z
        t2 = t1 - 1
        w = t2
        c0 = name[w]
        var74 = 2 * ii + ii  # == 3*ii

        # inner loop: var74 runs from 3*ii to 3*ii+2 (inclusive), i.e. 3 iterations
        while (2 * ii + ii + 3) > var74:
            c1 = serial[var74]

            # find 2nd occurrence of c1 in encodage
            idx78 = _find_second_occurrence(encodage, c1)
            # find 2nd occurrence of c0 in encodage
            idx7c = _find_second_occurrence(encodage, c0)

            if idx78 == -1 or idx7c == -1:
                result = 1
            else:
                distance = abs(idx78 - idx7c)
                if distance > 5:
                    result = 1

            var74 += 1

        ii += 1

    return result == 0


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Mirrors qhfCrackmeJeygen2.c keygen logic.
    """
    name = name.upper()
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')

    encodage = ENCODAGE
    serial = ['\x00'] * 13

    ii = 0
    while ii <= 3:
        z = len(name) // 4
        t1 = z * ii + z
        t2 = t1 - 1
        w = t2
        c0 = name[w]
        var74 = 3 * ii  # 2*ii+ii

        # find 2nd occurrence of c0 in encodage
        idx78 = _find_second_occurrence(encodage, c0)
        if idx78 == -1:
            raise ValueError(f'Character {c0!r} not found twice in encodage')

        # try character after idx78
        c1 = encodage[idx78 + 1]
        # check if second occurrence of c1 is at idx78+1
        temp = _find_second_occurrence(encodage, c1)
        if temp == idx78 + 1:
            chosen = c1
        else:
            # use character before idx78
            chosen = encodage[idx78 - 1]

        serial[var74] = chosen
        serial[var74 + 1] = chosen
        serial[var74 + 2] = chosen

        ii += 1

    serial[12] = '\x00'
    return ''.join(serial[:12])



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
