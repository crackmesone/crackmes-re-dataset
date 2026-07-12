def verify(name: str, serial: str) -> bool:
    """
    Validate a serial for the given name.

    Algorithm (from keygen.asm):
    1. Compute sum of ASCII values of all characters in name.
    2. Subtract ord('t') (0x74). If negative -> invalid name.
    3. Divide (eax=sum-0x74) by 4: quotient -> eax, remainder -> edx.
    4. If quotient > 0xFF - 4 (i.e. 251) -> invalid name.
    5. base = quotient (al after div)
    6. Serial bytes:
         Serial[0] = (base - ord('R')) & 0xFF    # 0x52
         Serial[1] = (base + ord('u')) & 0xFF    # 0x75
         Serial[2] = (base ^ ord('s')) & 0xFF    # 0x73
         Serial[3] = ord('-')  # fixed from template "---s-"
         Serial[4] = ord('s')  # fixed from template "---s-"
         Serial[5] = (base + edx - ord('a')) & 0xFF  # 0x61
       The serial template is "---s-" (6 chars) with a null terminator,
       so indices 0,1,2,5 are computed and index 3 stays '-', index 4 stays 's'.
    """
    if not name:
        return False

    # Step 1: sum of all ASCII bytes including null terminator? No - the loop
    # adds bytes until dl==0 (null), then subtracts at the end.
    # The asm loop: movzx edx, b[ecx]; add eax, edx; inc ecx; test dl,dl; jnz <
    # This adds the null terminator byte (0) before testing, so effectively
    # it is just the sum of name bytes (null contributes 0).
    total = sum(ord(c) for c in name)  # null adds 0, so ignore it

    # Step 2
    total -= ord('t')  # 0x74
    if total < 0:
        return False

    # Step 3: 32-bit unsigned division by 4
    # eax = total (after sub), treat as unsigned 32-bit
    eax = total & 0xFFFFFFFF
    quotient = eax // 4
    remainder = eax % 4

    # Step 4
    if quotient > 0xFF - 4:  # > 251
        return False

    base = quotient & 0xFF
    edx_rem = remainder & 0xFF

    # Step 5: compute expected serial bytes
    expected = [
        (base - ord('R')) & 0xFF,   # Serial[0]
        (base + ord('u')) & 0xFF,   # Serial[1]
        (base ^ ord('s')) & 0xFF,   # Serial[2]
        ord('-'),                    # Serial[3] fixed
        ord('s'),                    # Serial[4] fixed
        (base + edx_rem - ord('a')) & 0xFF,  # Serial[5]
    ]

    # Serial is 6 bytes (printable chars expected by the dialog)
    if len(serial) != 6:
        return False

    return all(ord(serial[i]) == expected[i] for i in range(6))


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Returns empty string if name is invalid.
    """
    if not name:
        return ''

    total = sum(ord(c) for c in name)
    total -= ord('t')
    if total < 0:
        return ''

    eax = total & 0xFFFFFFFF
    quotient = eax // 4
    remainder = eax % 4

    if quotient > 0xFF - 4:
        return ''

    base = quotient & 0xFF
    edx_rem = remainder & 0xFF

    s0 = (base - ord('R')) & 0xFF
    s1 = (base + ord('u')) & 0xFF
    s2 = (base ^ ord('s')) & 0xFF
    s3 = ord('-')
    s4 = ord('s')
    s5 = (base + edx_rem - ord('a')) & 0xFF

    return ''.join(chr(b) for b in [s0, s1, s2, s3, s4, s5])



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
