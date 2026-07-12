import ctypes

def signed_char(x):
    """Simulate C (signed char) cast"""
    x = x & 0xFF
    if x >= 128:
        return x - 256
    return x

def compute_psw(name):
    """Compute the intermediate password value (ecx) based on username length."""
    namelen = len(name)
    if namelen < 1 or namelen > 15:
        raise ValueError("Username must be 1-15 chars")

    # Build arr: each char + 0x15
    arr = [0] * 16
    for i in range(namelen):
        arr[i] = (ord(name[i]) + 0x15) & 0xFF

    def sc(i):
        return signed_char(arr[i])

    # Helper for the 0x8000000f modulo pattern used in cases 1, 7, 11
    def mod_pattern(val):
        """Simulate: eax = val & 0x8000000f; if eax < 0: eax--; eax |= 0xfffffff0; eax++"""
        # This is equivalent to Python's val % 16 using arithmetic (signed) modulo
        # In C with signed 32-bit: eax = val & 0x8000000f
        # then if eax < 0: eax = ((eax-1)|0xfffffff0)+1
        # This computes val mod 16 as a value in [0..15]
        eax = ctypes.c_int32(val & 0x8000000f).value
        if eax < 0:
            eax = eax - 1
            eax = eax | (-16)  # 0xfffffff0 as signed = -16
            eax = eax + 1
        return eax

    ecx = 0
    eax = 0
    edx = 0

    if namelen == 1:
        ecx = sc(0)
        eax = mod_pattern(ecx)
        ecx = ctypes.c_int32(ecx + 0xbb - eax).value

    elif namelen == 2:
        edx = sc(0)
        eax = sc(1)
        ecx = ctypes.c_int32((edx - eax) * eax + edx).value

    elif namelen == 3:
        eax = sc(0)
        ecx = ctypes.c_int32(1 - eax).value
        eax = sc(2)
        ecx = ctypes.c_int32(ecx * eax).value
        eax = sc(1)
        ecx = ctypes.c_int32(ecx + eax).value

    elif namelen == 4:
        eax = sc(3)
        ecx = sc(2)
        eax = ctypes.c_int32(eax // ecx).value
        ecx = ctypes.c_int32(sc(0) - eax).value
        eax = sc(1)
        ecx = ctypes.c_int32(ecx * eax).value
        ecx = ctypes.c_int32(ecx + sc(0)).value

    elif namelen == 5:
        eax = ctypes.c_int32(sc(1) + 0x50d).value
        ecx = ctypes.c_int32(sc(3) + eax).value
        eax = sc(4)
        ecx = ctypes.c_int32(ecx * eax).value
        eax = sc(2)
        ecx = ctypes.c_int32(ecx + eax).value

    elif namelen == 6:
        edx = mod_pattern(sc(5))
        eax = sc(4)
        ecx = sc(3)
        edx = ctypes.c_int32(edx * eax).value
        eax = ctypes.c_int32(sc(0) + 0x10f2c).value
        ecx = ctypes.c_int32(ecx + eax - edx).value

    elif namelen == 7:
        eax = sc(3)
        edx = sc(2)
        eax = ctypes.c_int32(eax * edx).value
        eax = mod_pattern(eax)
        ecx = sc(6)
        ecx = ctypes.c_int32(ecx - eax).value
        eax = sc(4)
        ecx = ctypes.c_int32(ecx - eax).value
        eax = sc(0)
        ecx = ctypes.c_int32(ecx - (eax - 0x1a4)).value
        ecx = ctypes.c_int32(ecx + edx).value

    elif namelen == 8:
        eax = sc(3)
        ecx = sc(6)
        edx = ctypes.c_int32(eax % ecx).value
        ecx = sc(7)
        eax = sc(5)
        ecx = ctypes.c_int32(ecx - (edx - eax)).value
        eax = sc(2)
        ecx = ctypes.c_int32(ecx + eax).value

    elif namelen == 9:
        ecx = sc(8)
        eax = sc(4)
        eax = ctypes.c_int32(eax * ecx).value
        edx = sc(6)
        ecx = eax
        eax = sc(5)
        ecx = ctypes.c_int32(ecx >> 1).value
        ecx = ctypes.c_int32(ecx * edx).value
        edx = sc(3)
        eax = ctypes.c_int32(eax * edx).value
        ecx = ctypes.c_int32(ecx + eax).value

    elif namelen == 10:
        eax = sc(9)
        ecx = ctypes.c_int32(eax * 0x2f).value
        eax = ctypes.c_int32(sc(8) + ctypes.c_int32(0xffffff45).value).value
        ecx = ctypes.c_int32(ecx + eax).value
        eax = sc(5)
        ecx = ctypes.c_int32(ecx * eax).value

    elif namelen == 11:
        edx = mod_pattern(sc(6))
        eax = sc(5)
        ecx = sc(10)
        edx = ctypes.c_int32(edx * eax).value
        eax = ctypes.c_int32(sc(0) + 0xbb).value
        ecx = ctypes.c_int32(ecx - (edx - eax)).value

    elif namelen == 12:
        eax = sc(7)
        ecx = sc(10)
        eax = ctypes.c_int32(eax // ecx).value
        ecx = sc(9)
        eax = sc(11)
        ecx = ctypes.c_int32(ecx * eax).value
        eax = sc(4)
        ecx = ctypes.c_int32(ecx - eax).value

    elif namelen == 13:
        eax = sc(10)
        ecx = sc(7)
        ecx = ctypes.c_int32(ecx - eax).value
        eax = sc(6)
        ecx = ctypes.c_int32(ecx + eax).value
        eax = sc(3)
        ecx = ctypes.c_int32(ecx + eax).value
        eax = sc(12)
        ecx = ctypes.c_int32(ecx * eax).value
        eax = sc(0)
        ecx = ctypes.c_int32(ecx * eax).value
        eax = sc(5)
        ecx = ctypes.c_int32(ecx - eax).value

    elif namelen == 14:
        eax = sc(5)
        edx = sc(8)
        ecx = sc(10)
        edx = ctypes.c_int32(edx + eax).value
        eax = sc(11)
        edx = ctypes.c_int32(edx * eax).value
        eax = sc(6)
        ecx = ctypes.c_int32(ecx - (edx - eax)).value
        eax = sc(2)
        ecx = ctypes.c_int32(ecx * eax).value
        ecx = ctypes.c_int32(ecx + 0x5c0).value

    elif namelen == 15:
        eax = sc(5)
        edx = sc(10)
        ecx = sc(14)
        edx = ctypes.c_int32(edx * eax).value
        eax = ctypes.c_int32(sc(0) + 0x114b).value
        ecx = ctypes.c_int32(ecx - (edx - eax)).value

    return ctypes.c_int32(ecx).value


def gen(psw, first_char, i):
    """Generate password for seed value i (1..4).
    psw: intermediate password value
    first_char: name[0] as unsigned byte
    i: seed (1..4)
    """
    a = first_char & 0xFF  # unsigned char
    res = 0
    if i == 1:
        res = signed_char(a) + psw
    elif i == 2:
        res = (signed_char(a) + psw) * psw
    elif i == 3:
        res = psw * 3
    elif i == 4:
        # case i==4 falls through to skip (res=0)
        res = 0
    res = ctypes.c_int32(res + 0x12d).value
    # Return as unsigned 32-bit (matching %u format)
    return ctypes.c_uint32(res).value


def verify(name, serial):
    """Verify if serial is a valid password for name.
    serial should be an integer or string of digits.
    Returns True if serial matches any of the 4 possible passwords.
    """
    if isinstance(serial, str):
        try:
            serial = int(serial)
        except ValueError:
            return False

    namelen = len(name)
    if namelen < 1 or namelen > 15:
        return False

    try:
        psw = compute_psw(name)
    except Exception:
        return False

    first_char = ord(name[0])
    for i in range(1, 5):
        candidate = gen(psw, first_char, i)
        if candidate == serial:
            return True
    return False


def keygen(name):
    """Returns all 4 valid passwords for the given name."""
    namelen = len(name)
    if namelen < 1 or namelen > 15:
        raise ValueError("Username must be 1-15 chars")

    psw = compute_psw(name)
    first_char = ord(name[0])
    passwords = []
    for i in range(1, 5):
        passwords.append(gen(psw, first_char, i))
    return passwords



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
