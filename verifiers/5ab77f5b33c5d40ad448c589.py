def gcd_and_first(a, b):
    """
    Implements the crackme's GCD-like loop.
    EAX = a, ECX = b
    Returns EAX after the loop (which is GCD(a,b)).
    """
    EAX = a
    ECX = b
    while ECX > 0:
        if EAX <= ECX:
            # swap so EAX >= ECX
            EDX = EAX
            EAX = ECX
            ECX = EDX
        EDX = EAX % ECX
        EAX = EAX // ECX
        EAX = ECX
        ECX = EDX
    return EAX


def keygen(name: str) -> str:
    """
    Generates the serial for the given name.
    Name must be 4-22 chars (no spaces).
    The serial has len(name)-1 characters (one per adjacent pair).
    Wait -- re-reading the C code: loop runs while i < strlen(name)-2,
    so it produces len(name)-2 digits (excluding the newline that fgets captures).
    Since we deal with a plain Python string (no trailing newline),
    the loop runs while i < len(name)-1, producing len(name)-1 digits.
    """
    # Validate
    if len(name) < 4 or len(name) > 22:
        raise ValueError("Name must be between 4 and 22 characters")
    if ' ' in name:
        raise ValueError("Spaces are not allowed in name")

    serial_chars = []
    # In the C code, fgets stores a trailing newline so strlen(name)-1 is
    # the real length. The loop: i < (strlen(name) - 2) means i < real_len - 1.
    # In Python we have no trailing newline, so loop: i < len(name) - 1
    for i in range(len(name) - 1):
        EAX = ord(name[i])
        EDX = ord(name[i])
        ECX = ord(name[i + 1])
        help_val = EAX  # saves original name[i]

        # GCD loop (Euclidean algorithm variant)
        while ECX > 0:
            if EAX <= ECX:
                EDX = EAX
                EAX = ECX
                ECX = EDX
            EDX = EAX % ECX
            EAX = EAX // ECX
            EAX = ECX
            ECX = EDX

        # EAX now holds GCD(name[i], name[i+1])
        EAX = EAX + help_val
        ECX = 0xA
        EDX = EAX % ECX
        EAX = EAX // ECX
        EDX += 0x30
        serial_chars.append(chr(EDX & 0xFF))

    return ''.join(serial_chars)


def verify(name: str, serial: str) -> bool:
    """
    Verifies that the given serial matches the name.
    Computes the expected serial and compares char by char.
    """
    try:
        expected = keygen(name)
    except ValueError:
        return False
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
