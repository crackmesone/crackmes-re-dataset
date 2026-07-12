def verify(name: str, serial: str) -> bool:
    """
    Validates a name/serial pair for cobrasniper555's keygenme_1.

    Rules (from both writeups):
    1. Serial length must be > 4 and <= 30.
    2. The first character of the serial must equal the first character of the name.
    """
    if not name or not serial:
        return False

    serial_len = len(serial)

    # Length check: strictly greater than 4 and not greater than 30
    if serial_len <= 4 or serial_len > 30:
        return False

    # Core check: first char of name == first char of serial
    if name[0] != serial[0]:
        return False

    return True


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name.

    The serial just needs to:
    - Start with the same character as the name.
    - Have length > 4 and <= 30.
    """
    if not name:
        raise ValueError("Name must not be empty")

    # Use the first char of the name followed by four padding chars to satisfy length > 4
    # ASSUMPTION: any characters can fill the remaining positions
    serial = name[0] + "AAAA"  # length = 5, which is > 4 and <= 30
    return serial



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
