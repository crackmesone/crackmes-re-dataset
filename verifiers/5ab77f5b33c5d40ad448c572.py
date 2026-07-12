def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Algorithm from the reverse-engineered source:
      1. sum = len(name) * 0x22
      2. For each character in name: sum += ord(char) ^ 0x1A
      3. sum += 0x1A
      4. sum = sum * sum  (DWORD multiplication, but Python handles big ints natively)
      5. serial = str(sum)  (decimal string, unsigned)
    Note: The crackme limits name and serial to 10 chars each.
    The C keygen uses DWORD (32-bit unsigned), so we mask to 32 bits.
    """
    n = len(name)
    # ASSUMPTION: sum is treated as a 32-bit unsigned DWORD throughout
    total = (n * 0x22) & 0xFFFFFFFF
    for ch in name:
        total = (total + (ord(ch) ^ 0x1A)) & 0xFFFFFFFF
    total = (total + 0x1A) & 0xFFFFFFFF
    total = (total * total) & 0xFFFFFFFF
    return str(total)


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the expected value for name.
    The timer handler compares the entered serial (as a string) to the generated one.
    Also enforces: serial length must be < 10 (crackme rejects >= 10 chars).
    """
    if len(serial) >= 10:
        return False
    expected = keygen(name)
    return serial == expected



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
