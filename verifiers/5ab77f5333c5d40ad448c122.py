#!/usr/bin/env python3
"""
CrackMe #3 by spoke3fff - Serial Validation Algorithm

From the writeup/assembly:
- Serial must be >= 4 characters (length check: if len==3 go to 'light register', if len==4 -> full registered path)
- Actually: len==3 -> jump to light_register (wrong), len==4 -> full registered OK
  Wait, re-reading: CMP EAX,3 / JNZ SHORT -> if not 3, skip; CMP EAX,4 / JE -> if 4, full registered
  So serial length must be >= 4 (checked as ==4? or >=5 with extra chars?)
  The writeup says: 'ZAV + any 2 char/digit = Full Registered' -> length 5
  ASSUMPTION: The length check passes if len >= 4 (the cmp eax,4 / je means exactly 4 or the keygen adds random digits)

The core algorithm (from assembly and VB keygen):
- Take first 3 characters of serial
- Compute a running sum using 32-bit arithmetic:
  BL starts at 1, ESI points to serial string
  For i in 1..3:
    AL = serial[i-1]  (byte)
    sum += AL         (ADD to [4097D2])
    AL = AL XOR BL    (XOR with loop counter 1,2,3)
    AL = AL * AL      (MUL AL - 8-bit multiply: result in AX = AL*AL)
    BL++, ESI++
  Finally compare sum to 0x31F1

IMPORTANT: The assembly does:
  ADD [sum], EAX  (EAX = zero-extended AL = full byte value of serial[i])
  XOR AL, BL
  MUL AL          -> AX = AL * AL (8-bit multiply)
  Then loops - but the result of MUL (AX) seems to not be added to sum explicitly in assembly...
  
However the VB keygen DOES add the mul result to sum. Let's follow the VB keygen as ground truth.

VB Keygen logic (translated):
  suma = 0
  
  # char 1 (index 0), bl=1
  al = ord(serial[0])
  suma += al           # ADD [sum], eax (eax = al)
  al = 1 ^ al          # XOR AL, BL (bl=1)
  eax = al * al        # MUL AL -> AX
  # VB then does complex hex truncation to simulate 16-bit register behavior
  # eax_hex = hex(eax), take high byte of 16-bit result, combine with next char's low byte
  
  # char 2 (index 1), bl=2  
  al2 = ord(serial[1])
  # eax is treated as 16-bit: high_byte = (al*al) >> 8 & 0xFF, low_byte = al2
  eax_combined = ((al * al) & 0xFF00) | al2  # 16-bit value
  suma += eax_combined
  
  # char 3 (index 2), bl=3
  al3_xor = 2 ^ al2    # previous al XOR'd with BL=2... wait, al was overwritten
  # ASSUMPTION: following VB code literally:
  #   al = 2 Xor al  (al here is still al from char1 xor, then xor'd with 2)
  #   eax = al * al
  # This is confusing. Let's implement directly from VB:
"""

def _compute_sum_vb(s3):
    """Compute the checksum for first 3 chars, following VB keygen logic."""
    # VB uses variant arithmetic and hex string manipulation
    # Let's implement it step by step
    
    suma = 0
    
    # Step 1: char at index 0, BL=1
    al = ord(s3[0]) & 0xFF
    suma += al
    al = (1 ^ al) & 0xFF          # XOR AL, BL (BL=1)
    eax = (al * al) & 0xFFFF      # MUL AL -> AX (16-bit)
    
    # Step 2: char at index 1, BL=2
    al2 = ord(s3[1]) & 0xFF
    # VB: eax = Hex(eax), take first 2 hex digits (high byte) + Hex(al2) = low byte
    # This constructs a new eax from high_byte_of_prev_mul and current char
    high_byte = (eax >> 8) & 0xFF
    eax2 = (high_byte << 8) | al2   # 16-bit
    suma += eax2
    
    # After this iteration:
    # VB: al = 2 Xor al  where 'al' is still the result from step1 XOR
    # ASSUMPTION: 'al' in VB is not updated to al2 before the XOR in step 3
    al_step3 = (2 ^ al) & 0xFF    # BL was incremented to 2, XOR with previous al
    eax3 = (al_step3 * al_step3) & 0xFFFF
    al3 = ord(s3[2]) & 0xFF
    high_byte3 = (eax3 >> 8) & 0xFF
    eax3_combined = (high_byte3 << 8) | al3
    suma += eax3_combined
    
    return suma & 0xFFFF


