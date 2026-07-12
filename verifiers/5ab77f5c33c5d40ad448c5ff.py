import random
import ctypes

# Allowed characters (from keygen source)
ALLOWED = 'abcdefghijklnopqrstuvxyz1234567890'

# Helper: sign-extend byte to 32-bit signed int
def movsx_byte(b):
    b = b & 0xFF
    if b >= 0x80:
        return b - 0x100
    return b

# Helper: wrap to 32-bit signed
def s32(x):
    x = x & 0xFFFFFFFF
    if x >= 0x80000000:
        return x - 0x100000000
    return x

def u32(x):
    return x & 0xFFFFFFFF

def ror32(val, count):
    val = u32(val)
    count = count % 32
    return u32((val >> count) | (val << (32 - count)))

def shr32(val, count):
    return u32(val) >> count

# --- Hash for serial2 (used in algo1 check) ---
# From keygen.asm generate_1 / assembly listing:
# lea eax, [szSerial2]
# movsx ebx, byte[eax]   ; ebx = sign_ext(s2[0])
# neg ebx
# inc eax
# xor bl, byte[eax]      ; bl ^= s2[1]
# add ebx, ebx
# neg ebx
# loop: (eax starts at s2[1])
#   inc eax
#   xor bh, byte[eax]
#   xor bh, bl    -- WAIT: source says xor bl, bh then add bl, bh add bl, bl add ebx, ebx
# Actually from 004012C1 (algo for serial2 which is checked first):
# But wait - the FIRST algo at 004012C1 uses the SECOND key box buffer.
# Let's re-read carefully:
#
# Algo for serial2 (stored in sn2_hash at 403278):
# From Keygen.asm sn2_hash computation:
#   movsx ebx, byte[eax=s2]   ebx = se(s2[0])
#   neg ebx
#   inc eax   -> eax = &s2[1]
#   xor bl, byte[eax]   bl ^= s2[1]
#   add ebx, ebx
#   neg ebx
#   loop (eax starts at s2[1]):
#     inc eax
#     xor bh, byte[eax]
#     xor bh, bl   -- ASSUMPTION: keygen source doesn't have xor bl,bh here for sn2
#     add ebx, ebx
#     if byte[eax+1] != 0: continue

def hash_serial2(s):
    """Compute sn2_hash from serial2 (10 chars)."""
    data = [ord(c) for c in s]
    ebx = movsx_byte(data[0])
    ebx = s32(-ebx)  # neg
    # eax -> index 1
    bl = ebx & 0xFF
    bl = (bl ^ data[1]) & 0xFF
    ebx = (ebx & 0xFFFFFF00) | bl
    ebx = s32(ebx + ebx)  # add ebx,ebx
    ebx = s32(-ebx)        # neg ebx
    # loop from index 1
    for i in range(2, 10):  # indices 2..9
        bh = (u32(ebx) >> 8) & 0xFF
        bl = u32(ebx) & 0xFF
        bh = (bh ^ data[i]) & 0xFF
        # From keygen sn2 loop: xor bh, bl is present
        # ASSUMPTION: xor bh, bl based on keygen source line
        bh = (bh ^ bl) & 0xFF
        ebx = (u32(ebx) & 0xFFFF0000) | (bh << 8) | bl
        ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    return u32(ebx)

# --- Hash for serial1 ---
# From keygen.asm generate_1 serial1 hash:
#   movsx ebx, byte[s1[0]]
#   dec ebx
#   inc eax -> s1[1]
#   xor bl, byte[s1[1]]
#   add ebx, ebx
#   dec ebx
#   loop from s1[1]:
#     inc eax
#     xor bh, byte[eax]
#     xor bl, bh
#     add bl, bh
#     add bl, bl
#     add ebx, ebx
#     if byte[eax+1] != 0: continue
def hash_serial1(s):
    """Compute hash from serial1 (10 chars)."""
    data = [ord(c) for c in s]
    ebx = movsx_byte(data[0])
    ebx = s32(ebx - 1)  # dec ebx
    # eax -> index 1
    bl = ebx & 0xFF
    bl = (bl ^ data[1]) & 0xFF
    ebx = (ebx & 0xFFFFFF00) | bl
    ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    ebx = s32(ebx - 1)  # dec ebx
    # loop from index 1
    for i in range(2, 10):
        bh = (u32(ebx) >> 8) & 0xFF
        bl = u32(ebx) & 0xFF
        bh = (bh ^ data[i]) & 0xFF  # xor bh, byte[eax]
        bl = (bl ^ bh) & 0xFF        # xor bl, bh
        bl = (bl + bh) & 0xFF        # add bl, bh
        bl = (bl + bl) & 0xFF        # add bl, bl
        ebx = (u32(ebx) & 0xFFFF0000) | (bh << 8) | bl
        ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    return u32(ebx)

def check_s1_s2(s1, s2):
    """Check that serial1 and serial2 are related correctly.
    From asm:
      sn2_hash stored at [403278]
      After computing s1 hash into ebx:
        ror ebx, 1
        shr ebx, 1
        xor bl, ah   (ah = high byte of sn2_hash low word)
        cmp bl, 0xAA
    """
    if len(s1) != 10 or len(s2) != 10:
        return False
    sn2 = hash_serial2(s2)
    s1h = hash_serial1(s1)
    ebx = s1h
    ebx = ror32(ebx, 1)
    ebx = shr32(ebx, 1)
    # xor bl, ah  where eax = sn2_hash
    ah = (sn2 >> 8) & 0xFF
    bl = ebx & 0xFF
    bl = (bl ^ ah) & 0xFF
    return bl == 0xAA

