def _compute_serial_base(name):
    """
    Step 1: sum of (ord(c) + 1) for each character in name (name must be exactly 7 chars)
    Step 2: multiply sum by ord(name[0])
    Step 3: XOR result with ord(name[6])
    """
    total = sum(ord(c) + 1 for c in name)
    result = total * ord(name[0])
    result ^= ord(name[6])
    return result


def keygen(name):
    """
    Find a digit character d (ascii 0x30..0x39) such that:
        serial_base * ord(d) produces a decimal string whose 3rd character (index 2)
        equals ord(d) itself (i.e. the digit d).
    The serial returned is str(serial_base * ord(d)).
    Returns None if no valid digit found.
    """
    if len(name) != 7:
        raise ValueError("Name must be exactly 7 characters long")

    base = _compute_serial_base(name)

    for code in range(0x30, 0x3A):  # '0' to '9'
        candidate = base * code
        serial_str = str(candidate)
        # The 3rd character of the serial (index 2) must match the digit used
        if len(serial_str) >= 3 and ord(serial_str[2]) == code:
            return serial_str

    return None  # No valid serial found for this name


def verify(name, serial):
    """
    Verify a name/serial pair:
    1. Name must be exactly 7 characters.
    2. Compute serial_base = (sum of ord(c)+1 for c in name) * ord(name[0]) XOR ord(name[6])
    3. Get the 3rd character (index 2) of the entered serial.
    4. Compute expected = serial_base * ord(serial[2])
    5. Check that str(expected) == serial
    """
    if len(name) != 7:
        return False
    if len(serial) < 3:
        return False

    base = _compute_serial_base(name)
    third_char_code = ord(serial[2])
    expected = base * third_char_code
    return str(expected) == serial



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
