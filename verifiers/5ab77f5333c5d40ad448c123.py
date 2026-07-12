import ctypes

def _to_u32(v):
    return v & 0xFFFFFFFF

def _compute_serial(name: str) -> int:
    """
    Implements the serial computation loop from the crackme assembly:

    xor edx, edx
    xor eax, eax
    xor ecx, ecx
    loop:
        movsx eax, byte [esi]       ; eax = signed char
        mov ebx, eax
        sub esi, edx               ; esi pointer adjustment (edx=0 always, no-op effectively)
        shl eax, 0x0e              ; eax <<= 14
        shr ebx, 0x0d              ; ebx >>= 13 (logical, since ebx=eax originally)
        xor eax, ebx
        add eax, 0x54622262
        xor eax, ecx
        add ecx, eax
        inc esi
        if byte[esi] != 0: goto loop

    Then after loop:
        mov eax, 0x087A9236
        sub eax, ecx               ; eax = 0x087A9236 - ecx
        imul eax, eax              ; eax = eax * eax  (but this is squared)
        ; NOTE from solution 2 (kg.asm) the keygen does NOT include the post-loop steps
        ; Solution 2 keygen stops at ecx after the loop and uses that directly as the code.
        ; Solution 1 (OllyDbg trace) shows:
        ;   mov eax, 87A9236
        ;   sub eax, ecx
        ;   imul eax, eax
        ;   xor eax, eax   <- this zeroes eax!
        ;   add ecx, eax   <- ecx += 0, no change
        ;   cmp ecx, ebx   <- compare ecx (computed) with ebx (entered)
        ; So the xor eax,eax effectively nullifies the imul result, and ecx stays as-is.
        ; The final serial == ecx from the loop.
    """
    # All arithmetic is 32-bit unsigned (wrap at 2^32)
    ecx = 0
    edx = 0  # edx is always 0 in the loop (sub esi, edx is a no-op)

    name_bytes = name.encode('latin-1') if isinstance(name, str) else name

    for i, byte_val in enumerate(name_bytes):
        # movsx eax, byte: sign-extend
        eax = ctypes.c_int32(ctypes.c_int8(byte_val).value).value
        ebx = eax

        # shl eax, 0x0e  (32-bit)
        eax = _to_u32(eax << 0x0e)

        # shr ebx, 0x0d  (logical shift right on the original signed value treated as 32-bit)
        ebx_u32 = _to_u32(ebx)
        ebx = ebx_u32 >> 0x0d

        # xor eax, ebx
        eax = _to_u32(eax ^ ebx)

        # add eax, 0x54622262
        eax = _to_u32(eax + 0x54622262)

        # xor eax, ecx
        eax = _to_u32(eax ^ ecx)

        # add ecx, eax
        ecx = _to_u32(ecx + eax)

    # Post-loop (from solution 1 disassembly):
    # mov eax, 0x087A9236
    # sub eax, ecx
    # imul eax, eax
    # xor eax, eax   <- zeroes eax, so the imul result is discarded!
    # add ecx, eax   <- ecx += 0
    # The final comparison is CMP ECX, EBX where EBX is the entered serial.
    # So serial = ecx (unsigned 32-bit)

    # ASSUMPTION: The post-loop steps net to zero change on ecx because
    # xor eax,eax zeroes eax before add ecx,eax, confirmed by solution 2 keygen
    # which outputs ecx directly without any post-loop modification.

    return ecx


def verify(name: str, serial) -> bool:
    """
    Verify a name/serial pair.
    serial can be an int or a string representation of an unsigned decimal int.
    """
    if not name:
        return False
    try:
        serial_int = int(serial)
    except (ValueError, TypeError):
        return False

    expected = _compute_serial(name)
    # The crackme uses GetDlgItemInt which returns unsigned 32-bit,
    # and compares ecx (unsigned 32-bit) == ebx (the entered int)
    return _to_u32(serial_int) == expected


def keygen(name: str) -> str:
    """
    Generate the serial (as a decimal string) for the given name.
    """
    if not name:
        raise ValueError('Name must not be empty')
    return str(_compute_serial(name))



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
