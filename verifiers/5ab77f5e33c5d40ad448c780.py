# Reverse-engineered algorithm for Berlon keygenme by necro1337
# Based on the solution writeup by crackmes.de
#
# Key observations from writeup:
# 1. Username MUST start with 'USER'
# 2. Username must be at least 6 bytes (so at least 2 chars after 'USER')
# 3. The characters after 'USER' that are digits ('0'-'9', i.e. 0x30-0x39) are used to compute a value
# 4. A second transformation is applied to produce the final serial
#
# ASSUMPTION: The full password comparison and final output format are truncated in the writeup.
# We implement what we can determine from the assembly snippets.

import ctypes

def _to_int32(v):
    """Truncate to signed 32-bit integer (simulate x86 register overflow)."""
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def _to_uint32(v):
    return v & 0xFFFFFFFF

def compute_numeric_value(digits_str):
    """
    Implements the assembly loop at 0x004021E0.
    Processes digits (chars with ord in 0x30..0x39) from the part of username after 'USER'.
    
    The loop:
      - Works with a 64-bit value in (EDX:EAX) and EBX/EBP as temporaries
      - For each digit char CL in [0x30, 0x39]:
          EBX = EAX  (current accumulated value)
          EBP = EDX
          SHLD EDX, EAX, 2   => EDX = (EDX << 2) | (EAX >> 30), but high bits only matter for 64-bit
          EAX = EAX * 4      (two ADD EAX,EAX)
          EBX = EBX + EAX    => EBX = old_EAX + EAX*4 = old_EAX * 5
          EBP += EDX (with carry from EBX)
          SHLD EBP, EBX, 1   => EBP = (EBP << 1) | (EBX >> 31)
          EAX = sign_extend(CL)  (current digit char value)
          CDQ => EDX = sign of EAX (0 since CL in 0x30..0x39)
          EBX = EBX * 2
          EAX = EAX + EBX    => EAX = digit_char + EBX
          EDX += EBP
          EAX -= 0x30        => subtract ASCII '0' to get numeric digit
          EDX -= 0 (SBB with 0)
      This is essentially: acc = acc * 10 + digit
    Returns (EDX, EAX) as a 64-bit pair, but we mainly care about EAX (low 32 bits).
    """
    eax = 0
    edx = 0
    
    chars = list(digits_str)
    if not chars:
        return eax
    
    # We need to look ahead: load first CL and then iterate
    # The loop checks CL >= 0x30 and CL <= 0x39
    i = 0
    # Prime CL with first char
    cl = ord(chars[i]) if i < len(chars) else 0
    
    while 0x30 <= cl <= 0x39:
        ebx = eax
        ebp = edx
        
        # SHLD EDX, EAX, 2
        new_edx = _to_uint32((edx << 2) | (_to_uint32(eax) >> 30))
        # EAX *= 4
        eax = _to_uint32(eax) * 4
        # EBX += EAX  => old_eax * 5
        ebx = _to_uint32(ebx + eax)
        # EBP += new_edx
        ebp = _to_uint32(ebp + new_edx)
        # SHLD EBP, EBX, 1
        ebp = _to_uint32((ebp << 1) | (_to_uint32(ebx) >> 31))
        
        # MOVSX EAX, CL
        eax_new = cl  # cl is in 0x30..0x39, so sign extension is just cl
        # CDQ => edx = 0 since eax_new >= 0
        edx_new = 0
        
        # Get next char
        i += 1
        next_cl = ord(chars[i]) if i < len(chars) else 0
        
        # EBX *= 2
        ebx = _to_uint32(ebx * 2)
        # EAX = eax_new + EBX
        eax = _to_uint32(eax_new + ebx)
        # EDX = edx_new + EBP
        edx = _to_uint32(edx_new + ebp)
        # EAX -= 0x30
        eax = _to_uint32(eax - 0x30)
        # (EDX -= 0 via SBB)
        
        cl = next_cl
        if not (0x30 <= cl <= 0x39):
            break
    
    return _to_int32(eax)

