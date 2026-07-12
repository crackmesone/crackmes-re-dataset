# Reverse-engineered keygen for parfen's KeygenMe
# Based on the solution writeup by Obnoxious (crackmes.de)
# The writeup was truncated before full algorithm details were shown,
# so some parts are inferred from common patterns for this era of crackmes.

# ASSUMPTION: The algorithm iterates over the name characters,
# performing arithmetic on their ASCII values to produce a serial.
# The writeup shows a call to 0x00401220 which returns AL=0 for bad serial.
# The exact inner loop was not fully shown due to truncation.

def compute_serial(name: str) -> int:
    """
    ASSUMPTION: A common pattern for VC++ crackmes of this type:
    - Iterate over name characters
    - Accumulate a value using ASCII codes
    - The serial is compared against this computed value
    This is speculative since the writeup was truncated.
    """
    # ASSUMPTION: simple weighted sum of character values
    result = 0
    for i, ch in enumerate(name):
        result += ord(ch) * (i + 1)
    # ASSUMPTION: result is taken modulo some value or masked
    result = result & 0xFFFFFFFF
    return result


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: Serial is the decimal or hex string representation
    of the computed hash of the name.
    """
    if not name or not serial:
        return False
    expected = compute_serial(name)
    # ASSUMPTION: serial is provided as decimal string
    try:
        serial_int = int(serial)
        return serial_int == expected
    except ValueError:
        pass
    # ASSUMPTION: also try hex
    try:
        serial_int = int(serial, 16)
        return serial_int == expected
    except ValueError:
        pass
    return False


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    ASSUMPTION: Returns decimal string of computed value.
    """
    if not name:
        raise ValueError('Name must not be empty')
    return str(compute_serial(name))



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
