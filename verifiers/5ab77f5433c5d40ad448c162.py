import ctypes

def generate_serial(username: str) -> str:
    """
    Reimplements the x86 assembly key generation loop from the keygen.cpp.
    Uses 32-bit unsigned arithmetic (ctypes.c_uint32) to match the original.
    
    Assembly logic (simplified):
      eax = 0 (loop index / counter)
      edx = 0 (accumulator)
      edi = 0 (magic offset, 0 when not debugging; would be 0x3025 under debugger)
      esi = pointer to username
      cl  = username[0]

    loop:
      ecx = sign-extend(cl)
      ebx = ecx ^ 0xC0C0C0C0
      ebx = ebx - edi + edx
      ebx = ebx * eax
      ebx = ebx << 1          (shl ebx, 1)
      edx = ebx
      ebx = ecx + ecx*4       (lea: ecx*5)
      edx = edx ^ ebx
      # compute shift amount: ecx & 0x8000001F, with sign adjustment
      shift = ecx & 0x8000001F
      if shift < 0 (i.e. bit31 set):
          shift = ((shift - 1) | 0xFFFFFFE0) + 1
      edx = edx << shift
      cl = username[eax + 1]
      edx = edx ^ 0xBADDC001
      eax += 1
      if cl != 0: goto loop
    
    result = edx formatted as 8 uppercase hex digits
    """
    username_bytes = username.encode('latin-1') + b'\x00'

    eax = 0
    edx = ctypes.c_int32(0).value
    edi = 0  # 0 when not debugging; ASSUMPTION: always 0 in normal use

    cl = username_bytes[0]

    while True:
        # movsx ecx, cl  (sign-extend byte to 32-bit)
        ecx = ctypes.c_int8(cl).value  # sign-extend

        ebx = ctypes.c_int32(ecx).value
        ebx = ctypes.c_int32(ebx ^ ctypes.c_int32(0xC0C0C0C0).value).value
        ebx = ctypes.c_int32(ebx - edi + edx).value
        ebx = ctypes.c_int32(ebx * eax).value
        # shl ebx, 1
        ebx = ctypes.c_int32(ebx << 1).value
        edx = ebx
        # lea ebx, [ecx + ecx*4]  => ebx = ecx * 5
        ebx = ctypes.c_int32(ecx * 5).value
        edx = ctypes.c_int32(edx ^ ebx).value

        # and ecx, 0x8000001F
        shift_val = ecx & 0x8000001F
        # jns positive: if sign bit set, adjust
        # treat shift_val as signed 32-bit for the sign check
        shift_signed = ctypes.c_int32(shift_val).value
        if shift_signed < 0:
            # dec ecx; or ecx, 0xFFFFFFE0; inc ecx
            shift_val = ctypes.c_int32(shift_val - 1).value
            shift_val = ctypes.c_int32(shift_val | ctypes.c_int32(0xFFFFFFE0).value).value
            shift_val = ctypes.c_int32(shift_val + 1).value
        # The shift amount is the low 5 bits effectively (x86 masks shift by 31 for 32-bit)
        # But we use the computed ecx value as shift count
        # shift is: shl edx, cl (where cl = shift_val & 0xFF, and x86 uses mod 32)
        shift_amount = (shift_val & 0xFF) % 32
        # shl edx, cl
        edx_u = ctypes.c_uint32(edx).value
        edx_u = (edx_u << shift_amount) & 0xFFFFFFFF
        edx = ctypes.c_int32(edx_u).value

        # mov cl, [eax+esi+1]  => next char
        next_index = eax + 1
        cl_next = username_bytes[next_index] if next_index < len(username_bytes) else 0

        # xor edx, 0xBADDC001
        edx = ctypes.c_int32(ctypes.c_uint32(edx).value ^ 0xBADDC001).value

        # inc eax
        eax += 1

        # test cl, cl; jnz loopstart
        cl = cl_next
        if cl == 0:
            break

    return '%08X' % (ctypes.c_uint32(edx).value)


def verify(name: str, serial: str) -> bool:
    """Verify that the serial matches the generated serial for name."""
    if len(name) < 6:
        return False
    expected = generate_serial(name)
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    """Generate a valid serial for the given name (must be >= 6 chars)."""
    if len(name) < 6:
        raise ValueError('Username must be at least 6 characters long.')
    return generate_serial(name)



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
