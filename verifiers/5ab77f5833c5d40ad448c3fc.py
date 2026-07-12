import ctypes

def _hash1(name_bytes):
    """CRC-like hash for s1/s2 computation"""
    ecx = 0
    if name_bytes:
        ecx = ctypes.c_uint32(int.from_bytes(name_bytes[:4].ljust(4, b'\x00'), 'little')).value
    for i in range(min(0x1d, len(name_bytes))):
        b = name_bytes[i]
        eax = ctypes.c_int32(b).value
        edx = eax
        eax = ctypes.c_uint32(eax << 0x18).value
        for _ in range(8):
            eax = ctypes.c_uint32(eax + eax).value
            if ctypes.c_int32(eax).value < 0:
                eax = ctypes.c_uint32(eax ^ 0xDB8173E4).value
        eax = ctypes.c_uint32(eax - ctypes.c_uint32(edx).value).value
        ecx = ctypes.c_uint32(ecx ^ eax).value
        # rotate left 5
        eax2 = ctypes.c_uint32(ecx >> 0x1B).value
        ecx = ctypes.c_uint32((ecx << 0x5) | eax2).value
    return ecx


def _hash3(name_bytes):
    """CRC-like hash for s3 computation"""
    edx = 0
    if name_bytes:
        edx = ctypes.c_uint32(int.from_bytes(name_bytes[:4].ljust(4, b'\x00'), 'little')).value
    for i in range(min(0x1d, len(name_bytes))):
        b = name_bytes[i]
        eax = ctypes.c_int32(b).value
        ecx = ctypes.c_uint32(eax << 0x18).value
        for _ in range(8):
            ecx = ctypes.c_uint32(ecx + ecx).value
            if ctypes.c_int32(ecx).value < 0:
                ecx = ctypes.c_uint32(ecx ^ 0x69A5F02C).value
        eax = ctypes.c_uint32(eax ^ ecx).value
        edx = ctypes.c_uint32(edx ^ eax).value
        # rotate left 3
        eax2 = ctypes.c_uint32(edx >> 0x1D).value
        ecx2 = ctypes.c_uint32(edx << 3).value
        edx = ctypes.c_uint32(eax2 | ecx2).value
    return edx


def _encode_val(val, multipliers):
    """Encode an integer into a 5-char string using the multiplier table."""
    result = []
    for m in multipliers:
        if m == 0:
            result.append(chr(0x21))
            continue
        q = val // m
        if q != 0:
            result.append(chr(q + 0x21))
            val = val % m
        else:
            result.append(chr(0x21))
    return ''.join(result)


# Multiplier tables from the keygen source
p1 = [0x31C84B1, 0x95EED, 0x1C39, 0x55, 0x1]
p2 = [0x4452100, 0xBE1C0, 0x2110, 0x5C, 0x1]
p3 = [0x4A75410, 0xCAC78, 0x2284, 0x5E, 0x1]
p4 = [0x3E92110, 0xB1FA8, 0x1FA4, 0x5A, 0x1]
p5 = [0x36A2C21, 0xA0C47, 0x1D91, 0x57, 0x1]


def _lcg_step(val):
    val = ctypes.c_uint32(val).value
    val = ctypes.c_uint32(val * 0x343FD + 0x269EC3).value
    return val


