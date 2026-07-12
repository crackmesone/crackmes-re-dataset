def gen_serial(name: str) -> str:
    """
    Implements the serial generation algorithm for ECM1 by shap0renk0.

    Algorithm (from Module1.bas keygen and assembly writeups):
        serial = "L" + name[0] + Hex(Asc(name[0]) + 0x22) + name[0:2] + "-PZ"

    Notes:
    - Name must be longer than 4 characters.
    - Hex() in VB6 produces uppercase hex without '0x' prefix.
    - Asc() returns the ASCII code of the character.
    - 0x22 = 34 decimal.
    """
    first_char = name[0]
    asc_val = ord(first_char) + 34  # 34 == 0x22
    hex_val = hex(asc_val)[2:].upper()  # VB6 Hex() gives uppercase, no prefix
    serial = "L" + first_char + hex_val + name[0:2] + "-PZ"
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verifies name/serial pair for ECM1.
    Returns True if the serial matches the generated serial for the given name.
    Name must be longer than 4 characters.
    """
    if len(name) <= 4:
        return False
    return serial == gen_serial(name)


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name.
    Raises ValueError if name is too short.
    """
    if len(name) <= 4:
        raise ValueError("Name must be longer than 4 characters")
    return gen_serial(name)



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