# --- Hash for serial3 ---
# From keygen.asm generate_2:
#   movsx ebx, byte[s3[0]]
#   neg ebx
#   shr ebx, 2
#   add ebx, ebx
#   inc eax -> s3[1]
#   xor bl, byte[s3[1]]
#   add ebx, ebx
#   neg ebx
#   loop from s3[1]:
#     inc eax
#     xor bh, byte[eax]
#     xor bh, bl
#     add ebx, ebx
#     if byte[eax+1] != 0: continue
#   ror ebx, 2
#   cmp bx, 0xAA00
def hash_serial3(s):
    data = [ord(c) for c in s]
    ebx = movsx_byte(data[0])
    ebx = s32(-ebx)              # neg
    ebx = s32(u32(ebx) >> 2)    # shr ebx, 2 (logical)
    # ASSUMPTION: shr on possibly negative - treating as logical (unsigned) shift
    ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    bl = u32(ebx) & 0xFF
    bl = (bl ^ data[1]) & 0xFF  # xor bl, byte[s3[1]]
    ebx = (u32(ebx) & 0xFFFFFF00) | bl
    ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    ebx = s32(-ebx)              # neg ebx
    for i in range(2, 10):
        bh = (u32(ebx) >> 8) & 0xFF
        bl = u32(ebx) & 0xFF
        bh = (bh ^ data[i]) & 0xFF  # xor bh, byte[eax]
        bh = (bh ^ bl) & 0xFF        # xor bh, bl
        ebx = (u32(ebx) & 0xFFFF0000) | (bh << 8) | bl
        ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    ebx = ror32(ebx, 2)
    return u32(ebx)

def check_s3(s3):
    if len(s3) != 10:
        return False
    h = hash_serial3(s3)
    bx = h & 0xFFFF
    return bx == 0xAA00

# --- Hash for serial4 ---
# From keygen.asm generate_3:
#   movsx ebx, byte[s4[0]]
#   neg ebx
#   sub bh, bh
#   shl ebx, 2
#   sub bh, bh
#   rol ebx, 4
#   inc eax -> s4[1]
#   xor bl, byte[s4[1]]
#   add ebx, ebx
#   neg ebx
#   loop from s4[1]:
#     inc eax
#     xor bh, byte[eax]
#     add ebx, ebx
#     if byte[eax+1] != 0: continue
#   cmp bh, 0x1E
def rol32(val, count):
    val = u32(val)
    count = count % 32
    return u32((val << count) | (val >> (32 - count)))

def hash_serial4(s):
    data = [ord(c) for c in s]
    ebx = movsx_byte(data[0])
    ebx = s32(-ebx)             # neg ebx
    # sub bh, bh  -> zero out BH (bits 8-15)
    ebx = u32(ebx) & 0xFFFF00FF
    ebx = u32(ebx) << 2         # shl ebx, 2
    ebx = ebx & 0xFFFFFFFF
    # sub bh, bh again
    ebx = ebx & 0xFFFF00FF
    ebx = rol32(ebx, 4)         # rol ebx, 4
    bl = ebx & 0xFF
    bl = (bl ^ data[1]) & 0xFF  # xor bl, byte[s4[1]]
    ebx = (ebx & 0xFFFFFF00) | bl
    ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    ebx = s32(-ebx)             # neg ebx
    for i in range(2, 10):
        bh = (u32(ebx) >> 8) & 0xFF
        bh = (bh ^ data[i]) & 0xFF  # xor bh, byte[eax]
        ebx = (u32(ebx) & 0xFFFF00FF) | (bh << 8)
        ebx = s32(u32(ebx) + u32(ebx))  # add ebx, ebx
    bh = (u32(ebx) >> 8) & 0xFF
    return bh

def check_s4(s4):
    if len(s4) != 10:
        return False
    return hash_serial4(s4) == 0x1E

def verify(name, serial):
    """
    The crackme has 4 serial boxes (not name-based).
    Serial format: s1-s2-s3-s4 (each 10 chars, separated by '-').
    NOTE: 'name' parameter is ignored - the crackme is serial-only.
    """
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    s1, s2, s3, s4 = parts
    if len(s1) != 10 or len(s2) != 10 or len(s3) != 10 or len(s4) != 10:
        return False
    # Check s1+s2 relationship
    if not check_s1_s2(s1, s2):
        return False
    # Check s3
    if not check_s3(s3):
        return False
    # Check s4
    if not check_s4(s4):
        return False
    return True

def keygen(name=None):
    """Generate a valid serial by brute-forcing each component."""
    chars = ALLOWED
    
    def rand_str(n=10):
        return ''.join(random.choice(chars) for _ in range(n))
    
    # Find valid s3
    s3 = None
    for _ in range(1000000):
        candidate = rand_str()
        if check_s3(candidate):
            s3 = candidate
            break
    if s3 is None:
        raise RuntimeError("Could not find valid s3")
    
    # Find valid s4
    s4 = None
    for _ in range(1000000):
        candidate = rand_str()
        if check_s4(candidate):
            s4 = candidate
            break
    if s4 is None:
        raise RuntimeError("Could not find valid s4")
    
    # Find valid s1+s2
    s1 = s2 = None
    for _ in range(1000000):
        c1 = rand_str()
        c2 = rand_str()
        if check_s1_s2(c1, c2):
            s1, s2 = c1, c2
            break
    if s1 is None:
        raise RuntimeError("Could not find valid s1/s2")
    
    return f"{s1}-{s2}-{s3}-{s4}"


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
            print(_sv)
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
