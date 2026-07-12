def keygen(name: str) -> str:
    """
    Reconstructed from KGCrackme4.asm KeyGeneration procedure.

    For each character in the name (index cl starting at 0):
        al = char_value + cl          (add al, cl)
        al = al XOR cl                (xor al, cl)
        AX = (al as 8-bit) / 0x1A    (div bl where bl=0x1A)
            -> quotient in AL, remainder in AH
        shr AX, 8  => AL = AH (the remainder becomes the low byte)
        al = al + 0x41                (add al, 0x41  => shift into A-Z range)
        output that character
        increment cl (index)
    """
    if not name:
        return ''
    
    serial_chars = []
    cl = 0
    bl = 0x1A  # divisor
    
    for ch in name:
        al = ord(ch) & 0xFF
        # add al, cl
        al = (al + cl) & 0xFF
        # xor al, cl
        al = (al ^ cl) & 0xFF
        # div bl: AX = AL (zero-extend), divide by BL
        # quotient in AL, remainder in AH
        ax = al  # zero-extended into 16-bit
        quotient = ax // bl
        remainder = ax % bl
        # shr AX, 8 => AL = AH (remainder)
        al = remainder & 0xFF
        # add al, 0x41
        al = (al + 0x41) & 0xFF
        serial_chars.append(chr(al))
        cl = (cl + 1) & 0xFF
    
    return ''.join(serial_chars)


def verify(name: str, serial: str) -> bool:
    """
    Verify by generating the expected serial and comparing.
    The crackme checks the generated serial character by character.
    """
    if not name:
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
