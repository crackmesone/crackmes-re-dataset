#!/usr/bin/env python3
"""
KeygenMe #2 by m@[tador] - Reverse Engineered Keygen

Two solutions were found:

SOLUTION A (from KEYGEN.ASM by mario/mbe):
  Simple formula per character:
    intDiv = (len(name) + 1) // 3
    serial[j] = chr( (ord(name[j-1]) XOR intDiv) + (5 * j) )   for j=1..len(name)
  (note: counter j starts at 1, serial length == name length)

SOLUTION B (from solution.pdf - the real crackme validation):
  The crackme uses RC4 internally. The writeup shows the check loop but the
  RC4 key/setup details are truncated. We implement what is clearly shown.

  From the disassembly comments:
  - len(name) must equal len(serial)
  - intDiv = (len(name)+1) // 3    (integer division by 3)
  - For each position i (0-based counter ds:dword_40A8DC):
      letter_from_serial = serial[i]
      val = (ord(serial[i]) + i) - (i * 5)   # i + i*4 = i*5
           = ord(serial[i]) - 4*i
      XOR with intDiv
      RC4-crypt that => compare with RC4-crypt of name-letter

  Because the RC4 key details are not fully recoverable from the truncated writeup,
  we implement the keygen from SOLUTION A (the MASM keygen source is complete and unambiguous).
"""

def _keygen_asm(name: str) -> str:
    """
    Implements the algorithm from the complete MASM keygen source (solution 2).
    
    From KEYGEN.ASM:
        save = len(name) + 1          ; (after GetDlgItemTextA returns len, then inc eax)
        intDiv = save // 3            ; cdq / idiv ecx(3)  -> eax=quotient -> ebx
        ecx = 1                       ; counter starts at 1
        for each char (edi walks name, esi walks serial):
            eax = unsigned(name[j])   ; movzx eax, byte ptr[edi]
            eax ^= ebx                ; xor eax, ebx  (ebx = intDiv)
            edx = ecx << 2            ; shl edx,2  -> ecx*4
            eax += edx                ; add eax, edx  -> name_char XOR intDiv + ecx*4
            serial[j] = eax & 0xFF    ; mov byte ptr[esi], al
            ecx += 1
            loop while ecx < save     ; cmp ecx, _save / jnz
    """
    if not name:
        return ''
    
    name_len = len(name)
    save = name_len + 1          # eax from GetDlgItemTextA = len, then inc eax
    int_div = save // 3          # cdq / idiv 3 -> quotient in eax -> ebx
    
    serial_chars = []
    ecx = 1
    for j in range(name_len):
        char_val = ord(name[j]) & 0xFF   # movzx - zero extend byte
        char_val ^= int_div               # xor with intDiv
        edx = ecx << 2                    # ecx * 4
        char_val = (char_val + edx) & 0xFF
        serial_chars.append(char_val)
        ecx += 1
        if ecx >= save:
            break
    
    # Build serial as raw bytes -> hex string (common for non-printable results)
    # The MASM keygen uses SetDlgItemTextA with raw bytes, so we return as string
    # ASSUMPTION: serial is treated as raw byte string; we return hex representation
    # since many chars may be non-printable
    try:
        serial = bytes(serial_chars).decode('latin-1')
    except Exception:
        serial = bytes(serial_chars).decode('latin-1', errors='replace')
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair using the algorithm from the MASM keygen.
    Checks:
    1. len(name) == len(serial)  (required by crackme)
    2. len(name) > 1             (crackme checks length >= 2)
    3. serial matches computed value
    """
    if not name or not serial:
        return False
    if len(name) != len(serial):
        return False
    if len(name) < 2:
        return False
    
    expected = _keygen_asm(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    if not name or len(name) < 2:
        raise ValueError('Name must be at least 2 characters long')
    return _keygen_asm(name)



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
