def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Algorithm (from multiple solutions):
      - Take the first 4 characters of the name (name must be >= 4 chars)
      - For each character, compute: ASCII_value + 100, then convert to uppercase hex
      - Concatenate the 4 hex strings (each will be 2 hex digits for typical ASCII)
    Example: 'DEViOUS' -> 'A8A9BACD'
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long")
    serial = ""
    for i in range(4):
        val = ord(name[i]) + 100
        serial += format(val, 'X')  # uppercase hex, no leading zeros (matches VB Hex())
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given name.
    Returns True if the serial matches the expected value.
    """
    if len(name) < 4:
        return False
    expected = keygen(name)
    return serial.upper() == expected.upper()



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
