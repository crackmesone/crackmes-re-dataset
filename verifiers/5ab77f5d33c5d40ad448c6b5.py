def _make_printable(val):
    """
    Mirrors the printable-character normalization from the keygen:
    reduces val modulo 64 (with sign fix), then maps to a character.
    """
    if val < 0:
        temp2 = val + 63
    else:
        temp2 = val
    temp2 = val - (temp2 & 0xFFFFFFC0)  # val mod 64, always in [0,63]

    if temp2 <= 0x19:           # 0-25  -> 'a'-'z'
        return chr(temp2 + 97)
    elif temp2 - 26 <= 0x19:    # 26-51 -> 'A'-'Z'  (temp2+39 => 65-90)
        return chr(temp2 + 39)
    elif temp2 - 52 <= 9:       # 52-61 -> '0'-'9'  (temp2-4  => 48-57)
        return chr(temp2 - 4)
    else:                       # 62 -> '-', 63 -> '_'
        if temp2 == 62:
            return '-'
        else:
            return '_'


def _compute_serial(name):
    """
    Core algorithm extracted from keygen.cpp.
    Returns the 5-character serial string for a given name,
    or None if the name is shorter than 4 characters.
    """
    if len(name) < 4:
        return None

    length = len(name)
    temp = [0, 0, 0, 0, 0]

    for ch in name:
        c = ord(ch)
        temp[0] += c
        temp[1] += c * length
        temp[2] += c ^ length
        temp[3] += c | 0x01010101
        temp[4] += c % length

    serial = ''.join(_make_printable(t) for t in temp)
    return serial


def verify(name, serial):
    """
    Returns True if the serial matches the one generated for name.
    Name must be >= 4 chars, serial must be exactly 5 chars.
    """
    if len(name) < 4:
        return False
    if len(serial) != 5:
        return False
    expected = _compute_serial(name)
    return expected == serial


def keygen(name):
    """
    Returns the valid serial for the given name,
    or raises ValueError if the name is too short.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters long')
    return _compute_serial(name)



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
