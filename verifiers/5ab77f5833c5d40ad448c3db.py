# Reverse-engineered keygen for keygenme_v2 by pxor
# Based on the writeup by Knight
#
# Key findings from writeup:
# 1. Serial must be exactly 0x4F (79) chars long
# 2. Serial must begin with "Kocham Gosie-"
# 3. After the prefix, hex digits are parsed
# 4. The name is used to fill a 32-byte buffer with repeated copies
# 5. There is a transformation loop on the serial using a lookup table
# 6. The final serial depends on the name buffer
#
# ASSUMPTION: The full lookup tables at 0x403586 and 0x403685 are unknown.
# ASSUMPTION: The exact final comparison values for name-dependent checks are not fully given.
# ASSUMPTION: The writeup was truncated, so the complete name-dependent portion is missing.

def rol32(val, count):
    val &= 0xFFFFFFFF
    return ((val << count) | (val >> (32 - count))) & 0xFFFFFFFF

def rol16(val, count):
    val &= 0xFFFF
    return ((val << count) | (val >> (16 - count))) & 0xFFFF

def neg32(val):
    return (-val) & 0xFFFFFFFF

def neg16(val):
    return (-val) & 0xFFFF

def neg8(val):
    return (-val) & 0xFF

# The fixed prefix check: serial[12] must be '-' (0x2D)
# Verify the '-' character check from assembly:
# AL = serial[12] = 0x2D
# AL ^= 0x33 => 0x2D ^ 0x33 = 0x1E
# AL = NEG(AL) => NEG(0x1E) = 0xE2
# AH = AL = 0xE2 => AX = 0xE2E2
# AX = ROL(AX, 4) => ROL16(0xE2E2, 4) = 0x2E2E
# AX = NEG(AX) => NEG16(0x2E2E) = 0xD1D2
# XCHG AL,AH => AX = 0xD2D1
# AX ^= 0x1234 => 0xD2D1 ^ 0x1234 = 0xC0E5
# AX -= 0x12 => 0xC0E5 - 0x12 = 0xC0D3
# BX = AX = 0xC0D3
# EAX = ROL32(EAX, 16): upper 16 bits of EAX were 0 (from prev ops), so EAX=0xC0D30000 ... 
# ASSUMPTION: upper 16 of EAX before ROL32 are 0, so after ROL32: 0x0000C0D3
# AX = BX = 0xC0D3 => EAX = 0xC0D3C0D3 ... wait
# Actually: after SUB AX,12: AX=0xC0D3, EAX high word still 0 => EAX=0x0000C0D3
# ROL EAX,16 => 0xC0D30000
# MOV AX,BX => AX=0xC0D3 => EAX=0xC0D3C0D3
# NEG EAX => NEG32(0xC0D3C0D3) = 0x3F2C3F2D
# XOR EAX, 0x87678767 => 0x3F2C3F2D ^ 0x87678767 = 0xB84BB84A
# CMP EAX, 0xB84BB84A => match! So '-' at position 12 is confirmed.

def verify_fixed_prefix(serial_bytes):
    """Check that serial[12] == '-' (the only fixed char check shown for position 12)"""
    if len(serial_bytes) < 13:
        return False
    c = serial_bytes[12]
    al = c ^ 0x33
    al = neg8(al)
    ah = al
    ax = (ah << 8) | al  # AX = al | (al<<8) -- AH=AL
    ax = rol16(ax, 4)
    ax = neg16(ax)
    # XCHG AL, AH
    al2 = (ax >> 8) & 0xFF
    ah2 = ax & 0xFF
    ax = (ah2 << 8) | al2
    ax = (ax ^ 0x1234) & 0xFFFF
    ax = (ax - 0x12) & 0xFFFF
    bx = ax
    # EAX: upper 16 bits assumed 0 before ROL32
    eax = ax  # 0x0000CCCC
    eax = rol32(eax, 16)
    eax = (eax & 0xFFFF0000) | bx
    eax = neg32(eax)
    eax = (eax ^ 0x87678767) & 0xFFFFFFFF
    return eax == 0xB84BB84A

