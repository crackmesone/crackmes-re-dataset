import ctypes

def _u32(x):
    """Truncate to unsigned 32-bit integer (simulating x86 EAX behavior)."""
    return x & 0xFFFFFFFF

def _compute(ser):
    """
    Compute res from a 13-character serial string (indices 0..12).
    ser is a list/string of characters; we use ord() values.
    This mirrors the assembly in brute.cpp exactly.
    All arithmetic is unsigned 32-bit (mul uses eax*ecx truncated to 32 bits).
    """
    b = [ord(c) for c in ser]  # byte values at positions 0..12

    # --- Block 1: compute dword_4039B0 ---
    eax = b[1]
    ecx = b[10]
    eax = _u32(eax + ecx)
    ecx = b[6]
    eax = _u32(eax + ecx)
    dword_4039B0 = eax

    # --- Block 2: compute dword_4039B4 ---
    eax = b[2]
    ecx = b[9]
    eax = _u32(eax * ecx)
    ecx = b[8]
    eax = _u32(eax * ecx)
    ecx = b[4]
    eax = _u32(eax - ecx)
    dword_4039B4 = eax

    # --- Block 3: compute unk_4039C8 ---
    eax = b[3]
    ecx = b[5]
    eax = _u32(eax + ecx)
    ecx = b[7]
    eax = _u32(eax - ecx)
    ecx = b[12]
    eax = _u32(eax * ecx)
    ecx = dword_4039B4
    eax = _u32(eax * ecx)
    ecx = b[11]
    eax = _u32(eax + ecx)
    ecx = b[0]
    eax = _u32(eax - ecx)
    ecx = dword_4039B0
    eax = _u32(eax * ecx)
    ecx = b[2]
    eax = _u32(eax + ecx)
    ecx = b[12]
    eax = _u32(eax + ecx)
    ecx = b[8]
    eax = _u32(eax + ecx)
    unk_4039C8 = eax

    # --- Block 4: recompute dword_4039B0 ---
    eax = b[0]
    ecx = b[1]
    eax = _u32(eax * ecx)
    ecx = b[2]
    eax = _u32(eax * ecx)
    ecx = b[12]
    eax = _u32(eax - ecx)
    dword_4039B0 = eax

    # --- Block 5: compute dword_4039B8 ---
    eax = b[3]
    ecx = b[3]
    eax = _u32(eax * ecx)
    dword_4039B8 = eax

    # --- Block 6: recompute dword_4039B4 ---
    eax = b[11]
    ecx = b[12]
    eax = _u32(eax * ecx)
    ecx = dword_4039B8
    eax = _u32(eax + ecx)
    dword_4039B4 = eax

    # --- Block 7: compute temp, then update dword_4039B4 ---
    eax = b[4]
    ecx = b[6]
    eax = _u32(eax * ecx)
    ecx = b[9]
    eax = _u32(eax + ecx)
    ecx = b[10]
    eax = _u32(eax + ecx)
    ecx = eax  # save as temp
    eax = dword_4039B4
    eax = _u32(eax - ecx)
    dword_4039B4 = eax

    # --- Block 8: recompute dword_4039B0 ---
    eax = dword_4039B0
    ecx = dword_4039B4
    eax = _u32(eax + ecx)
    ecx = b[12]
    eax = _u32(eax + ecx)
    dword_4039B0 = eax

    # --- Block 9: recompute dword_4039B4 ---
    eax = b[12]
    ecx = b[12]
    eax = _u32(eax + ecx)
    ecx = b[8]
    eax = _u32(eax + ecx)
    dword_4039B4 = eax

    # --- Block 10: compute dword_4039C0 ---
    eax = dword_4039B0
    ecx = dword_4039B4
    eax = _u32(eax - ecx)
    dword_4039C0 = eax

    # --- Block 11: sum of all 13 bytes * b[12] + dword_4039C0 ---
    eax = b[0]
    for i in range(1, 13):
        ecx = b[i]
        eax = _u32(eax + ecx)
    ecx = b[12]
    eax = _u32(eax * ecx)
    ecx = dword_4039C0
    eax = _u32(eax + ecx)
    dword_4039C0 = eax

    # --- Block 12: recompute dword_4039B0 ---
    eax = b[0]
    ecx = b[12]
    eax = _u32(eax + ecx)
    dword_4039B0 = eax

    # --- Block 13: recompute dword_4039B4 ---
    eax = b[0]
    ecx = b[1]
    eax = _u32(eax * ecx)
    ecx = b[12]
    eax = _u32(eax * ecx)
    ecx = b[3]
    eax = _u32(eax * ecx)
    ecx = dword_4039B0
    eax = _u32(eax + ecx)
    dword_4039B4 = eax

    # --- Block 14: compute (b[12] - b[0]) as ecx, then mul dword_4039B4, add dword_4039C0 ---
    eax_tmp = b[12]
    ecx_tmp = b[0]
    eax_tmp = _u32(eax_tmp - ecx_tmp)
    ecx = eax_tmp
    eax = dword_4039B4
    eax = _u32(eax * ecx)
    ecx = dword_4039C0
    eax = _u32(eax + ecx)
    dword_4039C0 = eax

    # --- Division: res = unk_4039C8 / dword_4039C0 ---
    # Fix to prevent div by zero (from the source)
    if dword_4039C0 == 0:
        # From the asm: movzx eax, byte ptr [ebx+0ch]; inc eax
        res = _u32(b[12] + 1)
    else:
        res = _u32(unk_4039C8 // dword_4039C0)  # unsigned integer division

    return res


def verify(name, serial):
    """
    The crackme only checks a 13-character serial of digits '0'-'9'.
    The name is NOT used in the algorithm (no name-based check found).
    The check is: _compute(serial[0:13]) == ord(serial[12])
    i.e., the computed 'res' must equal the ASCII value of the last serial character.
    """
    # ASSUMPTION: name is not used in serial validation (not mentioned in writeup)
    if len(serial) < 13:
        return False
    s = serial[:13]
    # Serial must consist of digit characters ('0'..'9')
    if not all('0' <= c <= '9' for c in s):
        return False
    res = _compute(s)
    # Check: res == ord(s[12])  (the value equals the ASCII of the last digit)
    return res == ord(s[12])


def keygen(name):
    """
    Brute-force keygen: iterate over all 13-digit serials (digits '0'-'9'),
    try each candidate where last digit matches res.
    We fix the first 12 digits and compute what last digit must be,
    then check if res == ord(that digit).
    ASSUMPTION: name is not used.
    """
    # ASSUMPTION: name is not used in serial validation
    # For efficiency: fix 12 digits, then for each candidate last digit d,
    # compute res and check res == ord(d).
    # Since we have 10^12 combinations, we just yield valid ones found quickly.
    # For demonstration, we'll do a smarter search:
    # fix digits 0..11, try all 10 values for digit 12, check validity.
    from itertools import product

    digits = '0123456789'
    # For a quick result, try a reduced search (first few combos):
    for prefix in product(digits, repeat=12):
        s12 = list(prefix)
        for d in digits:
            candidate = list(prefix) + [d]
            res = _compute(candidate)
            if res == ord(d):
                yield ''.join(candidate)
                return  # yield first found and stop
    return None



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
