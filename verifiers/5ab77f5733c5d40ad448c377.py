import ctypes

def _sar32(value, shift):
    """Arithmetic shift right for 32-bit signed integers."""
    v = ctypes.c_int32(value).value
    if shift == 0:
        return v
    return v >> shift

def _shr32(value, shift):
    """Logical shift right for 32-bit unsigned integers."""
    return ctypes.c_uint32(value).value >> shift

def _to_int32(value):
    return ctypes.c_int32(value).value

def _to_uint32(value):
    return ctypes.c_uint32(value).value

def _imul64(a, b):
    """Signed 32x32 -> 64-bit multiply, return (edx, eax) as signed 32-bit pair."""
    result = ctypes.c_int32(a).value * ctypes.c_int32(b).value
    eax = _to_int32(result & 0xFFFFFFFF)
    edx = _to_int32((result >> 32) & 0xFFFFFFFF)
    return edx, eax

def compute_serial1(id_val):
    """
    Serial 1 algorithm (from disassembly at 0x401304):

    EDX = id_val
    EAX = EDX
    EAX = SAR(EAX, 0x1F)   ; sign bit replicated -> 0 if positive, -1 if negative
    EAX = SHR(EAX, 0x1F)   ; 0 if positive, 1 if negative
    EAX = EDX + EAX         ; for positive: EAX = id; for negative: EAX = id+1 (floor div prep)
    EDX = EAX
    EDX = SAR(EDX, 1)       ; EDX = floor(id / 2)
    EAX = EDX
    EAX = EAX + EAX         ; EAX = 2 * floor(id/2)
    EAX = EAX + EDX         ; EAX = 3 * floor(id/2)
    EAX = EAX + 0x50A5D     ; EAX = 3*floor(id/2) + 330333
    """
    edx = _to_int32(id_val)
    eax = edx
    eax = _sar32(eax, 0x1F)   # 0 for positive, -1 for negative
    eax = _shr32(eax, 0x1F)   # 0 for positive, 1 for negative
    eax = _to_int32(_to_uint32(edx) + _to_uint32(eax))
    edx = eax
    edx = _sar32(edx, 1)
    eax = edx
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax))  # *2
    eax = _to_int32(_to_uint32(eax) + _to_uint32(edx))  # +edx
    eax = _to_int32(_to_uint32(eax) + 0x50A5D)
    return eax

def compute_serial2(serial1):
    """
    Serial 2 algorithm (from disassembly at 0x401359):

    EDX = serial1
    [LOCAL.9] = serial1
    EAX = 0x55555556
    (EDX, EAX) = IMUL(EAX, serial1)  ; signed 64-bit result, high 32 bits in EDX
    ECX = EDX                         ; high 32 bits of product
    EAX = serial1
    EAX = SAR(EAX, 0x1F)             ; sign bit of serial1 (0 or -1)
    ECX = ECX - EAX                  ; adjust for sign -> ECX = serial1 / 3
    EAX = ECX
    EDX = EAX + 0x40564              ; EDX = serial1/3 + 263524
    EAX = EDX
    EAX = SAR(EAX, 0x1F)
    EAX = SHR(EAX, 0x1F)
    EAX = EDX + EAX
    EAX = SAR(EAX, 1)                ; EAX = floor((serial1/3 + 263524) / 2) with rounding
    """
    local9 = _to_int32(serial1)
    eax_mul = _to_int32(0x55555556)
    edx_hi, _ = _imul64(eax_mul, local9)
    ecx = edx_hi
    eax = _to_int32(local9)
    eax = _sar32(eax, 0x1F)  # sign bit
    ecx = _to_int32(_to_uint32(ecx) - _to_uint32(eax))
    eax = ecx
    # LEA EDX, [EAX + 0x40564]
    edx = _to_int32(_to_uint32(eax) + 0x40564)
    eax = edx
    eax = _sar32(eax, 0x1F)
    eax2 = _shr32(eax, 0x1F)
    eax = _to_int32(_to_uint32(edx) + _to_uint32(eax2))
    eax = _sar32(eax, 1)
    return eax

def compute_serial3(id_val, serial1, serial2):
    """
    Serial 3 algorithm (from disassembly at 0x4013BE):

    EAX = serial1
    EAX = EAX + id_val          ; EAX = serial1 + id
    ECX = EAX
    ECX = ECX + serial2         ; ECX = serial1 + id + serial2
    EAX = 0x2E8BA2E9
    (EDX, EAX) = IMUL(ECX)      ; signed 64-bit, high bits in EDX
    EDX = SAR(EDX, 1)           ; EDX >>= 1
    EAX = ECX
    EAX = SAR(EAX, 0x1F)        ; sign bit of ECX
    EDX = EDX - EAX             ; adjust
    EAX = EDX
    """
    eax = _to_int32(serial1)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(_to_int32(id_val)))
    ecx = eax
    ecx = _to_int32(_to_uint32(ecx) + _to_uint32(_to_int32(serial2)))
    eax_mul = _to_int32(0x2E8BA2E9)
    edx_hi, _ = _imul64(eax_mul, ecx)
    edx = _sar32(edx_hi, 1)
    eax = _to_int32(ecx)
    eax = _sar32(eax, 0x1F)  # sign bit of ecx
    edx = _to_int32(_to_uint32(edx) - _to_uint32(eax))
    eax = edx
    return eax

def keygen(id_val):
    """
    Generate (serial1, serial2, serial3) for a given numeric ID.
    The VB keygen shows that if ID is odd, it uses ID-1 for S1 and S3 computation.
    (ID is used as-is for the raw assembly, but the VB code rounds down to even.)
    """
    # ASSUMPTION: The crackme takes a numeric ID, not a name string.
    # The VB keygen from solution 1 adjusts odd IDs down by 1.
    id_int = int(id_val)
    if id_int % 2 != 0:
        id_adjusted = id_int - 1
    else:
        id_adjusted = id_int

    s1 = compute_serial1(id_adjusted)
    s2 = compute_serial2(s1)
    s3 = compute_serial3(id_adjusted, s1, s2)
    return (s1, s2, s3)

def verify(name, serial):
    """
    Verify (name=ID string, serial='s1:s2:s3' or tuple).
    name is the numeric ID entered by the user.
    serial can be a tuple (s1, s2, s3) or a colon-separated string.
    """
    try:
        id_int = int(name)
    except (ValueError, TypeError):
        return False

    if isinstance(serial, (tuple, list)):
        try:
            s1_in, s2_in, s3_in = int(serial[0]), int(serial[1]), int(serial[2])
        except (ValueError, IndexError):
            return False
    else:
        parts = str(serial).split(':')
        if len(parts) != 3:
            return False
        try:
            s1_in, s2_in, s3_in = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            return False

    # ASSUMPTION: ID is used directly (no rounding) in raw assembly check;
    # the VB keygen rounds odd IDs down. We replicate raw assembly here.
    s1_expected = compute_serial1(id_int)
    s2_expected = compute_serial2(s1_expected)
    s3_expected = compute_serial3(id_int, s1_expected, s2_expected)

    return (s1_in == s1_expected and s2_in == s2_expected and s3_in == s3_expected)


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