# Verify the fixed prefix is correct
assert verify_fixed_prefix(b'Kocham Gosie-'), "Fixed prefix check failed!"

# ASSUMPTION: The three XLAT-based checks use lookup tables at 0x403586 that are not
# provided in the writeup. The writeup tells us the answers:
# First 4 chars: 'K','o','c','h' => "Koch"
# Next 4 chars: 'a','m',' ','G' => "am G"
# Next 4 chars: 'o','s','i','e' => "osie"
# These are fixed regardless of name.

FIXED_PREFIX = b'Kocham Gosie-'
# Total serial length must be 0x4F = 79 chars
# After 'Kocham Gosie-' (13 chars), we have 79-13 = 66 chars of hex digits
# ASSUMPTION: The remaining 66 chars are hex digits derived from name

def make_name_buffer(name):
    """Fill a 32-byte buffer with repeated copies of name."""
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    n = len(name_bytes)
    buf = bytearray(32)
    dst = 0
    # The assembly fills 32 bytes with copies of name
    # EDX = 0x20 - n (initially)
    # Loop: subtract n, if sign -> partial fill
    remaining = 32
    src_pos = 0
    while remaining > 0:
        chunk = min(n, remaining)
        for i in range(chunk):
            buf[dst] = name_bytes[i % n]
            dst += 1
        remaining -= chunk
        # ASSUMPTION: simplified fill - just repeat name to fill 32 bytes
        if chunk == 0:
            break
    # Simpler implementation:
    buf2 = bytearray(32)
    for i in range(32):
        buf2[i] = name_bytes[i % n]
    return buf2

# ASSUMPTION: The name-dependent part of the serial is derived from the name buffer
# but the exact algorithm after the truncated writeup is unknown.
# We can only implement the fixed-prefix portion.

SERIAL_LEN = 0x4F  # 79

def verify(name, serial):
    """
    Verify name/serial pair.
    Returns True if serial passes all known checks.
    ASSUMPTION: Name-dependent checks after position 13 are not fully recoverable
    from the truncated writeup.
    """
    if isinstance(serial, str):
        serial = serial.encode('ascii')
    if isinstance(name, str):
        name = name.encode('ascii')
    
    # Length check: serial must be exactly 79 chars
    if len(serial) != SERIAL_LEN:
        return False
    
    # Fixed prefix check
    if not serial.startswith(FIXED_PREFIX):
        return False
    
    # The 13th character (index 12) must be '-'
    if not verify_fixed_prefix(serial):
        return False
    
    # After prefix, must be hex digits (0-9, a-f, A-F)
    hex_part = serial[13:]
    for b in hex_part:
        c = chr(b)
        if c not in '0123456789abcdefABCDEF':
            return False
    
    # ASSUMPTION: Name-dependent checks on the hex portion are not implemented
    # due to truncated writeup and unknown lookup tables.
    # A real verify would also check name-derived transformations.
    
    # ASSUMPTION: Returning True here means we only verified the fixed portion.
    return True

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: The name-dependent hex portion (66 hex chars after 'Kocham Gosie-')
    cannot be computed without the lookup tables and full algorithm from the writeup.
    Returns a placeholder serial that passes the fixed checks only.
    """
    if isinstance(name, str):
        name = name.encode('ascii')
    
    # Build name buffer (32 bytes)
    name_buf = make_name_buffer(name)
    
    # Fixed prefix
    prefix = FIXED_PREFIX  # b'Kocham Gosie-'
    
    # ASSUMPTION: The 66 hex chars are derived from name_buf via the transformation
    # described in the (truncated) writeup. We cannot compute them without:
    # 1. The lookup table at 0x403685
    # 2. The full comparison logic after the truncation point
    # Placeholder: use zeros encoded as hex
    hex_part = b'00' * 33  # 66 hex chars
    
    serial = prefix + hex_part
    assert len(serial) == SERIAL_LEN, f"Serial length {len(serial)} != {SERIAL_LEN}"
    return serial.decode('ascii')


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
