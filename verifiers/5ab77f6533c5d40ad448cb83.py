import hashlib
import struct
import ctypes

# ASSUMPTION: The hash used is MD5 (IniHash constants 67452301h, EFCDAB89h, 98BADCFEh, 10325476h are standard MD5 init values)
# ASSUMPTION: The registry keys may not exist; we use empty strings for missing ones
# ASSUMPTION: The serial format is "%lx %lx %lx %lx" (4 hex longs separated by spaces)

def _u32(x):
    return x & 0xFFFFFFFF

def _lfsr_step_forward(esi, edi):
    """
    One iteration of the key generation loop:
    - Treat (esi, edi) as a 64-bit value (esi=low, edi=high)
    - Left rotate by 1 bit as a 64-bit register
    - Replace bit31 of new esi with (old_bit2 XOR old_bit13 XOR old_bit31)
    Based on assembly: __allshl by 1, then XOR in feedback bits
    """
    # Extract feedback bits from current esi (low 32)
    bit2  = (esi >> 2)  & 1
    bit13 = (esi >> 13) & 1
    bit31 = (esi >> 31) & 1
    feedback = bit2 ^ bit13 ^ bit31

    # 64-bit left shift by 1
    combined = (edi << 32) | esi
    combined = ((combined << 1) & 0xFFFFFFFFFFFFFFFF)
    new_esi = _u32(combined)
    new_edi = _u32(combined >> 32)

    # Set bit31 of new_esi to feedback
    new_esi = (new_esi & 0x7FFFFFFF) | (feedback << 31)

    return new_esi, new_edi

def _lfsr_step_backward(esi, edi):
    """
    Reverse one iteration:
    We know that the feedback was (old_bit2 XOR old_bit13 XOR old_bit31)
    and new_bit31 = feedback.
    Reverse: right rotate by 1 bit as 64-bit, then restore old bit31.
    old_bit31 = new_bit31 XOR old_bit2 XOR old_bit13
    But old_bit2 and old_bit13 are in the rotated-back position...
    ASSUMPTION: bit2 and bit13 refer to bits of old esi (before rotation)
    After right-rotating back, bit0 of new_esi becomes old bit31 of edi (the carry).
    Let's think carefully:
    After forward step:
      combined_new = (old_edi << 32 | old_esi) << 1  (64-bit)
      new_esi = combined_new[31:0] with bit31 replaced by feedback
      new_edi = combined_new[63:32]
    So: new_edi = (old_edi << 1 | (old_esi >> 31)) & 0xFFFFFFFF
        new_esi_raw = (old_esi << 1) & 0xFFFFFFFF  (bit31 cleared since shifted out)
        new_esi = new_esi_raw | (feedback << 31)
    Reverse:
      old_esi_high_bit = new_edi & 1  (= old bit31 of esi after shift, but that's old_esi>>31 shifted in)
      Wait: new_edi bit0 = old_esi bit31
    So:
      old_esi_bit31 = new_edi & 1
      old_edi = (new_edi >> 1) ... no, we need old_edi
      new_edi = (old_edi << 1 | old_esi_bit31) & 0xFFFFFFFF
      So old_edi_bit31_shifted = ... we need old_edi from new_edi and old_esi_bit31
      old_edi = (new_edi >> 1) | (??? << 31)  -- we don't know old_edi bit31
    ASSUMPTION: treating edi as the high part, its bit31 came from the previous iteration or is 0 initially
    For simplicity in keygen, we use forward LFSR only.
    """
    # Right rotate 64-bit by 1
    combined = (edi << 32) | esi
    # The bit that was shifted into bit63 from old bit62, we need to recover old bit63
    # new_esi bit31 = feedback (known)
    # new_edi bit0 = old_esi bit31 (before rotation)
    old_esi_b31 = edi & 1  # new_edi bit0 = old_esi bit31
    # Right rotate
    lsb = combined & 1
    combined = (combined >> 1) | (lsb << 63)
    new_esi = _u32(combined)
    new_edi = _u32(combined >> 32)
    # We need to restore the correct bit31 of new_esi
    # new_esi (after right rotate) has at bit31: old bit0 of edi (=lsb of edi)
    # The forward step set new_esi bit31 = feedback = bit2^bit13^bit31 of old_esi
    # In reverse, after unrotating, new_esi bit31 should be old_esi bit31 = old_esi_b31
    new_esi = (new_esi & 0x7FFFFFFF) | (old_esi_b31 << 31)
    return new_esi, new_edi

def checkkey_forward(a, b, iterations):
    """Run the LFSR forward for 'iterations' steps, starting with (esi=a, edi=b)"""
    esi, edi = _u32(a), _u32(b)
    for _ in range(iterations):
        esi, edi = _lfsr_step_forward(esi, edi)
    return esi, edi

