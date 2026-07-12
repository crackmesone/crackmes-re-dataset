def _transform_char(bl, i):
    """
    For each character in the name:
    1. If the character is 'Z', 'z', or '9', decrement it by 1.
    2. The low byte of the serial word (BL) = transformed_char + 1
    3. The high byte of the serial word (BH) = ord('a') + i
    Serial is built as pairs: BL then BH (little-endian word stored, read as two chars)
    """
    # Step 1: special character substitution
    if bl in (ord('Z'), ord('z'), ord('9')):
        bl -= 1
    # Step 2: BL = char + 1, BH = 'a' + index
    # The word stored is BH:BL but compared as a 16-bit little-endian value
    # CX = word at serial[i*2], which means serial[i*2] = BL, serial[i*2+1] = BH
    # Multiple writeups confirm output order is: (bl+1) then ('a'+i)
    bl_out = bl + 1
    bh_out = ord('a') + i
    return chr(bl_out), chr(bh_out)


def keygen(name):
    """
    Generate a valid serial for the given name.
    Name must be at least 3 characters long.
    """
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters long")
    serial = ''
    for i, ch in enumerate(name):
        bl = ord(ch)
        lo, hi = _transform_char(bl, i)
        serial += lo + hi
    return serial


def verify(name, serial):
    """
    Returns True if the serial is valid for the given name.
    """
    if len(name) < 3:
        return False
    # Serial must be exactly 2 * len(name) characters
    if len(serial) != 2 * len(name):
        return False
    for i, ch in enumerate(name):
        bl = ord(ch)
        # Special character substitution
        if bl in (ord('Z'), ord('z'), ord('9')):
            bl -= 1
        # Expected BL (low byte of BX) = bl + 1
        # Expected BH (high byte of BX) = ord('a') + i
        expected_lo = bl + 1
        expected_hi = ord('a') + i
        # Serial characters at positions i*2 and i*2+1
        actual_lo = ord(serial[i * 2])
        actual_hi = ord(serial[i * 2 + 1])
        if actual_lo != expected_lo or actual_hi != expected_hi:
            return False
    return True



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
