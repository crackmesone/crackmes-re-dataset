import ctypes

def _to_u32(v):
    """Truncate to unsigned 32-bit integer (simulate x86 register overflow)."""
    return v & 0xFFFFFFFF

def _to_s32(v):
    """Interpret unsigned 32-bit as signed 32-bit."""
    v = _to_u32(v)
    if v >= 0x80000000:
        return v - 0x100000000
    return v


def _calculate_serial(name: str) -> int:
    """
    Reconstruct the serial calculation algorithm from the assembly in Solution 3 (BadSector keygen).
    The algorithm has 4 passes over the name, each with a div step in between (the remainder after
    div is carried forward into the next pass as the starting accumulator value 'edx').
    """
    name_len = len(name)

    # ---- Pass 1 (loop at j_00401104) ----
    # ebp-4 starts at 0
    # For each char:
    #   ebp-4 += char_val
    #   if char >= 0x4A: eax = char_val * ebp-4
    #   else:            eax = char_val * ebp-4, then eax <<= 1
    #   ebp-4 = eax
    var4 = 0
    for i in range(name_len):
        cl = ord(name[i])
        eax = _to_s32(cl)
        var4 = _to_u32(var4 + eax)
        eax = _to_u32(eax)
        if cl >= 0x4A:
            eax = _to_u32(eax * var4)
        else:
            eax = _to_u32(eax * var4)
            eax = _to_u32(eax << 1)
        var4 = eax

    # ---- div 0x724, remainder goes to edx for pass 2 ----
    eax_val = var4
    edx = eax_val % 0x724  # we use the remainder
    # eax (quotient) is discarded; edx is the accumulator for next pass

    # ---- Pass 2 (loop at j_00401139) ----
    # edx starts from remainder above
    # For each char:
    #   edx += char_val
    #   if char >= 0x40: ecx = char_val * edx; edx = ecx
    #   else:            ecx = char_val * edx; edx = ecx << 2
    for i in range(name_len):
        bl = ord(name[i])
        ecx = _to_s32(bl)
        edx = _to_u32(edx + ecx)
        ecx = _to_u32(ecx)
        if bl >= 0x40:
            ecx = _to_u32(ecx * edx)
            edx = ecx
        else:
            ecx = _to_u32(ecx * edx)
            edx = _to_u32(ecx << 2)

    # ---- div 0x2225, remainder goes to edx for pass 3 ----
    eax_val = edx
    edx = eax_val % 0x2225

    # ---- Pass 3 (loop at j_0040116C) ----
    # edx starts from remainder above
    # For each char:
    #   edx += char_val
    #   if char >= 0x54: ecx = char_val * edx; edx = ecx
    #   else:            ecx = char_val * edx; edx = ecx + 2*ecx (= 3*ecx), then edx <<= 1  => edx = 6*ecx
    for i in range(name_len):
        al = ord(name[i])
        ecx = _to_s32(al)
        edx = _to_u32(edx + ecx)
        ecx = _to_u32(ecx)
        if al >= 0x54:
            ecx = _to_u32(ecx * edx)
            edx = ecx
        else:
            ecx = _to_u32(ecx * edx)
            # lea edx, [ecx + 2*ecx] => edx = 3*ecx
            edx_temp = _to_u32(ecx + 2 * ecx)
            # shl edx, 1 => edx = 6*ecx
            edx = _to_u32(edx_temp << 1)

    # ---- Pass 4 (loop at j_00401193) ----
    # edx carries over from pass 3
    # For each char:
    #   edx += char_val
    #   if char >= 0x4A: ecx = char_val * edx; edx = ecx
    #   else:            ecx = char_val * edx; edx = ecx + 4*ecx = 5*ecx
    for i in range(name_len):
        al = ord(name[i])
        ecx = _to_s32(al)
        edx = _to_u32(edx + ecx)
        ecx = _to_u32(ecx)
        if al >= 0x4A:
            ecx = _to_u32(ecx * edx)
            edx = ecx
        else:
            ecx = _to_u32(ecx * edx)
            # lea edx, [ecx + 4*ecx] = 5*ecx
            edx = _to_u32(ecx + 4 * ecx)

    # ---- div 0x2E34, remainder goes to edx for pass 5 ----
    eax_val = edx
    edx = eax_val % 0x2E34

    # ---- Pass 5 (loop at j_004011C3) ----
    # edx starts from remainder above
    # For each char:
    #   edx += char_val
    #   if char >= 0x40: eax = char_val * edx
    #   else:            eax = char_val * edx * 7
    #   edx = eax
    for i in range(name_len):
        cl = ord(name[i])
        eax = _to_s32(cl)
        edx = _to_u32(edx + eax)
        eax = _to_u32(eax)
        if cl >= 0x40:
            eax = _to_u32(eax * edx)
        else:
            eax = _to_u32(eax * edx)
            eax = _to_u32(eax * 7)
        edx = eax

    return _to_u32(edx)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Serial is formatted as "%X%lu" with the final edx value pushed twice.
    That means: hex representation (uppercase) of the value, followed by decimal representation.
    Both arguments to wsprintf are the same value (pushed twice as per the assembly).
    """
    if len(name) < 4:
        raise ValueError("Name must be more than 3 chars")
    val = _calculate_serial(name)
    # wsprintf format "%X%lu": first arg is hex (no '0x'), second is decimal
    serial = "%X%d" % (val, val)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    The crackme computes the expected serial from name and compares character-by-character.
    """
    if len(name) <= 3:
        return False
    if len(serial) <= 3:
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
