def keygen(name):
    """
    Generate serial for a given name.
    Name must be at least 6 characters.
    
    Algorithm:
      For each character c in name:
        x1 = ord(c) + 0x0B
        x2 = len(name) + 0x13
        x3 = (x1 * x2) + x1 + len(name)
        Convert x3 to decimal string, reverse it -> part
      Concatenate all parts into one long string S
      Format: S[0:5] + '-' + S[5:10] + '-' + S[10:15]
    """
    if len(name) < 6:
        raise ValueError("Name must be at least 6 characters long")
    
    n = len(name)
    parts = []
    for c in name:
        x1 = ord(c) + 0x0B
        x2 = n + 0x13
        x3 = (x1 * x2) + x1 + n
        # Convert to decimal string and reverse
        part = str(x3)[::-1]
        parts.append(part)
    
    S = ''.join(parts)
    # Take first 15 characters, split as 5-5-5 with dashes
    # (discard the last 3 characters of 6th part per writeup)
    serial = S[0:5] + '-' + S[5:10] + '-' + S[10:15]
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    """
    try:
        expected = keygen(name)
        return serial == expected
    except ValueError:
        return False



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
