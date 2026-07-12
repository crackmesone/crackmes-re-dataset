import struct

def _compute_serial_15(name: str) -> str:
    """
    Name length == 15
    hash1 = "'TDHUWNHI"
    loop ecx = 0, 2, 4, 6, 8 (5 iterations? check boundary)
    Actually the assembly says: inc ecx twice, cmp ecx,8 jnz
    So ecx goes 0,2,4,6 -> after 4th iteration ecx becomes 8, loop ends.
    esi goes 0,1,2,3 -> 4 serial chars

    serial[esi] = (name[ecx] >> 4) + (hash1[ecx] >> 2) + 0x20
    """
    hash1 = "'TDHUWNHI"
    serial = []
    ecx = 0
    esi = 0
    while True:
        bl = ord(name[ecx]) & 0xFF
        bh = ord(hash1[ecx]) & 0xFF
        bh = (bh >> 2) & 0xFF
        bl = (bl >> 4) & 0xFF
        bl = (bl + bh + 0x20) & 0xFF
        serial.append(chr(bl))
        ecx += 2
        esi += 1
        if ecx == 8:
            break
    return ''.join(serial)


def _compute_serial_16(name: str) -> str:
    """
    Name length == 16
    hash2 = "'DUFDL*EUBFL"
    loop ecx = 0, 3, 6, 9 -> after 4th iteration ecx becomes 12 (0x0C), loop ends.
    esi goes 0,1,2,3 -> 4 serial chars

    serial[esi] = (name[ecx] >> 2) + (hash2[ecx] >> 3) + 0x20
    """
    hash2 = "'DUFDL*EUBFL"
    serial = []
    ecx = 0
    esi = 0
    while True:
        bl = ord(name[ecx]) & 0xFF
        bh = ord(hash2[ecx]) & 0xFF
        bl = (bl >> 2) & 0xFF
        bh = (bh >> 3) & 0xFF
        bl = (bl + bh + 0x20) & 0xFF
        serial.append(chr(bl))
        ecx += 3
        esi += 1
        if ecx == 0x0C:
            break
    return ''.join(serial)


def _compute_serial_17(name: str) -> str:
    """
    Name length == 17
    hash4 = "'SOB'DHCB'DUFDLBU"
    loop ecx = 0, 4, 8, 12 -> after 4th iteration ecx becomes 16 (0x10), loop ends.
    esi goes 0,1,2,3 -> 4 serial chars

    serial[esi] = (name[ecx] >> 4) + hash4[ecx]  (no +0x20 based on cosmos asm)
    
    Note: br0ken keygen also has no +0x20 for len==17 but cosmos asm also lacks it.
    Both solutions agree: no +0x20 for length-17 case.
    """
    hash4 = "'SOB'DHCB'DUFDLBU"
    serial = []
    ecx = 0
    esi = 0
    while True:
        bl = ord(name[ecx]) & 0xFF
        bh = ord(hash4[ecx]) & 0xFF
        bl = (bl >> 4) & 0xFF
        bl = (bl + bh) & 0xFF
        serial.append(chr(bl))
        ecx += 4
        esi += 1
        if ecx == 0x10:
            break
    return ''.join(serial)


def keygen(name: str) -> str:
    """
    Generate serial for a given name.
    Name must be 15, 16, or 17 characters long.
    """
    n = len(name)
    if n == 15:
        return _compute_serial_15(name)
    elif n == 16:
        return _compute_serial_16(name)
    elif n == 17:
        return _compute_serial_17(name)
    else:
        raise ValueError(f"Name must be 15, 16, or 17 characters long (got {n})")


def verify(name: str, serial: str) -> bool:
    """
    Verify that the serial matches the one computed from the name.
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
