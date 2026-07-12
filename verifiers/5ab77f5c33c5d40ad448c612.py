def verify(name: str, serial: str) -> bool:
    """Verify a serial for the given name."""
    if len(name) < 5:
        return False
    expected = keygen(name)
    return serial == expected


def keygen(name: str) -> str:
    """Generate a valid serial for the given name.

    Algorithm (from multiple writeups):
    1. First char of name
    2. Literal '-'
    3. Last char of name converted to uppercase
    4. Sum of ASCII values of all name chars + 0x6064 (24676), converted to decimal string
    5. Literal '-'
    6. (sum + 0x6064) + 0x6064 again (i.e., sum + 2*0x6064), converted to decimal string
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")

    first_char = name[0]
    last_char_upper = name[-1].upper()

    ascii_sum = sum(ord(c) for c in name)
    val1 = ascii_sum + 0x6064  # 24676
    val2 = val1 + 0x6064       # ascii_sum + 2*24676

    serial = f"{first_char}-{last_char_upper}{val1}-{val2}"
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
