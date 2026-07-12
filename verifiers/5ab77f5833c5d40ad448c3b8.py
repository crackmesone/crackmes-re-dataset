def compute_serial(id_val: int) -> int:
    """
    Implements the serial generation algorithm from Ank83's KeyGenMe #2.

    Steps (from assembly / multiple writeups):
      1. nID = id_val + 1
      2. nID = nID + nID   (i.e., nID *= 2)
      3. nID = nID - 1
         => nID = (id_val + 1) * 2 - 1  = 2*id_val + 1
      4. nID = nID * nID  (square it)
      5. Loop: counter from 1 to 19 (counter < 20, i.e., 0x14)
         nID -= counter  for counter in 1..19
         Sum of 1..19 = 190, so nID -= 190

    Note: The Delphi solution loops i from 0 to 0x13 (0 to 19 inclusive),
    which subtracts 0+1+2+...+19 = 190.
    The assembly loops counter from 1 to 19 (counter < 20), subtracting 1+2+...+19 = 190.
    Both give the same result (subtracting 0 is a no-op).
    """
    nID = id_val
    nID += 1        # nID = id + 1
    nID += nID      # nID = (id + 1) * 2
    nID -= 1        # nID = (id + 1) * 2 - 1  = 2*id + 1
    nID *= nID      # nID = (2*id + 1)^2
    # Loop counter from 1 to 19 inclusive (counter < 20 = 0x14)
    for counter in range(1, 20):  # 1..19
        nID -= counter
    return nID


def verify(name: str, serial: str) -> bool:
    """
    The crackme only uses a numeric ID (0..999), not a name.
    'name' here is treated as the ID string.
    Returns True if serial matches the computed value.
    """
    # ASSUMPTION: 'name' parameter is used as the numeric ID (the crackme has no name field)
    try:
        id_val = int(name)
        serial_val = int(serial)
    except ValueError:
        return False
    if id_val < 0 or id_val > 999:
        return False
    return compute_serial(id_val) == serial_val


def keygen(name: str) -> str:
    """
    Given an ID (passed as 'name'), returns the valid serial.
    ID must be in range 0..999.
    """
    # ASSUMPTION: 'name' is the numeric ID string
    try:
        id_val = int(name)
    except ValueError:
        raise ValueError(f"ID must be a numeric string (0-999), got: {name!r}")
    if id_val < 0 or id_val > 999:
        raise ValueError(f"ID must be in range 0-999, got: {id_val}")
    return str(compute_serial(id_val))



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
