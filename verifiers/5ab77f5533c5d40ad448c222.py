import math

def _hash_name(name: str) -> int:
    """
    Replicates the 16-bit hash loop at 0x401220.
    All arithmetic is done in 16-bit (mod 65536) to match the x86 word-size ops.
    """
    name_bytes = name.encode('latin-1', errors='replace')
    length = len(name_bytes)

    ax = 0
    dx = 0

    for i in range(length):
        ch = name_bytes[i] & 0xFF
        # movzx ax, byte ptr [esi]
        ax = ch
        # add dx, ax
        dx = (dx + ax) & 0xFFFF
        # add dx, dx
        dx = (dx + dx) & 0xFFFF
        # mul dx  (ax = ax * dx, 16-bit result in ax)
        ax = (ax * dx) & 0xFFFF
        # sub dx, ax
        dx = (dx - ax) & 0xFFFF
        # add dx, dx
        dx = (dx + dx) & 0xFFFF
        # add dx, ax
        dx = (dx + ax) & 0xFFFF
        # imul dx, ax
        dx = (dx * ax) & 0xFFFF

    # movzx ecx, dx
    ecx = dx & 0xFFFF

    ax = 0
    dx = 0
    eax = ecx
    # imul eax, ecx
    eax = (eax * ecx) & 0xFFFFFFFF
    # and ecx, eax
    ecx = (ecx & eax) & 0xFFFFFFFF
    # or eax, ecx
    eax = (eax | ecx) & 0xFFFFFFFF
    # xor eax, ecx
    eax = (eax ^ ecx) & 0xFFFFFFFF
    # xor ecx, ecx
    ecx = 0
    # mov ecx, eax
    ecx = eax
    # xor eax, eax
    eax = 0
    # return ecx
    return ecx


def _power_call(val: int, exp: int) -> int:
    """
    Replicates 0x401278: raises val to the power exp by repeated multiplication.
    The loop runs (exp-1) times (dec eax / cmp eax,1 / jnz).
    All in 32-bit.
    """
    val = val & 0xFFFFFFFF
    esi = val
    edi = val
    eax = exp
    # loop: imul esi,edi; dec eax; cmp eax,1; jnz
    while True:
        esi = (esi * edi) & 0xFFFFFFFF
        eax -= 1
        if eax == 1:
            break
    return esi


def _compute_magic(name: str) -> int:
    """
    Full magic-number derivation matching the crackme's validation logic.
    Returns R (the magic number the serial parts must satisfy).
    """
    # Step 1: hash name
    ecx = _hash_name(name)

    # Step 2: ecx^2 via power call
    esi = _power_call(ecx, 2)

    # Step 3: post-power ops (from 0x401119)
    # xor ecx, eax  (ecx=ecx from hash, eax=esi from power call)
    # but at this point the original ecx from hash was in ecx, eax=esi result
    # Looking at Delphi keygen inline asm more carefully:
    # After power call returns in eax:
    #   xor ecx, eax  -> ecx = ecx_hash XOR esi_power
    #   and eax, ecx  -> eax = esi_power AND (ecx_hash XOR esi_power)
    #   xor ecx, ecx  -> ecx = 0
    #   shl eax, 2
    #   mov edi, eax
    # Then lstrlen(name) -> ecx
    #   mov eax, edi
    #   cdq
    #   idiv ecx   -> eax=quotient, edx=remainder
    #   sub edi, eax  -> edi = edi - quotient
    #   add edi, edx  -> edi = edi + remainder   (== edi % len)
    #   shr edi, 0x16  -> edi >>= 22
    #   R = edi

    ecx_hash = ecx
    eax_power = esi

    # xor ecx, eax
    ecx_xor = (ecx_hash ^ eax_power) & 0xFFFFFFFF
    # and eax, ecx
    eax_and = (eax_power & ecx_xor) & 0xFFFFFFFF
    # xor ecx, ecx -> 0
    # shl eax, 2
    eax_shl = (eax_and << 2) & 0xFFFFFFFF
    edi = eax_shl

    name_len = len(name.encode('latin-1', errors='replace'))
    if name_len == 0:
        return 0

    # signed 32-bit division
    def to_signed32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    eax_s = to_signed32(edi)
    # cdq
    edx_s = -1 if eax_s < 0 else 0
    # idiv ecx (ecx = name_len, positive)
    # dividend = (edx:eax) as 64-bit signed
    dividend = (edx_s << 32) | (edi & 0xFFFFFFFF)
    quotient = int(eax_s / name_len)  # truncate toward zero
    remainder = eax_s - quotient * name_len

    edi = (edi - (quotient & 0xFFFFFFFF)) & 0xFFFFFFFF
    edi = (edi + (remainder & 0xFFFFFFFF)) & 0xFFFFFFFF
    # shr edi, 22 (0x16)
    edi = (edi >> 22) & 0xFFFFFFFF
    return edi


def _verify_serial_parts(a: int, b: int, c: int, d: int, R: int) -> bool:
    """
    The serial check: a^2 + b^2 + c^2 + d^2 == R
    Each part is parsed from the serial string via StrToIntA and then squared.
    """
    return (a * a + b * b + c * c + d * d) == R


def verify(name: str, serial: str) -> bool:
    """
    Verify name + serial (format 'A-B-C-D') against the crackme.
    """
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    try:
        a, b, c, d = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        return False

    R = _compute_magic(name)
    return _verify_serial_parts(a, b, c, d, R)


def keygen(name: str):
    """
    Generate all valid serials for the given name.
    Yields strings of the form 'A-B-C-D' where A^2+B^2+C^2+D^2 == R.
    """
    R = _compute_magic(name)
    if R < 0:
        return
    L = int(math.isqrt(R)) + 1
    for a in range(0, L + 1):
        if a * a > R:
            break
        for b in range(0, L + 1):
            if a * a + b * b > R:
                break
            for c in range(0, L + 1):
                rem = R - a * a - b * b - c * c
                if rem < 0:
                    break
                d_sq = math.isqrt(rem)
                if d_sq * d_sq == rem:
                    yield f"{a}-{b}-{c}-{d_sq}"



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
