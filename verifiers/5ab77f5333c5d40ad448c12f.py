# Reverse-engineered keygen for lincrkme_01 by digitalbyte
# Based on the writeup by macabre (crackmes.de)
#
# The writeup was truncated before the actual serial validation algorithm
# was fully described. What we know:
#   - The binary takes a username and serial via fgets()
#   - Username must be at least 6 characters long (cmp eax, 0x6 before length check)
#   - There is an anti-debug ptrace check that must be bypassed
#   - Serial is compared with strcmp() against a computed value
#   - Serial buffer is 0x33 (51) bytes
#   - The loop at 0x80485ad iterates over the username (loop variable at [ebp-0xac])
#
# ASSUMPTION: Based on common patterns for simple Linux crackmes of this era,
# the serial is likely computed by iterating over the username characters and
# performing arithmetic (e.g., summing, XORing, or multiplying ASCII values).
# The exact algorithm is NOT shown in the truncated writeup.

def _compute_serial(name: str) -> str:
    """
    ASSUMPTION: This is a placeholder. The real algorithm was not shown
    in the writeup (it was truncated). A common pattern would be something
    like summing ASCII values or XOR-folding, then formatting as decimal/hex.
    This implementation is a GUESS and almost certainly wrong.
    """
    # ASSUMPTION: sum of ASCII values of username characters, formatted as decimal
    total = 0
    for ch in name:
        total += ord(ch)
    return str(total)


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    Known constraints from the writeup:
      1. len(name) >= 6  (binary checks cmp eax, 0x6)
      2. strcmp(computed_serial, serial) == 0
    ASSUMPTION: _compute_serial is not confirmed; algorithm was truncated.
    """
    if len(name) < 6:
        return False
    # Strip trailing newline, as fgets would include it and the algo may or may not
    name_clean = name.rstrip('\n')
    serial_clean = serial.rstrip('\n')
    expected = _compute_serial(name_clean)
    return expected == serial_clean


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: Uses the placeholder _compute_serial; real algorithm unknown.
    """
    if len(name) < 6:
        raise ValueError(f"Username '{name}' is too short (must be >= 6 characters)")
    return _compute_serial(name)



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
