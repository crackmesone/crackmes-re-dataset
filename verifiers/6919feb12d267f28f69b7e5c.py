import ctypes

def compute_serial(name: str) -> int:
    """
    Implements the same logic as the crackme:
    1. Apply alternating lower/upper to each character (even index -> lower, odd index -> upper)
    2. Take the first 8 characters of the result
    3. Apply atoi (parse leading integer, return 0 if starts with non-digit)
    """
    # Step 1: zigzag case transform
    modified = []
    for i, ch in enumerate(name):
        if (i & 1) == 0:
            modified.append(ch.lower())
        else:
            modified.append(ch.upper())
    modified_str = ''.join(modified)

    # Step 2: truncate to first 8 characters (strncpy behavior)
    truncated = modified_str[:8]

    # Step 3: atoi - parse leading integer characters, return 0 if none
    # atoi skips leading whitespace, then reads optional sign + digits
    import re
    m = re.match(r'\s*([+-]?\d+)', truncated)
    if m:
        # atoi returns a C int (32-bit signed), simulate overflow
        val = int(m.group(1))
        # Clamp to 32-bit signed int range as C atoi would
        val = ctypes.c_int(val).value
        return val
    else:
        return 0


def verify(name: str, serial: str) -> bool:
    """
    Verify username + serial pair.
    The program reads the serial as a double via scanf, then compares:
      (double)atoi_result == serial_input
    We accept serial as a string (like the program's input) and convert to int.
    """
    if not (8 <= len(name) <= 12):
        return False
    expected = compute_serial(name)
    try:
        user_serial = int(serial)
    except ValueError:
        return False
    return expected == user_serial


def keygen(name: str) -> str:
    """
    Generate the correct serial for a given username.
    Username must be 8-12 characters.
    If username starts with a letter, serial is '0'.
    If username starts with digits, serial is the integer parsed from the
    first 8 characters of the zigzag-cased username.
    """
    if not (8 <= len(name) <= 12):
        raise ValueError(f"Username must be between 8 and 12 characters, got {len(name)}")
    serial = compute_serial(name)
    return str(serial)



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
