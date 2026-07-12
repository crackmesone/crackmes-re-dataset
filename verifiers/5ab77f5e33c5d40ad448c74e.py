# KeyGenMe-1 by synapse - Key validation / keygen
# Based on xyzero's solution writeup
#
# PART A: Serial Maker Routine
#   For each EBX in range(1, 7):
#     For each ESI in range(0, 5):   (inner loop, ESI goes 0..4)
#       if EBX == ESI: skip (store nothing, just increment ESI)
#       else:
#         ECX = name[EBX] ... wait, actually:
#         ECX = name[0]  (always name[0])
#         AL  = name[ESI+1] ... actually the writeup shows ESI starts at 0
#                               and LODS reads from name[ESI], incrementing
#         The outer EBX loop seems to reset; the writeup is a bit ambiguous.
#
# PART B: Serial Check
#   The generated buffer's first 4 bytes are compared as a DWORD against
#   a value derived from the entered serial.
#
# ASSUMPTION: The serial maker produces a buffer; only the first 4 bytes matter.
# ASSUMPTION: The inner/outer loop relationship is that EBX is the 'column' index
#             and ESI is the 'row' index, both 0-based, skipping when EBX==ESI.
# ASSUMPTION: 'name[0]' always refers to byte 0 of the name string.
#
# From the writeup, for name="xyzero" (0x78,0x79,0x7A,0x65,0x72,0x6F):
#   The buffer starts with: A7 7A 65 72  (little-endian DWORD = 0x72657AA7)
#   Serial check: the entered serial (as text) is NOT directly compared;
#   instead a computed value from the serial bytes is compared to the buffer DWORD.
#
# Serial check routine (004072F0):
#   ECX = length of entered serial (from GetDlgItemTextA return value)
#   ESI points to name string
#   EDX  = (name[0] << 2) + name[1] + 2*name[2] + 11*name[3]
#   ESI2 = EDX
#   EDX  = EDX * EDX  (EDX = ESI2 * ESI2)
#   EAX  = ECX * EDX  (MUL: EAX:EDX = ECX * EDX, we take low 32 bits)
#   EAX  = EAX + EAX  (i.e., EAX * 2)
#   EAX  = EAX XOR 0x404358
#   This EAX is stored at [405CC8] (not used for compare directly)
#   Then [403B30] (first 4 bytes of generated serial buffer) is compared to [4032F4]
# ASSUMPTION: [4032F4] stores the entered serial's first 4 bytes as a DWORD (little-endian ASCII).
# ASSUMPTION: The comparison is between the generated buffer DWORD and the first 4 chars of entered serial.

def _make_serial_buffer(name: str) -> bytes:
    """Reconstruct the serial generation routine (Part A)."""
    # name is stored at 004054C8
    # Buffer written to 00403B30
    # Outer loop: EBX in 1..6 (CMP EBX,7 / JL)
    # Inner loop: ESI in 0..4 (CMP ESI,5 / JL)
    # At start of inner loop body: if EBX==ESI -> skip to INC ESI
    # ECX = name[EBX]  (name[0] for EBX=1? No - the writeup says name[0] always)
    # ASSUMPTION: ECX always = name[0] (the writeup trace shows EBX=1 -> name[0]='x')
    # Actually re-reading: ADD EBX, base_addr; MOV AL,[EBX] -> name[EBX] but EBX starts at 1
    #   so name[1] = second char. But the writeup says "get the name[0]" when EBX=1.
    # ASSUMPTION: The buffer address offset means name[EBX-1] or the loop is EBX in 0..6
    # The writeup says EBX goes 1..6 (INC EBX; CMP EBX,7) and at EBX=1 it reads name[0].
    # So ECX = name[EBX - 1].  (offset by -1)
    name_bytes = [ord(c) for c in name]
    buf = []
    for ebx in range(1, 7):
        for esi in range(0, 5):
            if ebx == esi:
                # JE -> skip to INC ESI (no store)
                continue
            # ECX = name[ebx - 1]  (ASSUMPTION: offset)
            ecx = name_bytes[(ebx - 1) % len(name_bytes)]
            # AL = name[esi] via LODS (ESI points into name, but ESI register is 0..4 here)
            # ASSUMPTION: LODS reads name[esi] (0-based into name string)
            al = name_bytes[esi % len(name_bytes)]
            # CMP ECX, EAX  (ECX=name[ebx-1], EAX=al=name[esi])
            if ecx >= al:   # JB: jump if ECX < EAX (unsigned below)
                # STOS AL directly
                buf.append(al & 0xFF)
            else:
                # ECX < AL  => NOT jump at JB
                result = al - ecx          # SUB EAX, ECX
                result = (result - 2) & 0xFFFFFFFF  # ADD EAX, -2
                result = result ^ 0x404358           # XOR EAX, 404358
                buf.append(result & 0xFF)
    return bytes(buf)


def _compute_check_value(name: str, serial_len: int) -> int:
    """Reconstruct the serial check routine (Part B) - computes expected DWORD."""
    nb = [ord(c) for c in name]
    # ASSUMPTION: uses first 4 bytes of name
    n0 = nb[0] if len(nb) > 0 else 0
    n1 = nb[1] if len(nb) > 1 else 0
    n2 = nb[2] if len(nb) > 2 else 0
    n3 = nb[3] if len(nb) > 3 else 0
    edx = ((n0 << 2) + n1 + 2 * n2 + 11 * n3) & 0xFFFFFFFF
    esi2 = edx
    edx = (esi2 * esi2) & 0xFFFFFFFF
    ecx = serial_len & 0xFFFFFFFF
    # MUL EDX: EAX:EDX = ECX * EDX, take low 32
    eax = (ecx * edx) & 0xFFFFFFFF
    eax = (eax + eax) & 0xFFFFFFFF   # ADD EAX, EAX
    eax = (eax ^ 0x404358) & 0xFFFFFFFF
    return eax


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    
    The crackme compares the first 4 bytes of the generated serial buffer
    (as a little-endian DWORD) against the first 4 bytes of the entered serial
    (as ASCII characters interpreted as a little-endian DWORD).
    ASSUMPTION: comparison is direct ASCII bytes of serial vs generated buffer.
    """
    if len(name) < 5:
        return False
    if len(serial) < 4:
        return False
    buf = _make_serial_buffer(name)
    if len(buf) < 4:
        return False
    # [403B30] = first 4 bytes of generated buffer as little-endian DWORD
    gen_dword = int.from_bytes(buf[:4], 'little')
    # [4032F4] = first 4 bytes of entered serial as little-endian DWORD (ASCII)
    ser_dword = int.from_bytes(serial[:4].encode('latin-1'), 'little')
    return gen_dword == ser_dword


def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    
    The valid serial only needs its first 4 bytes to match the generated buffer.
    We append extra characters to meet any minimum length requirements.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")
    buf = _make_serial_buffer(name)
    # First 4 bytes of buffer are the required serial prefix
    serial_prefix = buf[:4].decode('latin-1')
    # Pad to at least 5 chars with arbitrary printable chars
    serial = serial_prefix + 'AAAA'
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
