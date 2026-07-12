# Reconstructed keygen for 'braynfack' by lone.wolf
# Based on the keygen ASM source (garbled UTF encoding, partially decoded)
#
# Summary of what was recovered from the ASM keygen source:
#
# 1. The 'generrar' (generate) routine:
#    - Iterates over characters of the name (nombre)
#    - For each character at position edi:
#      * Loads byte from nombre[edi]
#      * Loads byte from serial[esi]  (esi = offset aux)
#      * XORs ecx,ecx and eax,eax
#      * Loop 'salto1':
#        - Loads byte ptr[edi] from name
#        - Moves byte ptr[edi] from name to byte ptr[esi] serial position
#        - add ecx, eax
#        - rol ecx, 6
#        - xor ecx, 0A0A0A0Ah
#        - test al, al
#        - jnz salto1
#      * xchg eax, ecx
#      * mov [crypt], eax   -> saves coded user value for later comparison
#
#    - Loop 'buscaserial':
#      * mov esi, offset aux2
#      * mov edi, esi
#      * xor ecx, ecx / xor eax, eax
#      * Loop 'salto2':
#        - Loads byte ptr[edi]
#        - Moves byte ptr[edi] from aux2 to byte ptr[esi]
#        - add ecx, eax
#        - ror ecx, 0Ch
#        - xor ecx, 5555h
#        - test al, al
#        - jnz salto2
#        - xchg eax, ecx
#
#    - Comparison:
#      * mov ebx, [crypt]
#      * cmp eax, ebx
#      * jnz fin  (no match -> increment counter & try coding serial differently)
#
#    - Conversion to decimal ASCII (2 bytes per digit):
#      * mov ebx, 0A0h  (10 decimal)
#      * xor ecx, ecx
#      * divide:
#        - xor edx, edx
#        - div ebx
#        - add edx, 30h  ('0')
#        - mov [aux2+ecx*2], edx
#        - inc ecx
#        - test eax, eax
#        - jnz divide
#
#    - Invert routine (invertiete):
#      * mov eax, [aux2+ecx*2-1]
#      * and eax, 0F0Fh
#      * or  eax, 3030h
#      * mov [aux2+ebx*2], eax
#      * inc ebx
#      * dec ecx
#      * cmp ecx, 0
#      * jl buscaserial
#      * jmp invertiete
#
#    - Serial has 10 digits (5*2 digits per pair)
#    - pop ecx / ret
#
# ASSUMPTION: The serial generation tries values 0..9999 until the ROR/XOR
# encoding of the candidate serial matches the ROL/XOR encoding of the name.
# The name encoding uses: accumulate bytes, ROL 6, XOR 0xA0A0A0A0
# The serial encoding uses: accumulate bytes (decimal digits), ROR 12, XOR 0x5555
# ASSUMPTION: 'aux' buffer holds the name string, 'aux2' holds serial digits as ASCII
# ASSUMPTION: The comparison is crypt (from name) == result from serial processing
# ASSUMPTION: serial is 10 decimal digits (as suggested by cmp eax, 10000 and 5*2)

import struct

def _encode_name(name: str) -> int:
    """Encode name string: accumulate bytes, ROL6, XOR 0xA0A0A0A0"""
    ecx = 0
    eax = 0
    for ch in name:
        eax = ord(ch) & 0xFF
        ecx = (ecx + eax) & 0xFFFFFFFF
        # ROL ecx, 6
        ecx = ((ecx << 6) | (ecx >> 26)) & 0xFFFFFFFF
        ecx = (ecx ^ 0xA0A0A0A0) & 0xFFFFFFFF
    return ecx

def _encode_serial_digits(digits_str: str) -> int:
    """Encode serial digit string: accumulate bytes, ROR 12, XOR 0x5555"""
    ecx = 0
    eax = 0
    for ch in digits_str:
        eax = ord(ch) & 0xFF
        ecx = (ecx + eax) & 0xFFFFFFFF
        # ROR ecx, 0Ch (12)
        ecx = ((ecx >> 12) | (ecx << 20)) & 0xFFFFFFFF
        ecx = (ecx ^ 0x5555) & 0xFFFFFFFF
    return ecx

def keygen(name: str) -> str:
    """
    Generate a 10-digit serial for the given name.
    ASSUMPTION: We search serials 0..9999999999 until encoding matches.
    For performance we brute-force up to 100000 candidates.
    """
    target = _encode_name(name)
    # ASSUMPTION: serial is a 10-char decimal string (possibly zero-padded)
    # Try candidates from 0 to 9999999999
    for candidate in range(10000000000):
        s = str(candidate).zfill(10)
        if _encode_serial_digits(s) == target:
            return s
    return None

def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    ASSUMPTION: serial must be a decimal string whose encoding matches name encoding.
    """
    if not name or not serial:
        return False
    # ASSUMPTION: serial length should be 10 digits
    # ASSUMPTION: serial must be all digits
    if not serial.isdigit():
        return False
    target = _encode_name(name)
    result = _encode_serial_digits(serial)
    return result == target


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
