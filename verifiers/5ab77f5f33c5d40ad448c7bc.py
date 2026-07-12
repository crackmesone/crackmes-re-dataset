import ctypes

def _to_dword(val):
    """Simulate 32-bit unsigned integer overflow (DWORD wrapping)."""
    return val & 0xFFFFFFFF

def compute_serial(name: str) -> int:
    """
    Algorithm from the writeup:
        SERIAL = 0
        if name_length > 0x13: name_length = 0x13
        for i in range(name_length):
            TEMP = 0x1337 * NAME[i]   # NAME[i] is the byte value of the char
            SERIAL += TEMP
        SERIAL *= name_length
    All arithmetic is 32-bit unsigned (DWORD).
    """
    name_bytes = name.encode('ascii', errors='replace')
    name_length = len(name_bytes)
    if name_length > 0x13:
        name_length = 0x13

    serial = 0
    for i in range(name_length):
        temp = _to_dword(0x1337 * name_bytes[i])
        serial = _to_dword(serial + temp)

    serial = _to_dword(serial * name_length)
    return serial


def keygen(name: str) -> str:
    """Generate the correct serial string for the given name."""
    if not name:
        raise ValueError('Name must not be empty')
    return str(compute_serial(name))


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    The program reads both as strings; the serial is compared as a decimal integer string.
    # ASSUMPTION: The crackme compares the computed serial (formatted with %i / sprintf as signed decimal)
    # against the user-supplied serial string. We replicate that here.
    """
    if not name or not serial:
        return False
    try:
        user_serial = int(serial)
    except ValueError:
        return False
    computed = compute_serial(name)
    # The C code uses sprintf("%i", dw_serial) which treats the DWORD as a signed int
    # ASSUMPTION: interpret the DWORD as a signed 32-bit integer for the %i format
    computed_signed = ctypes.c_int32(computed).value
    return user_serial == computed_signed



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
