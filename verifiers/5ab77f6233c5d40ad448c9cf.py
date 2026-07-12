import ctypes

def _to_int32(v):
    """Simulate 32-bit signed integer overflow."""
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def _to_uint32(v):
    return v & 0xFFFFFFFF


def keygen(name: str) -> str:
    """Generate a valid serial for the given username."""
    # Username must be longer than 4 characters
    if len(name) < 5:
        raise ValueError("Username must be longer than 4 characters")

    # Truncate to 50 characters (as in original)
    user = list(name[:50])

    # Initial register values
    ebp = 0x32
    esi = 0x18

    # ---- Loop1 ----
    def loop1(user, esi):
        ebx = 0x400
        length = len(user)
        var_164 = 0
        i = 0
        while i < length:
            eax = _to_int32(ord(user[i]) + 0x56b)
            esi = _to_int32(esi + (eax ^ 0x890428))
            edx = _to_int32((ord(user[3]) + length) ^ 0x209)
            if length <= 9:
                edx = _to_int32(edx * esi)
                ebx = _to_int32(ebx + edx)
            else:
                edx = _to_int32(edx * ebx)
                esi = _to_int32(esi + edx)
            # edx = (eax << 7) + eax
            edx = _to_int32((eax << 7) + eax)
            # edx = ebx + (eax + edx*8)*4
            edx = _to_int32(ebx + _to_int32((_to_int32(eax + _to_int32(edx * 8))) * 4))
            var_164 = edx
            ebx = edx
            i += 1
        return var_164, esi

    var_164, esi = loop1(user, esi)

    # ---- Loop2 ----
    # Loop2 uses strrev(user) internally; we must track the reversals
    def loop2(user, ebp):
        edi = 5
        while edi > 0:
            eax = ord(user[edi])
            ebp = _to_int32(ebp + 0x134a + eax)
            user = user[::-1]  # strrev
            edi -= 1
        return ebp, user

    ebp, user = loop2(user, ebp)

    # ---- Loop3 ----
    # Loop3: j goes 1..5 (5 iterations), also calls strrev(user)
    def loop3(user, ebp, esi):
        j = 1
        i = 5
        while i > 0:
            eax = _to_int32(ord(user[j]) + 0x23)
            ebp = _to_int32(ord(user[0]) + ebp + 0x134a)
            ecx = _to_int32(eax + eax * 2)       # ecx = eax * 3
            ecx = _to_int32(ecx + ecx * 4)       # ecx = ecx * 5 => eax*15
            edx = _to_int32(ecx + ecx * 4)       # edx = ecx * 5 => eax*75
            eax = _to_int32(eax + edx * 4)       # eax = eax + edx*4 => eax + eax*300 = eax*301
            esi = _to_int32(esi + eax * 2)
            user = user[::-1]  # strrev
            j += 1
            i -= 1
        return ebp, esi, user

    ebp, esi, user = loop3(user, ebp, esi)

    # ---- Key computation ----
    # Note: user[5] and user[2] refer to the CURRENT state of user after all reversals
    k2 = _to_int32((0x18 - ord(user[5])) ^ (ebp + var_164))
    k1 = _to_int32((0x1337 - ord(user[2])) ^ (esi + 0x3c))

    return f"LNT-{k1}-{k2}"


def verify(name: str, serial: str) -> bool:
    """Verify that serial matches the generated key for name."""
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
