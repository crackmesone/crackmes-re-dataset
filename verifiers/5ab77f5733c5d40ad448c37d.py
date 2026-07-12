def verify(name, serial_str, auth_code_str=None):
    """
    This crackme does not use 'name' at all - it uses numeric ID, serial, and auth code.
    For compatibility with verify(name, serial) signature we treat:
      - name as the ID (integer or string)
      - serial as 'serial:authcode' or just serial (auth code check skipped if not provided)
    Returns True if all checks pass.
    """
    try:
        id_code = int(name)
    except (ValueError, TypeError):
        return False

    # Parse serial: may be 'serial:authcode'
    parts = str(serial_str).split(':')
    try:
        serial_code = int(parts[0])
    except (ValueError, TypeError):
        return False

    auth_code = None
    if len(parts) >= 2:
        try:
            auth_code = int(parts[1])
        except (ValueError, TypeError):
            return False
    elif auth_code_str is not None:
        try:
            auth_code = int(auth_code_str)
        except (ValueError, TypeError):
            return False

    # Check 1: 9999 < ID < 99999
    if not (9999 < id_code < 99999):
        return False

    # Check 2: 99 < serial < 999
    if not (99 < serial_code < 999):
        return False

    # Check 3: 849 < (ID * serial) // (ID + serial) < 900
    d = (id_code * serial_code) // (id_code + serial_code)
    if not (849 < d < 900):
        return False

    # Check 4 (auth code): if provided
    if auth_code is not None:
        # 9999 < auth_code < 99999
        if not (9999 < auth_code < 99999):
            return False
        # (ID - serial - 100) <= auth_code <= (ID + serial - 100)
        # From assembly: jl if AC < (ID - serial - 0x64), jg if AC > (ID + serial - 0x64)
        # ASSUMPTION: lower bound uses (ID - serial - 100), upper bound uses (ID + serial - 100)
        lower = id_code - serial_code - 100
        upper = id_code + serial_code - 100
        if not (lower <= auth_code <= upper):
            return False

    return True


def keygen(name):
    """
    Given an ID (passed as 'name'), find a valid serial and auth code.
    Returns a string 'serial:authcode'.
    """
    try:
        id_code = int(name)
    except (ValueError, TypeError):
        raise ValueError("name must be a numeric ID (10000 <= ID <= 99998)")

    if not (9999 < id_code < 99999):
        raise ValueError("ID must satisfy 9999 < ID < 99999")

    # Find serial: iterate 100..998, find one where 849 < (ID*serial)//(ID+serial) < 900
    serial_code = None
    for s in range(100, 999):
        d = (id_code * s) // (id_code + s)
        if 849 < d < 900:
            serial_code = s
            break

    if serial_code is None:
        raise ValueError("No valid serial found for this ID")

    # Auth code: use midpoint of valid range
    # ASSUMPTION: auth_code = ID - serial - 100 (from keygen source in solution 1)
    # The keygen source uses (id - serial - 99) but assembly shows 0x64 = 100
    # Solution 1 cpp uses -99, solution 2 Delphi uses -100; assembly shows SUB EAX,64h = -100
    auth_code = id_code - serial_code - 100

    # Verify auth code range 9999 < auth_code < 99999
    if not (9999 < auth_code < 99999):
        # Try to find a mid-range auth code within the valid window
        lower = id_code - serial_code - 100
        upper = id_code + serial_code - 100
        # pick midpoint
        auth_code = (lower + upper) // 2

    return f"{serial_code}:{auth_code}"



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