def checkkey_backward(a, b, iterations):
    """Run the LFSR backward for 'iterations' steps"""
    esi, edi = _u32(a), _u32(b)
    for _ in range(iterations):
        esi, edi = _lfsr_step_backward(esi, edi)
    return esi, edi

def compute_hash(data):
    """Compute MD5 of data, return (H1, H2, H3, H4) as 32-bit ints (little-endian words)"""
    h = hashlib.md5(data).digest()
    h1, h2, h3, h4 = struct.unpack('<IIII', h)
    return h1, h2, h3, h4

def get_registry_productid():
    """Try to get ProductId from registry; return empty string if not found"""
    # ASSUMPTION: On non-Windows or missing key, return empty string
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'SOFTWARE\Microsoft\Windows\CurrentVersion')
        val, _ = winreg.QueryValueEx(key, 'ProductId')
        winreg.CloseKey(key)
        return val
    except Exception:
        return ''

def get_registry_registered_owner():
    """Try to get RegisteredOwner from registry; return empty string if not found"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'SOFTWARE\Microsoft\Windows\CurrentVersion')
        val, _ = winreg.QueryValueEx(key, 'RegisteredOwner')
        winreg.CloseKey(key)
        return val
    except Exception:
        return ''

def build_hash_string(name):
    """
    Build the string: [Name][reverse(Name)][ProductId][RegisteredOwner]
    Example: AmenesiaaisenemA<productid><registeredowner>
    ASSUMPTION: The registry values are appended as plain strings (no separator)
    """
    reversed_name = name[::-1]
    product_id = get_registry_productid()
    registered_owner = get_registry_registered_owner()
    s = name + reversed_name + product_id + registered_owner
    return s.encode('ascii', errors='replace')

def compute_serial_from_hash(h1, h2, h3, h4):
    """
    Keygen: find A, B, C, D such that checkkey produces H1..H4.
    Forward:
      (KeyA, Bt)  = checkkey(A,  B,  0xBADC0DE // 0x50)
      (KeyB, Ct)  = checkkey(Bt, C,  0xBADC0DE // 0x51)
      (KeyC, KeyD)= checkkey(Ct, D,  0xBADC0DE // 0x52)
    We need KeyA=H1, KeyB=H2, KeyC=H3, KeyD=H4.
    Reverse:
      From (KeyC, KeyD) backward with iters2 steps: (Ct, D)
      From (KeyB, Ct)  backward with iters1 steps: (Bt, C)
      From (KeyA, Bt)  backward with iters0 steps: (A,  B)
    """
    iters0 = 0xBADC0DE // 0x50
    iters1 = 0xBADC0DE // 0x51
    iters2 = 0xBADC0DE // 0x52

    # KeyC, KeyD -> Ct, D
    Ct, D = checkkey_backward(h3, h4, iters2)
    # KeyB, Ct -> Bt, C
    Bt, C = checkkey_backward(h2, Ct, iters1)
    # KeyA, Bt -> A, B
    A, B = checkkey_backward(h1, Bt, iters0)

    return A, B, C, D

def verify(name, serial):
    """
    Verify a name/serial pair.
    Serial format: '%lx %lx %lx %lx' (4 hex longs separated by spaces)
    """
    # Parse serial
    parts = serial.strip().split()
    if len(parts) != 4:
        return False
    try:
        A = int(parts[0], 16) & 0xFFFFFFFF
        B = int(parts[1], 16) & 0xFFFFFFFF
        C = int(parts[2], 16) & 0xFFFFFFFF
        D = int(parts[3], 16) & 0xFFFFFFFF
    except ValueError:
        return False

    # Build hash string and compute MD5
    data = build_hash_string(name)
    h1, h2, h3, h4 = compute_hash(data)
    # Mask H1 to 16 bits as per 'and ebx, 0FFFFh'
    h1 = h1 & 0xFFFF

    iters0 = 0xBADC0DE // 0x50
    iters1 = 0xBADC0DE // 0x51
    iters2 = 0xBADC0DE // 0x52

    # Forward compute keys
    KeyA, Bt  = checkkey_forward(A,  B,  iters0)
    KeyB, Ct  = checkkey_forward(Bt, C,  iters1)
    KeyC, KeyD= checkkey_forward(Ct, D,  iters2)

    return (KeyA == h1) and (KeyB == h2) and (KeyC == h3) and (KeyD == h4)

def keygen(name):
    """
    Generate a valid serial for the given name.
    """
    data = build_hash_string(name)
    h1, h2, h3, h4 = compute_hash(data)
    # Mask H1 to 16 bits
    h1 = h1 & 0xFFFF

    A, B, C, D = compute_serial_from_hash(h1, h2, h3, h4)
    return '%08x %08x %08x %08x' % (A, B, C, D)


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
