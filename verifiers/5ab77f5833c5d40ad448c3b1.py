def keygen(name: str) -> str:
    """
    Generate the serial for a given name.
    
    Step 1: XOR each character of name with a counter starting at 1
    Step 2: XOR each character of the result from step 1 with a counter starting at 10
    The result is the serial (stored as raw bytes/chars).
    
    Note: The serial is a string of characters whose ordinal values may include
    non-printable bytes, matching the original Delphi behavior.
    """
    # Step 1: XOR name characters with cl starting at 1
    intermediate = []
    cl = 1
    for ch in name:
        bl = ord(ch) ^ cl
        intermediate.append(bl)
        cl += 1

    # Step 2: XOR intermediate characters with cl starting at 10
    result = []
    cl = 10
    for bl in intermediate:
        bl2 = bl ^ cl
        result.append(bl2)
        cl += 1

    # Build serial string from byte values
    serial = ''.join(chr(b) for b in result)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the expected value for the given name.
    The crackme sets Edit2 (serial field) automatically as name is typed,
    so the 'correct' serial is exactly the output of keygen(name).
    """
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
