def keygen(name: str) -> str:
    """
    Keygen for AndSoOn CrackMe #1
    Algorithm (from kao's writeup):
      1. Uppercase the name
      2. Sum all character ordinal values
      3. XOR with 0x00031337
      4. Integer-divide by 10
      5. Multiply by 20
      6. Add 0x5EFC051A
    The serial is formatted as '$<hex_value>' (lowercase hex, no leading zeros,
    prefixed with '$') based on the fmt string in the ASM keygen: "$%x"
    """
    name_upper = name.upper()
    total = sum(ord(c) for c in name_upper)
    total ^= 0x00031337
    total //= 10
    total *= 20
    total += 0x5EFC051A
    # Mask to 32-bit unsigned to match Pascal longint / x86 register behavior
    total &= 0xFFFFFFFF
    return '$%x' % total


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    The serial is expected to be in the format '$<hex>' (case-insensitive).
    """
    expected = keygen(name)
    return serial.strip().lower() == expected.lower()



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
