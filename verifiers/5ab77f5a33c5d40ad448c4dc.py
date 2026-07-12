import struct

def _to_u32(x):
    return x & 0xFFFFFFFF

def generate_serial(name):
    """
    Implements the keygen algorithm from the assembly / C translation in the writeup.
    All arithmetic is unsigned 32-bit (mod 2^32), matching x86 register behaviour.
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    eax = len(name_bytes)

    # Initialise registers
    edi = 0
    ecx = _to_u32(eax * 45)          # IMUL ECX,ECX,2D  (2Dh=45)
    edx = _to_u32(ecx * 2)           # LEA EDX,[ECX+ECX]
    esi = _to_u32(edx * 3)           # LEA ESI,[EDX+EDX*2]
    ebp4  = esi                      # MOV [EBP-4],ESI
    esi   = _to_u32(eax * ebp4)      # IMUL ESI,[EBP-4]
    ebp4  = _to_u32(ebp4 + eax)      # ADD [EBP-4],EAX
    ebp14 = 0                        # [EBP-14] = deg_311E = 0

    # --- Loop 1 ---
    for i in range(eax):
        edi = i
        esi = _to_u32(esi + eax)     # ADD ESI,EAX
        edi = name_bytes[i]          # MOVSX EDI,BYTE (sign-extended, but byte chars <= 127 typically)
        # Handle signed byte
        if edi >= 128:
            edi = edi - 256
        edi = _to_u32(edi * ecx)     # IMUL EDI,ECX
        edi = _to_u32(edi + edx)     # ADD EDI,EDX
        ebp14 = _to_u32(ebp14 + edi) # ADD [EBP-14],EDI
        ecx = _to_u32(ecx + 1)       # INC ECX
        edi = _to_u32(esi + ecx)     # LEA EDI,[ESI+ECX]
        edx = _to_u32(edx + edi)     # ADD EDX,EDI

    # --- Between loops 1 and 2 ---
    edi = 0
    esi = _to_u32(edx * 45)          # IMUL ESI,ESI,2D
    esi = _to_u32(esi + ecx)         # ADD ESI,ECX
    ebp10 = 0                        # [EBP-10] = deg_3122 = 0

    # --- Loop 2 ---
    for i in range(eax):
        ecx = name_bytes[i]          # MOVSX ECX,BYTE
        if ecx >= 128:
            ecx = ecx - 256
        ecx = _to_u32(ecx + 1)       # INC ECX
        esi = _to_u32(esi + 45)      # ADD ESI,2Dh
        ecx = _to_u32(ecx * edx)     # IMUL ECX,EDX
        ebp10 = _to_u32(ebp10 + ecx) # ADD [EBP-10],ECX
        ebp4  = _to_u32(ebp4 + esi)  # ADD [EBP-4],ESI
        edx = _to_u32(edx + 1)       # INC EDX
        edi = _to_u32(edi + 1)       # INC EDI

    # --- Between loops 2 and 3 ---
    ecx = 0
    ebpc = 0                         # [EBP-C] = deg_3126 = 0

    # --- Loop 3 ---
    for i in range(eax):
        esi = name_bytes[i]          # MOVSX ESI,BYTE
        if esi >= 128:
            esi = esi - 256
        esi = _to_u32(esi * ebp4)    # IMUL ESI,[EBP-4]
        esi = _to_u32(esi + edx)     # ADD ESI,EDX
        ebpc = _to_u32(ebpc + esi)   # ADD [EBP-C],ESI
        edx = _to_u32(edx + 1)       # INC EDX
        ecx = _to_u32(ecx + 1)       # INC ECX

    # --- Compute s1, s2, s3 ---
    # s3 = (eax+2) * ebpc
    ecx_tmp = _to_u32(eax + 2)
    s3 = _to_u32(ecx_tmp * ebpc)

    # s1 = eax * ebp14
    s1 = _to_u32(eax * ebp14)

    # s2 = ebp10 + ebp14
    s2 = _to_u32(ebp10 + ebp14)

    return '{}-{}-{}'.format(s1, s2, s3)


def verify(name, serial):
    """
    Returns True if serial matches the generated serial for the given name.
    Name must be between 4 and 24 characters (inclusive).
    """
    if isinstance(name, str):
        n = name.encode('latin-1')
    else:
        n = name
    if len(n) < 4 or len(n) > 24:
        return False
    expected = generate_serial(name)
    return serial.strip() == expected


def keygen(name):
    """
    Returns a valid serial for the given name.
    Raises ValueError if name length is not in [4, 24].
    """
    if isinstance(name, str):
        n = name.encode('latin-1')
    else:
        n = name
    if len(n) < 4 or len(n) > 24:
        raise ValueError('Name must be between 4 and 24 characters')
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
