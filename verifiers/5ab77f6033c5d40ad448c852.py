def verify(name: str, serial: str) -> bool:
    """
    Validate name/serial pair.
    Rules:
      - len(name) >= 3
      - len(name) must be odd
      - serial (hex string) must match computed val
    """
    length = len(name)
    if length < 3:
        return False
    if length % 2 == 0:
        return False

    val = 0
    # Sum pairs: name[i] * name[i+1] for i in 0, 2, 4, ... up to len-2
    # The last character (index len-1) is unpaired in the loop below
    # because len is odd, the loop goes i=0,2,...,len-3  (pairs: (0,1),(2,3),...,(len-3,len-2))
    for i in range(0, length - 1, 2):
        val += ord(name[i]) * ord(name[i + 1])

    # Add last character * 123
    val += ord(name[length - 1]) * 123

    # Serial is the hex representation (uppercase, no prefix)
    expected = format(val & 0xFFFFFFFF, 'X')
    return serial.upper().lstrip('0') == expected.upper().lstrip('0') or (val == 0 and serial.upper() in ('0', ''))


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Returns None if the name does not meet requirements.
    """
    length = len(name)
    if length < 3:
        raise ValueError('Name must be at least 3 characters long.')
    if length % 2 == 0:
        raise ValueError('Name length must be odd.')

    val = 0
    for i in range(0, length - 1, 2):
        val += ord(name[i]) * ord(name[i + 1])

    val += ord(name[length - 1]) * 123

    # Return as uppercase hex string (no 0x prefix), matching printf("%X", val)
    # val is treated as unsigned in C; mask to 32-bit unsigned
    return format(val & 0xFFFFFFFF, 'X')



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
