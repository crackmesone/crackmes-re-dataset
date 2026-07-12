import socket

def _compute_serial(name: str, computer_name: str) -> str:
    """
    Algorithm (from the Delphi keygen source):
      1. Uppercase the name.
      2. a = sum of ord(c) for c in uppercase(name)
      3. a = a - sum of ord(c) for c in computer_name  (computer_name used as-is)
      4. a = (a * a) XOR 0xC0DE
      5. Serial = hex(a, 4 digits uppercase)
    """
    s = name.upper()
    a = sum(ord(c) for c in s)
    for c in computer_name:
        a -= ord(c)
    a = (a * a) ^ 0xC0DE
    # Format as 4-digit uppercase hex (matching Inttohex(a,4) in Delphi)
    # Delphi IntToHex with negative numbers still formats the raw integer bits
    # For a 32-bit signed integer, mask to 32 bits
    a = a & 0xFFFFFFFF
    return format(a, '08X')  # Delphi IntToHex(a,4) uses at least 4 digits; use 8 for full 32-bit


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against a name.
    Uses the current machine's computer name (as the crackme does).
    """
    computer_name = socket.gethostname().upper()  # ASSUMPTION: computer name used as returned by GetComputerName (uppercase on Windows)
    expected = _compute_serial(name, computer_name)
    return serial.upper().lstrip('0') == expected.lstrip('0') or serial.upper() == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name on the current machine.
    NOTE: The serial is machine-specific (depends on the computer name).
    """
    # ASSUMPTION: GetComputerName returns the hostname; on Windows it is typically uppercase already
    computer_name = socket.gethostname().upper()
    return _compute_serial(name, computer_name)



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
