# Crackme 0.3 by Psycho Arjani - keygen/verify
# Based on the generate() function from ToMKoL's C keygen source

# Characters not allowed as the first character of the name
BAD_FIRST_CHARS = [0x20, 0x36, 0x38, 0x4E, 0x52, 0x54, 0x6A, 0x6C, 0x70]
# i.e.: ' ', '6', '8', 'N', 'R', 'T', 'j', 'l', 'p'


def _compute_serial_value(name: str) -> int | None:
    """Compute the integer l that goes into the serial format string.
    Returns None if the first character is forbidden.
    """
    if len(name) == 0:
        return None
    first = ord(name[0]) & 0xFF
    if first in BAD_FIRST_CHARS:
        return None
    last = ord(name[-1]) & 0xFF

    # All arithmetic is done as unsigned 32-bit (mask to 32 bits after each op)
    # The C code uses 'unsigned int' which is 32-bit on Windows.
    l = ((first * 0x13361) ^ 0xC) & 0xFFFFFFFF
    r = ((last  * 0x417F)  ^ 0x22) & 0xFFFFFFFF
    l = (l ^ r) & 0xFFFFFFFF
    return l


def keygen(name: str) -> str | None:
    """Generate a valid serial for the given name.
    Returns None if the name starts with a forbidden character or is empty.
    """
    val = _compute_serial_value(name)
    if val is None:
        return None
    return f"CrKme-{val}-PsY"


def verify(name: str, serial: str) -> bool:
    """Verify whether the serial is correct for the given name."""
    expected = keygen(name)
    if expected is None:
        return False
    return serial == expected



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