def apply_generator_transform(val):
    """
    Implements the 'generator' function at 0x00401131.
    Input: val (the computed numeric value from digits)
    
    Steps (all 32-bit signed/unsigned):
      1. ebx = val * 10
      2. ebx += 0x7D (125)
      3. ebx += -0x63 (i.e. ebx -= 0x63, which is ebx -= 99 => net so far: val*10 + 125 - 99 = val*10 + 26)
      4. ebx *= 0x81 (129)
      5. ebx = ebx // 2  (signed IDIV by 2)
      6. ebx = ebx + ebx + ebx = ebx * 3  (ADD ebx,ebx then ADD ebx,ebx: wait, re-read...)
         Actually: ADD EBX,[var] twice = EBX + var + var = ebx*3 if var=ebx after step5
         Then ADD EBX,[var] once more after storing => ebx*2 of the *3 result = *6? 
         # ASSUMPTION: The store/reload pattern makes this ebx*4 then ebx*2 = ebx*4:
         # After IDIV: ebx stored to [407C10]
         # ADD EBX,[407C10] => ebx = ebx + ebx = ebx*2, store
         # ADD EBX,[407C10] => ebx = ebx + ebx = ebx*2 (now ebx*4 of original), store  -- wait stored is the *2
         # Let me re-read more carefully:
         # mov [var],ebx  (ebx = x)
         # add ebx,[var]  => ebx = x+x = 2x, but [var] still = x
         # add ebx,[var]  => ebx = 2x+x = 3x
         # mov [var],ebx  (var = 3x)
         # add ebx,[var]  => ebx = 3x+3x = 6x
         # mov [var],ebx
         # So total multiplier after IDIV: *6
      7. ebx *= 0x3E7 (999)
    Returns the final transformed value.
    """
    # Step 1: *10
    ebx = _to_int32(val * 10)
    # Step 2: +0x7D
    ebx = _to_int32(ebx + 0x7D)
    # Step 3: ADD -0x63 = subtract 0x63
    ebx = _to_int32(ebx - 0x63)
    # Step 4: *0x81
    ebx = _to_int32(ebx * 0x81)
    # Step 5: IDIV by 2 (signed)
    # Python int division truncates toward negative infinity, but x86 IDIV truncates toward zero
    if ebx < 0:
        ebx = -((-ebx) // 2)
    else:
        ebx = ebx // 2
    # Step 6: *6 (see analysis above)
    ebx = _to_int32(ebx * 6)
    # Step 7: *0x3E7
    ebx = _to_int32(ebx * 0x3E7)
    return ebx

def keygen(name):
    """
    Generate a serial for a given username.
    Username must start with 'USER' and be at least 6 chars.
    Characters after 'USER' that are digits contribute to the numeric computation.
    
    ASSUMPTION: The final serial is the decimal or hex string representation
    of the transformed value. The exact output format is not shown in the writeup.
    """
    if not name.startswith('USER'):
        raise ValueError("Username must start with 'USER'")
    if len(name) < 6:
        raise ValueError("Username must be at least 6 characters")
    
    suffix = name[4:]  # Part after 'USER'
    
    # Extract leading digits for computation
    # ASSUMPTION: all digit chars in suffix are processed
    digit_chars = ''.join(c for c in suffix if '0' <= c <= '9')
    
    if not digit_chars:
        # ASSUMPTION: If no digits, the numeric value is 0
        # The writeup mentions you could bypass key generation with no numericals
        numeric_val = 0
    else:
        numeric_val = compute_numeric_value(digit_chars)
    
    final_val = apply_generator_transform(numeric_val)
    
    # ASSUMPTION: Serial is the decimal string representation of the unsigned 32-bit value
    serial = str(_to_uint32(final_val))
    return serial

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: The serial should match the keygen output.
    """
    if not name.startswith('USER'):
        return False
    if len(name) < 6:
        return False
    try:
        expected = keygen(name)
        return serial == expected
    except Exception:
        return False


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