def _compute_s4_val(ok1, ok3):
    """Reproduce the inline asm for s4 seed."""
    ok1 = ctypes.c_int32(ok1).value
    ok3 = ctypes.c_int32(ok3).value
    esi = ctypes.c_uint32(ok1 ^ ok3).value
    esi = ctypes.c_uint32(ctypes.c_int32(esi).value - ok1).value
    esi = ctypes.c_uint32(ctypes.c_int32(esi).value - ok3).value
    # rotate esi by (0x1f - (0x1f % 32)) ... simplified: rol by computed shift
    # shift = 0x1f, remainder = 0x1f % 32 = 0x1f, so rotate by (0x1f - edx) where edx=esi%0x1f
    shift_total = 0x1f
    divisor = ctypes.c_uint32(shift_total).value
    esi_u = ctypes.c_uint32(esi).value
    if divisor == 0:
        edx = 0
    else:
        edx = esi_u % divisor
    rotate_by = shift_total - edx
    rotate_by = rotate_by % 32
    esi_rotated = ctypes.c_uint32((esi_u >> rotate_by) | (esi_u << (32 - rotate_by))).value
    val = _lcg_step(esi_rotated)
    rval = ctypes.c_int32(val).value >> 0x10
    rval &= 0x7fff
    # determine loop count
    loop_count = rval % 0xffff  # # ASSUMPTION: edx from idiv is loop count
    cur_esi = esi_rotated
    for _ in range(loop_count):
        val = _lcg_step(val)
        r1 = (ctypes.c_int32(val).value >> 0x10) & 0x7fff
        ecx = ctypes.c_uint32(r1 * ctypes.c_int32(cur_esi).value).value
        val = _lcg_step(val)
        r2 = (ctypes.c_int32(val).value >> 0x10) & 0x7fff
        ecx = ctypes.c_uint32(ctypes.c_int32(ecx).value + r2).value
        cur_esi = ecx
    return ctypes.c_uint32(cur_esi).value


def keygen(name):
    """Generate serials for a given name."""
    name_bytes = name.encode('ascii', errors='replace')

    val1 = _hash1(name_bytes)
    vect1 = [0x0 ^ val1, 0x10000 ^ val1]

    val3 = _hash3(name_bytes)
    vect3_base = [0x0, 0x1, 0x4000000, 0x4000001]

    serials = []
    for c1 in range(2):
        s1_str = _encode_val(vect1[c1], p1)

        vect3 = [v ^ val3 for v in vect3_base]

        for c3 in range(4):
            s3_str = _encode_val(vect3[c3], p3)

            ok1 = vect1[c1]
            ok3 = vect3[c3]
            s4_seed = _compute_s4_val(ok1, ok3)
            vect4 = [0x0 ^ s4_seed, 0x10 ^ s4_seed]

            for c4 in range(2):
                s4_str = _encode_val(vect4[c4], p4)

                # s2 and s5 computations are truncated in the writeup
                # ASSUMPTION: s2 uses vect2 = [0x0, 0x80000000] XOR some combined hash of ok1,ok3,ok4
                # ASSUMPTION: s5 uses vect5 derived from all previous values
                # We only output what we can fully reconstruct
                serials.append({
                    's1': s1_str,
                    's3': s3_str,
                    's4': s4_str,
                    'note': 's2 and s5 truncated in writeup'
                })

    return serials


def verify(name, serial):
    """Attempt to verify a serial. Only partial check possible due to truncated writeup."""
    # ASSUMPTION: Serial format is unknown as writeup was truncated.
    # We can only partially reconstruct the algorithm.
    parts = serial.split('-')
    if len(parts) < 3:
        return False

    name_bytes = name.encode('ascii', errors='replace')
    val1 = _hash1(name_bytes)
    vect1 = [0x0 ^ val1, 0x10000 ^ val1]

    val3 = _hash3(name_bytes)
    vect3_base = [0x0, 0x1, 0x4000000, 0x4000001]

    # Try all combinations
    for c1 in range(2):
        s1_candidate = _encode_val(vect1[c1], p1)
        vect3 = [v ^ val3 for v in vect3_base]
        for c3 in range(4):
            s3_candidate = _encode_val(vect3[c3], p3)
            ok1 = vect1[c1]
            ok3 = vect3[c3]
            s4_seed = _compute_s4_val(ok1, ok3)
            vect4 = [0x0 ^ s4_seed, 0x10 ^ s4_seed]
            for c4 in range(2):
                s4_candidate = _encode_val(vect4[c4], p4)
                if (len(parts) >= 1 and parts[0] == s1_candidate and
                    len(parts) >= 2 and parts[1] == s3_candidate and
                    len(parts) >= 3 and parts[2] == s4_candidate):
                    return True  # partial match, s2/s5 not verifiable
    return False



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
