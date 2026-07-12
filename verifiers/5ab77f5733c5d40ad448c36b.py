# GenoCide Crackme 10 by Gandalf - Reverse-engineered validation
# Based on the tutorial by {Cronos}
#
# From the writeup we can determine:
#   1. check_str_lengths: name >= 5 chars, serial >= 1 char, unlock_code >= 1 char
#   2. check_str3: validates the serial (flag2)
#   3. final_check: validates the unlock code (flag3)
#
# The writeup was truncated before showing the actual serial and unlock code
# computation algorithms. The structures below are based on what was shown,
# with ASSUMPTION comments for the missing parts.
#
# The program has THREE fields: name, serial, unlock_code
# verify() here takes name and serial as a combined (serial, unlock_code) tuple
# or we expose a three-argument form.

def _check_str_lengths(name, serial, unlock_code):
    """check_str_lengths: name >= 5, serial >= 1, unlock_code >= 1"""
    if len(name) < 5:
        return False  # flag1 = 1 (bad)
    if len(serial) < 1:
        return False  # flag1 = 1 (bad)
    if len(unlock_code) < 1:
        return False  # flag1 = 1 (bad)
    return True  # flag1 = 0 (good)


def _check_serial(name, serial):
    """
    check_str3: validates the serial against the name.
    The writeup was truncated before showing this logic.
    ASSUMPTION: A common Delphi crackme pattern is to sum/XOR character
    ordinals of the name and produce a decimal or hex string as the serial.
    We implement a plausible name->serial derivation below, but this is
    NOT confirmed by the writeup.
    """
    # ASSUMPTION: serial is derived from summing ASCII values of name chars
    # multiplied by their 1-based position, then formatted as decimal string.
    total = 0
    for i, ch in enumerate(name):
        total += ord(ch) * (i + 1)
    expected = str(total)
    return serial == expected


def _check_unlock_code(name, serial, unlock_code):
    """
    final_check: validates the unlock_code against name and/or serial.
    The writeup was truncated before showing this logic.
    ASSUMPTION: unlock_code is derived from XOR-ing serial digits or
    from a second transformation of the name.
    """
    # ASSUMPTION: unlock_code is derived from XOR of all serial character ordinals
    xor_val = 0
    for ch in serial:
        xor_val ^= ord(ch)
    expected = str(xor_val)
    return unlock_code == expected


def verify(name, serial_and_unlock):
    """
    Public verify interface.
    serial_and_unlock should be a tuple (serial, unlock_code) or a string
    formatted as 'serial:unlock_code'.
    Returns True if all checks pass.
    """
    if isinstance(serial_and_unlock, tuple):
        serial, unlock_code = serial_and_unlock
    elif isinstance(serial_and_unlock, str) and ':' in serial_and_unlock:
        serial, unlock_code = serial_and_unlock.split(':', 1)
    else:
        # Treat whole thing as serial with empty unlock (will fail length check)
        serial = serial_and_unlock
        unlock_code = ''

    # Step 1: length checks
    if not _check_str_lengths(name, serial, unlock_code):
        return False

    # Step 2: serial check
    if not _check_serial(name, serial):
        return False

    # Step 3: unlock code check
    if not _check_unlock_code(name, serial, unlock_code):
        return False

    return True


def keygen(name):
    """
    Generate (serial, unlock_code) for a given name.
    Requires name >= 5 characters.
    Returns a tuple (serial, unlock_code).
    """
    if len(name) < 5:
        raise ValueError('Name must be at least 5 characters long')

    # ASSUMPTION: derive serial as per _check_serial
    total = 0
    for i, ch in enumerate(name):
        total += ord(ch) * (i + 1)
    serial = str(total)

    # ASSUMPTION: derive unlock_code as per _check_unlock_code
    xor_val = 0
    for ch in serial:
        xor_val ^= ord(ch)
    unlock_code = str(xor_val)

    return (serial, unlock_code)



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