def _compute_sum_asm(s3):
    """
    Implement the assembly loop directly:
    sum = 0  (32-bit at [4097D2])
    BL = 1
    for i in range(3):
        AL = serial[i]
        sum += AL  (32-bit add, AL zero-extended)
        AL = AL XOR BL
        AX = AL * AL  (MUL AL: 8-bit * 8-bit = 16-bit in AX)
        # AX result is NOT added to sum in the loop body per assembly
        # But the next iteration: MOV AL, [ESI] loads next char
        # The MUL result in AX/AL is overwritten
        BL += 1
    """
    # ASSUMPTION: The assembly only adds the raw char bytes to sum, not the mul results
    # The mul may be used differently (perhaps AX feeds into next iteration's ADD?)
    # But the VB keygen clearly adds more. Let's implement both and prefer VB.
    suma = 0
    for i in range(3):
        al = ord(s3[i]) & 0xFF
        suma = (suma + al) & 0xFFFFFFFF
        # MUL result not explicitly added back per assembly reading
    return suma & 0xFFFF


def _compute_checksum(s3):
    """Use VB keygen logic as ground truth."""
    return _compute_sum_vb(s3)


def verify(name, serial):
    """
    Verify a serial for this crackme.
    
    'Light Registered': The serial's ESI (ptr) != hardcoded HEXA ptr
      -> This seems to be a pointer comparison, likely checking if
         the serial buffer == a hardcoded string. 
         ASSUMPTION: Light registered = serial is exactly the hardcoded string
         (ESI == HEXA means success for light register)
         From writeup: 'HEXA = hardcoded Light Registered' -> specific hardcoded serial
         We don't know this value. ASSUMPTION: we skip light register check.
    
    'Full Registered': serial length >= 4, first 3 chars satisfy checksum == 0x31F1,
                        remaining chars can be anything.
    
    From writeup: 'ZAV + any 2 char/digit = Full Registered'
    """
    if len(serial) < 4:
        return False
    
    # ASSUMPTION: name is not used in the check (no name field visible in algorithm)
    
    s3 = serial[:3]
    checksum = _compute_checksum(s3)
    
    # Compare to 0x31F1 = 12785
    TARGET = 0x31F1
    return checksum == TARGET


def keygen(name):
    """
    Generate a valid serial for Full Registered.
    Brute force first 3 chars from printable ASCII range (0x30-0x7A per VB),
    then append '00' as the required extra chars.
    """
    TARGET = 0x31F1
    # Search space: chars from 0x30 ('0') to 0x7A ('z') per VB keygen
    for c1 in range(0x30, 0x7B):
        for c2 in range(0x30, 0x7B):
            for c3 in range(0x30, 0x7B):
                s3 = chr(c1) + chr(c2) + chr(c3)
                if _compute_checksum(s3) == TARGET:
                    return s3 + '00'  # append 2 chars to satisfy length >= 4
    # ASSUMPTION: if not found in range, try broader range
    for c1 in range(32, 127):
        for c2 in range(32, 127):
            for c3 in range(32, 127):
                s3 = chr(c1) + chr(c2) + chr(c3)
                if _compute_checksum(s3) == TARGET:
                    return s3 + '00'
    return None


def keygen_all(name):
    """Generator yielding all valid serials (first 3 chars from '0'-'z' range)."""
    TARGET = 0x31F1
    for c1 in range(0x30, 0x7B):
        for c2 in range(0x30, 0x7B):
            for c3 in range(0x30, 0x7B):
                s3 = chr(c1) + chr(c2) + chr(c3)
                if _compute_checksum(s3) == TARGET:
                    yield s3 + '00'



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
