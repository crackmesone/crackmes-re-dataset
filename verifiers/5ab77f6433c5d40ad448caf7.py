def verify(name: str, serial: str) -> bool:
    """
    Validate a serial for the given name.
    Algorithm taken directly from Code.cpp in the solution writeup.
    """
    length = len(name)
    if length < 5:
        return False

    cval = 356 % length
    SERIAL_LEN = 15

    real_serial = []
    i = 0
    for j in range(SERIAL_LEN):
        # From source: char x = ((szName[i] + j) * (j - cval)) % 27 + 65;
        # In C, char arithmetic is signed 8-bit; szName[i] is treated as int.
        # The result is taken mod 27 (C integer mod, can be negative for negative numerator)
        # then +65 to land in printable ASCII range.
        name_char = ord(name[i])
        raw = (name_char + j) * (j - cval)
        # C '%' with negative numbers: result has sign of dividend
        remainder = raw % 27  # Python mod always non-negative; adjust for C behaviour
        if raw < 0:
            # C-style mod: same sign as dividend
            remainder = -((-raw) % 27)
        x = remainder + 65
        real_serial.append(chr(x))

        if i + 1 == length:
            i = 0
        else:
            i += 1

    computed = ''.join(real_serial)
    return computed == serial


def keygen(name: str) -> str:
    """
    Generate the correct serial for a given name.
    Name must be at least 5 characters.
    """
    length = len(name)
    if length < 5:
        raise ValueError("Name must be at least 5 characters long.")

    cval = 356 % length
    SERIAL_LEN = 15

    serial_chars = []
    i = 0
    for j in range(SERIAL_LEN):
        name_char = ord(name[i])
        raw = (name_char + j) * (j - cval)
        # Replicate C signed modulo
        if raw < 0:
            remainder = -((-raw) % 27)
        else:
            remainder = raw % 27
        x = remainder + 65
        serial_chars.append(chr(x))

        if i + 1 == length:
            i = 0
        else:
            i += 1

    return ''.join(serial_chars)



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
