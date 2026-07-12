# Reconstructed from the writeup by Anhkhoa
# The keygen loops 9 times, building a key character-by-character
# from a running sum derived from the ASCII values of the name.

def keygen(name: str) -> str:
    total = 0
    c1 = 0
    key = ""

    # Step 1: sum all ASCII values of the name
    for ch in name:
        total += ord(ch)

    # Step 2: generate 9 key characters
    for j in range(0, 9):
        c1 = total // (len(name) + j)
        if c1 == 0:
            # ASSUMPTION: avoid division by zero; break or skip
            break
        key += chr(c1)
        # Update running sum
        total += (total // c1)

    return key


def verify(name: str, serial: str) -> bool:
    """Check if serial matches the generated key for name."""
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
