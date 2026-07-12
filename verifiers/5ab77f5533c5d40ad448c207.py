import struct

def transform_byte(b, ecx):
    """Transform a single serial byte using the crackme's inner function.
    Based on the assembly at 0040197F (but the bulk of that function is
    discarded; only the tail matters for the serial):
      eax = b + ecx
      if eax < 0x21: eax += 0x21
      if eax > 0x7b: eax >>= 1
    ecx counts DOWN from 0x10 to 1 (loop uses LOOPD with initial ECX=0x10).
    """
    eax = b + ecx
    if eax < 0x21:
        eax += 0x21
    if eax > 0x7b:
        eax >>= 1
    return eax & 0xFF


def float_to_packed_bcd(value):
    """Simulate x87 FBSTP: convert integer to 18-digit packed BCD (10 bytes).
    Returns bytes object of 10 bytes (little-endian BCD, sign in byte 9 high nibble)."""
    negative = value < 0
    value = abs(int(value))
    bcd = []
    for _ in range(9):
        lo = value % 10
        value //= 10
        hi = value % 10
        value //= 10
        bcd.append((hi << 4) | lo)
    sign_byte = 0x80 if negative else 0x00
    bcd.append(sign_byte)
    return bytes(bcd)


def compute_bcd_bytes(dword_val):
    """Given the 4-byte integer from serial[2:6] after transform,
    convert to packed BCD and extract cl (byte 0) and dl (byte 0 low nibble
    + 0x30 / shifted version).
    Based on the C keygen and assembly description:
      - fild the dword as a qword
      - fbstp -> get 10 bytes of packed BCD
      - pop ecx = first 4 bytes
      - edx = ecx
      - ecx >>= 4
      - edx &= 0x0F0F0F0F
      - ecx &= 0x0F0F0F0F
      - edx += 0x30303030
      - ecx += 0x30303030
      - key[0] = cl (ecx & 0xFF)
      - key[1] = dl (edx & 0xFF)
    """
    bcd = float_to_packed_bcd(dword_val)
    # First 4 bytes of packed BCD -> ecx
    ecx = struct.unpack_from('<I', bcd, 0)[0]
    edx = ecx
    ecx_shifted = (ecx >> 4) & 0x0F0F0F0F
    edx_masked = edx & 0x0F0F0F0F
    ecx_final = (ecx_shifted + 0x30303030) & 0xFFFFFFFF
    edx_final = (edx_masked + 0x30303030) & 0xFFFFFFFF
    cl = ecx_final & 0xFF
    dl = edx_final & 0xFF
    return cl, dl


def verify(name, serial):
    """Verify the serial against the crackme algorithm.
    The serial is validated independently of the name (name-independent keygen).
    Serial must be at least 6 characters (crackme reads up to 0x1E bytes).
    
    Steps:
    1. Apply transform to each of the first 0x10 bytes of serial (ecx goes 0x10..1).
       transformed[i] = transform_byte(serial[i], ecx) where ecx = 0x10 - i
       ASSUMPTION: ECX in the loop goes from 0x10 down to 1 (LOOP instruction decrements before check).
    2. Take transformed[2..5] (4 bytes) as a little-endian DWORD.
    3. Convert that DWORD via fbstp to packed BCD, extract cl and dl.
    4. Compute: ax = (transformed[0] | (transformed[1] << 8)) as unsigned short
               bx = (cl | (dl << 8)) as unsigned short
               result = ((ax - bx) ^ 0x1B3F) - 0x123
    5. result == 0 means valid.
    
    ASSUMPTION: The transform loop uses ECX as the addend (not a fixed constant).
    ASSUMPTION: The final check is (ax - bx) ^ 0x1B3F - 0x123 == 0, i.e. ax - bx == 0x1B3F ^ 0x123 = 0x1A1C.
    """
    if len(serial) < 2:
        return False
    s = [ord(c) for c in serial]
    n = min(len(s), 0x10)
    transformed = []
    for i in range(n):
        ecx = 0x10 - i  # ECX counts down: first iteration ecx=0x10, last ecx=1
        transformed.append(transform_byte(s[i], ecx))
    # Pad if serial shorter than expected
    while len(transformed) < 6:
        transformed.append(0)
    
    # Get first two transformed bytes as ax
    ax = (transformed[0] | (transformed[1] << 8)) & 0xFFFF
    
    # Get dword from transformed[2..5]
    dword_val = struct.unpack_from('<I', bytes(transformed[2:6]))[0]
    
    # BCD conversion
    cl, dl = compute_bcd_bytes(dword_val)
    bx = (cl | (dl << 8)) & 0xFFFF
    
    # Final check: ((ax - bx) ^ 0x1B3F) - 0x123 == 0
    # => ax - bx == 0x1A1C  (0x1B3F ^ 0x123 = 0x1A1C... let's verify: 0x1B3F^0x123=0x1A1C yes)
    result = (((ax - bx) & 0xFFFF) ^ 0x1B3F) - 0x123
    return (result & 0xFFFFFFFF) == 0


def keygen(name):
    """Generate a valid serial (name-independent).
    
    Strategy (based on C keygen by r2nwcnydc):
    - Pick 4 random bytes for positions 2-5 of the PRE-transform serial in range [0x21,0x7A].
    - Apply forward transform to get transformed[2..5].
    - Compute BCD bytes (cl, dl) from that DWORD.
    - We need: (ax - bx) & 0xFFFF == 0x1A1C
      ax = low16 of (transformed[0] | transformed[1]<<8)
      bx is fixed by the choice of serial[2..5]
    - So ax = (bx + 0x1A1C) & 0xFFFF
      transformed[0] = ax & 0xFF, transformed[1] = (ax >> 8) & 0xFF
    - Invert the transform to get serial[0] and serial[1]:
      transform_byte(s[i], ecx) = transformed[i]
      We need to find s such that s + ecx (mod adjustments) = transformed
    - Append extra bytes (serial[6..10]) as printable chars.
    
    ASSUMPTION: inversion of transform_byte is approximate (we brute-force it).
    """
    import random
    
    def invert_transform(target, ecx):
        """Find s in [0x21,0x7A] such that transform_byte(s, ecx) == target."""
        for s in range(0x21, 0x7B):
            if transform_byte(s, ecx) == target:
                return s
        return None
    
    for _ in range(10000):
        # Pick serial[2..5] in printable ASCII range
        raw = [random.randint(0x21, 0x7A) for _ in range(4)]
        # Transform them (ecx for positions 2,3,4,5 = 0x10-2=0xE, 0xD, 0xC, 0xB)
        transformed_2_5 = [transform_byte(raw[i], 0x10 - (i+2)) for i in range(4)]
        
        dword_val = struct.unpack_from('<I', bytes(transformed_2_5))[0]
        cl, dl = compute_bcd_bytes(dword_val)
        bx = (cl | (dl << 8)) & 0xFFFF
        
        ax = (bx + 0x1A1C) & 0xFFFF
        t0 = ax & 0xFF
        t1 = (ax >> 8) & 0xFF
        
        # Invert transform for positions 0 and 1 (ecx=0x10 and 0xF)
        s0 = invert_transform(t0, 0x10)
        s1 = invert_transform(t1, 0x0F)
        
        if s0 is None or s1 is None:
            continue
        if not (0x21 <= s0 <= 0x7A and 0x21 <= s1 <= 0x7A):
            continue
        
        # Build full serial (positions 6-10 can be anything printable)
        extra = [random.randint(0x21, 0x7A) for _ in range(5)]
        serial = bytes([s0, s1] + raw + extra).decode('latin-1')
        
        if verify(name, serial):
            return serial
    
    return None



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
