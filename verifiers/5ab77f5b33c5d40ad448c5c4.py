import ctypes

def count_every_chars_ascii_value(name: str) -> int:
    """Sum of ASCII values of all characters in name."""
    return sum(ord(c) for c in name)


def _u32(x):
    """Truncate to unsigned 32-bit."""
    return x & 0xFFFFFFFF


def _mul32(a, b):
    """Unsigned 32x32 multiply, return (high32, low32)."""
    result = _u32(a) * _u32(b)
    lo = result & 0xFFFFFFFF
    hi = (result >> 32) & 0xFFFFFFFF
    return hi, lo


def keygen(name: str):
    """
    Reproduce the inline ASM keygen from the writeup.

    Assembly (translated):
        dummy1 = sum of ASCII values of name
        EAX = dummy1
        EDX = EAX
        EDX = EDX << 5          # EDX = dummy1 * 32
        EDX = EDX - EAX         # EDX = dummy1 * 31
        EAX = 0x6830D6E5
        EDX = high32(EAX * EDX) # MUL EDX (unsigned 64-bit, keep EDX)
        EDX = EDX >> 8
        ECX = EDX + 0x2A5F828   # key1
        EAX = ECX + ECX*4       # EAX = ECX*5
        EAX = ECX + EAX*8      # EAX = ECX + ECX*40 = ECX*41
        EAX = EAX + EAX - 3    # EAX = ECX*82 - 3
        EBX = 0xCCCCCCCD
    loop:
        (EDX,_) = MUL(EAX, EBX)  # high32 of EAX*EBX
        EAX = EDX
        EAX = EAX >> 3
        if EAX > 0x1869F: goto loop
        key2 = EAX
    """
    dummy1 = count_every_chars_ascii_value(name)

    # EDX = dummy1 * 31  (all values treated as unsigned 32-bit)
    eax = _u32(dummy1)
    edx = _u32(eax << 5)      # SHL EDX,5  => dummy1*32
    edx = _u32(edx - eax)     # SUB EDX,EAX => dummy1*31

    # MUL EDX with 0x6830D6E5 => keep high 32 bits
    eax = 0x6830D6E5
    hi, _lo = _mul32(eax, edx)
    edx = hi

    # SHR EDX,8
    edx = edx >> 8

    # ECX = EDX + 0x2A5F828  => key1
    ecx = _u32(edx + 0x2A5F828)
    key1 = ecx

    # LEA EAX, [ECX + ECX*4]  => EAX = ECX*5
    eax = _u32(ecx + ecx * 4)
    # LEA EAX, [ECX + EAX*8]  => EAX = ECX + ECX*40 = ECX*41
    eax = _u32(ecx + eax * 8)
    # LEA EAX, [EAX + EAX - 3] => EAX = EAX*2 - 3
    eax = _u32(eax + eax - 3)

    ebx = 0xCCCCCCCD
    # Loop: multiply EAX by EBX, keep high 32 bits, SHR 3; repeat while > 0x1869F
    while True:
        hi, _lo = _mul32(eax, ebx)
        eax = hi
        eax = eax >> 3
        if eax <= 0x1869F:
            break

    key2 = eax
    return key1, key2


def verify(name: str, serial: str) -> bool:
    """
    The crackme asks for two serials (space or comma separated, or as 'serial1 serial2').
    Serial is expected as a string like '44431431 36433'.
    """
    parts = serial.strip().split()
    if len(parts) != 2:
        return False
    try:
        s1 = int(parts[0])
        s2 = int(parts[1])
    except ValueError:
        return False

    k1, k2 = keygen(name)
    return s1 == k1 and s2 == k2



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
