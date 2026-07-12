import random
import struct

def umulhi(a, b):
    """Return the upper 32 bits of the 64-bit product of two 32-bit unsigned integers."""
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    return ((a * b) >> 32) & 0xFFFFFFFF

def u32(x):
    return x & 0xFFFFFFFF

def verify(name, serial):
    """
    Verify a serial (64 hex char string) for this crackme.
    NOTE: The crackme does NOT use 'name' in the check - serial is standalone.
    """
    serial = serial.strip()
    if len(serial) != 64:
        return False
    # Parse 8 x 32-bit big-endian integers from hex string
    try:
        s = []
        for i in range(8):
            s.append(int(serial[i*8:(i+1)*8], 16))
    except ValueError:
        return False
    s1, s2, s3, s4, s5, s6, s7, s8 = s

    mask28 = 0x6487169F
    mask16 = 0x20890481
    mask35 = 0x5B7A027F
    mask47 = 0x11258023

    # Derive intermediate values from serial
    v161 = u32(((s1 ^ s6) & mask16) ^ s1)
    v166 = u32(((s1 ^ s6) & mask16) ^ s6)
    v282 = u32(((s2 ^ s8) & mask28) ^ s2)
    v288 = u32(((s2 ^ s8) & mask28) ^ s8)
    v353 = u32(((s3 ^ s5) & mask35) ^ s3)
    v355 = u32(((s3 ^ s5) & mask35) ^ s5)
    v474 = u32(((s4 ^ s7) & mask47) ^ s4)
    v477 = u32(((s4 ^ s7) & mask47) ^ s7)

    # Check 1: v474 XOR v288 XOR 0x35059FC5 == 0x48A86FC4
    if u32(v474 ^ v288 ^ 0x35059FC5) != 0x48A86FC4:
        return False

    # Check 2: v166 XOR v355 XOR 0x54A80618 == 0x489AC581
    if u32(v166 ^ v355 ^ 0x54A80618) != 0x489AC581:
        return False

    # Check 3: v477 XOR v474 XOR 0x35059FC5 == 0x6582138E
    if u32(v477 ^ v474 ^ 0x35059FC5) != 0x6582138E:
        return False

    # Check 4: ~(...) == v282
    x161 = u32(v161 ^ 0x698B93C2)
    x355 = u32(v355 ^ 0x54A80618)
    x474 = u32(v474 ^ 0x35059FC5)
    calc_v282 = u32(~u32(
        u32(u32(umulhi(0xF0F0F0F1, x161) >> 4) * x355) +
        u32(u32(umulhi(0x4EC4EC4F, x161) >> 2) * x474) +
        u32(x355 * x474)
    ))
    if calc_v282 != v282:
        return False

    # Check 5: ~(...) == v353
    calc_v353 = u32(~u32(
        u32(x161 -
        u32(umulhi(0xAAAAAAAB, u32(x161 * x474)) >> 1) +
        x355)
    ))
    if calc_v353 != v353:
        return False

    return True

def keygen(name):
    """
    Generate a valid serial. 'name' is not used by the crackme algorithm.
    Randomly picks v161, v474, v355 and derives all other values.
    """
    mask28 = 0x6487169F
    mask16 = 0x20890481
    mask35 = 0x5B7A027F
    mask47 = 0x11258023

    # Pick random free variables
    v161 = random.getrandbits(32)
    v474 = random.getrandbits(32)
    v355 = random.getrandbits(32)

    # Derive dependent variables from the 5 checks
    # Check 1: v288 = 0x48A86FC4 ^ 0x35059FC5 ^ v474
    v288 = u32(0x48A86FC4 ^ 0x35059FC5 ^ v474)

    # Check 2: v166 = 0x489AC581 ^ 0x54A80618 ^ v355
    v166 = u32(0x489AC581 ^ 0x54A80618 ^ v355)

    # Check 3: v477 = 0x6582138E ^ 0x35059FC5 ^ v474
    v477 = u32(0x6582138E ^ 0x35059FC5 ^ v474)

    x161 = u32(v161 ^ 0x698B93C2)
    x355 = u32(v355 ^ 0x54A80618)
    x474 = u32(v474 ^ 0x35059FC5)

    # Check 4: v282
    v282 = u32(~u32(
        u32(u32(umulhi(0xF0F0F0F1, x161) >> 4) * x355) +
        u32(u32(umulhi(0x4EC4EC4F, x161) >> 2) * x474) +
        u32(x355 * x474)
    ))

    # Check 5: v353
    v353 = u32(~u32(
        u32(x161 -
        u32(umulhi(0xAAAAAAAB, u32(x161 * x474)) >> 1) +
        x355)
    ))

    # Compose serial parts s[1..8]
    s1 = u32(((v161 ^ v166) & mask16) ^ v161)
    s6 = u32(((v161 ^ v166) & mask16) ^ v166)
    s2 = u32(((v282 ^ v288) & mask28) ^ v282)
    s8 = u32(((v282 ^ v288) & mask28) ^ v288)
    s3 = u32(((v353 ^ v355) & mask35) ^ v353)
    s5 = u32(((v353 ^ v355) & mask35) ^ v355)
    s4 = u32(((v474 ^ v477) & mask47) ^ v474)
    s7 = u32(((v474 ^ v477) & mask47) ^ v477)

    serial = '%08X%08X%08X%08X%08X%08X%08X%08X' % (s1, s2, s3, s4, s5, s6, s7, s8)
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
