# Reverse-engineered serial validation for hellspwn's CrackMe #3
# Based on the writeup by gyver75 (truncated). The writeup describes:
#   - Name length check (minimum length)
#   - Serial/code length check (minimum length)
#   - Anti-debug via hardware breakpoint clearing and thread context
#   - A second thread is created in FormCreate
#   - The actual math for serial generation was in the truncated portion
#
# ASSUMPTION: The writeup was truncated before revealing the exact serial algorithm.
# ASSUMPTION: Based on typical Delphi crackme patterns and the partial info:
#   - minimum name length appears to be ~4 characters
#   - minimum serial length appears to be ~6 characters
#   - The serial is likely derived from a checksum/hash of the name
# ASSUMPTION: Serial computation is unknown; placeholder logic inserted.

def _compute_serial(name: str) -> str:
    """
    ASSUMPTION: The actual serial computation algorithm is unknown due to
    truncation of the writeup. The real algorithm was implemented in
    Button5Click at 0x004557C5 in the Delphi binary.
    
    This is a PLACEHOLDER and will NOT produce correct serials.
    """
    # ASSUMPTION: typical Delphi crackme arithmetic on name bytes
    acc = 0
    for i, ch in enumerate(name):
        acc = (acc + ord(ch) * (i + 1)) & 0xFFFFFFFF
    # ASSUMPTION: serial is the decimal or hex representation of acc
    return str(acc)


MIN_NAME_LEN = 4   # ASSUMPTION: from writeup "ERROR: short name!" message
MIN_SERIAL_LEN = 6  # ASSUMPTION: from writeup "ERROR: short reg code!" message


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    
    Known checks from writeup:
    1. len(name) >= MIN_NAME_LEN
    2. len(serial) >= MIN_SERIAL_LEN
    3. serial must match computed value for name
    
    ASSUMPTION: step 3 uses _compute_serial which is a placeholder.
    """
    if len(name) < MIN_NAME_LEN:
        return False  # "ERROR: short name!"
    if len(serial) < MIN_SERIAL_LEN:
        return False  # "ERROR: short reg code!"
    expected = _compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    
    ASSUMPTION: _compute_serial is a placeholder; real algorithm unknown.
    """
    if len(name) < MIN_NAME_LEN:
        raise ValueError(f"Name must be at least {MIN_NAME_LEN} characters long.")
    serial = _compute_serial(name)
    # Pad if needed to meet minimum serial length
    while len(serial) < MIN_SERIAL_LEN:
        serial = '0' + serial
    return serial



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
