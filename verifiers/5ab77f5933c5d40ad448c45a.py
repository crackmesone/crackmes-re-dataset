import ctypes

def _sar(value, shift):
    """Arithmetic right shift (sign-extending), 32-bit signed integer."""
    # Treat as 32-bit signed
    value = ctypes.c_int32(value).value
    if value < 0:
        result = (value >> shift) | (~(~0 >> shift))  # sign extend
    else:
        result = value >> shift
    return ctypes.c_int32(result).value


def _compute_parts(name_str):
    """
    The crackme prepends 'Hccc' and appends 'KeygenMe' to the entered name
    before running the two loops.
    """
    name = 'Hccc' + name_str + 'KeygenMe'

    # Loop 1
    counter = 0
    temp4 = 0
    while True:
        temp1 = 0
        temp2 = 0
        temp3 = 0
        counter += 1
        temp1 = temp1 + ord(name[counter - 1])  # Delphi strings are 1-indexed
        temp2 = temp1 + 9
        temp3 = temp2 * 14
        temp3 = _sar(temp3, 2)
        temp4 = temp4 + temp3
        part1 = str(temp4)
        if counter == len(name):
            break

    # Loop 2
    counter = 0
    temp3 = 0
    while True:
        temp2 = 0
        temp1 = 0
        counter += 1
        temp1 = temp1 + ord(name[counter - 1])
        temp2 = temp1 ^ 9
        temp3 = temp3 + temp2
        part2 = str(temp3)
        if counter == len(name):
            break

    serial = part1 + '-' + part2 + '-69'
    return serial


def verify(name, serial):
    """
    Returns True if serial matches the expected serial for the given name.
    The name must be at least 4 characters long.
    """
    if len(name) < 4:
        return False
    expected = _compute_parts(name)
    return serial == expected


def keygen(name):
    """
    Returns the valid serial for the given name.
    Name must be at least 4 characters.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters long')
    return _compute_parts(name)



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
