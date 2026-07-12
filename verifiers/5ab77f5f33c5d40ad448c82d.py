import struct

# Encryption table from the writeup (32 bytes = 16 words)
ENC_DATA = bytes([
    0x10, 0x10, 0x20, 0x20,
    0x83, 0x94, 0x81, 0x12,
    0x82, 0x12, 0x11, 0x19,
    0x77, 0x07, 0x66, 0x06,
    0x28, 0x19, 0x29, 0x19,
    0x21, 0x94, 0x31, 0x94,
    0x98, 0x43, 0x81, 0x56,
    0x81, 0x65, 0x80, 0x85
])

def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def ror32(val, n):
    return rol32(val, 32 - n)

def rol16(val, n):
    val &= 0xFFFF
    n &= 15
    return ((val << n) | (val >> (16 - n))) & 0xFFFF

def ror16(val, n):
    return rol16(val, 16 - n)

def encrypt_name(name_bytes):
    """Encrypt the name (up to 16 bytes, zero-padded) using the encryption table.
    Returns a list of 16 words (stored in Buffer[2..32] as words, indexed by 2*ecx).
    """
    # Pad name to 16 bytes
    name16 = (name_bytes + b'\x00' * 16)[:16]
    result_words = [0] * 16
    for i in range(16):
        # lodsb: al = name16[i]
        eax = name16[i] & 0xFF
        # shl eax, 4
        eax = (eax << 4) & 0xFFFFFFFF
        # shr al, 4  (shift right low byte by 4)
        al = eax & 0xFF
        ah = (eax >> 8) & 0xFF
        al = (al >> 4) & 0xFF
        eax = (eax & 0xFFFFFF00) | al
        # xor al, ah
        al = al ^ ah
        eax = (eax & 0xFFFFFF00) | al
        # xor ah, ah -> ah = 0
        eax = eax & 0xFFFF00FF
        # Now eax is the index (0..15)
        idx = eax & 0xFF
        # mov bx, word ptr [EncData + 2*eax]
        bx = struct.unpack_from('<H', ENC_DATA, 2 * idx)[0]
        # Store at Buffer[2*ecx - 2] where ecx counts from 16 down to 1
        # ecx = 16 - i (starts at 16, decremented after each iteration)
        ecx = 16 - i
        result_words[ecx - 1] = bx  # index 0..15 corresponding to ecx=16..1
    return result_words

def words_to_buffer(result_words):
    """Convert list of 16 words back to 32-byte buffer.
    The assembly stores at [Buffer - 2 + 2*ecx] where ecx goes from 16..1,
    meaning indices 30,28,26,...,0 => positions 15,14,...,0 words.
    result_words[ecx-1] = word at ecx, so:
      ecx=16 -> buffer[30:32], ecx=15 -> buffer[28:30], ..., ecx=1 -> buffer[0:2]
    """
    buf = bytearray(32)
    for ecx in range(1, 17):
        w = result_words[ecx - 1]
        offset = (ecx - 1) * 2  # 2*(ecx-1)
        struct.pack_into('<H', buf, offset, w)
    return bytes(buf)

def compute_serial(name_str, start_value=0xAB12CD34):
    """Full keygen: given a name and optional start_value, return (serial1, serial2)."""
    name_bytes = name_str.encode('ascii', errors='replace')[:16]
    
    # Step 1: Encrypt name into Buffer (32 bytes = 16 words)
    result_words = encrypt_name(name_bytes)
    buf = bytearray(words_to_buffer(result_words))
    
    # Step 2: XOR buffer dwords with evolving serial, 8 dwords
    # ContinueEncryption1: for ecx=8..1, xor Buffer[4*(ecx-1)..] with eax,
    # then eax = (eax + 0x42424242) ^ 0x21212121
    eax = start_value & 0xFFFFFFFF
    for ecx in range(8, 0, -1):
        offset = (ecx - 1) * 4
        dw = struct.unpack_from('<I', buf, offset)[0]
        dw ^= eax
        struct.pack_into('<I', buf, offset, dw)
        eax = (eax + 0x42424242) & 0xFFFFFFFF
        eax ^= 0x21212121
    
    # Step 3: XOR all 8 dwords with rol3 accumulation
    # ContinueEncryption2: for ecx=8..1, eax = rol3(eax ^ Buffer[4*(ecx-1)])
    eax = 0
    for ecx in range(8, 0, -1):
        offset = (ecx - 1) * 4
        dw = struct.unpack_from('<I', buf, offset)[0]
        eax ^= dw
        eax = rol32(eax, 3)
    
    # eax is the computed value (2nd modified serial)
    # ebx = start_value (popped from stack)
    ebx = start_value & 0xFFFFFFFF
    
    # xchg ax, bx  (swap lower 16 bits)
    ax = eax & 0xFFFF
    bx = ebx & 0xFFFF
    eax = (eax & 0xFFFF0000) | bx
    ebx = (ebx & 0xFFFF0000) | ax
    
    # rol ebx, 0x10
    ebx = rol32(ebx, 16)
    # ror eax, 0x10
    eax = ror32(eax, 16)
    
    serial2 = eax
    serial1 = ebx
    return serial1, serial2

def verify(name, serial):
    """Verify name against a serial string.
    Serial expected as 'XXXXXXXX-YYYYYYYY' (two 8-hex-digit parts) or two separate values.
    Since the crackme has serial1 and serial2, we accept 'S1-S2' format.
    """
    # Parse serial
    parts = serial.strip().split('-')
    if len(parts) != 2:
        return False
    try:
        s1_input = int(parts[0], 16) & 0xFFFFFFFF
        s2_input = int(parts[1], 16) & 0xFFFFFFFF
    except ValueError:
        return False
    
    # The crackme validation:
    # Load serial1=eax, serial2=ebx
    # rol eax,16; ror ebx,16
    # xchg ax,bx (net effect of rol+ror+xor-swap on lower 16)
    # Actually the assembly does:
    #   rol eax,10h; ror ebx,10h
    #   xor ax,bx; xor bx,ax; xor ax,bx  (= xchg ax,bx)
    # This transforms the inputs. We need to check the final comparison.
    
    eax = s1_input
    ebx = s2_input
    eax = rol32(eax, 16)
    ebx = ror32(ebx, 16)
    # xchg ax, bx
    ax = eax & 0xFFFF
    bx = ebx & 0xFFFF
    eax = (eax & 0xFFFF0000) | bx
    ebx = (ebx & 0xFFFF0000) | ax
    
    # Now eax is 'modified serial1' = start_value used in keygen
    # ebx is 'modified serial2' = result to compare against
    start_value = eax
    expected_result = ebx
    
    # Encrypt name
    name_bytes = name.encode('ascii', errors='replace')[:16]
    result_words = encrypt_name(name_bytes)
    buf = bytearray(words_to_buffer(result_words))
    
    # XOR buffer with evolving start_value
    ev = start_value
    for ecx in range(8, 0, -1):
        offset = (ecx - 1) * 4
        dw = struct.unpack_from('<I', buf, offset)[0]
        dw ^= ev
        struct.pack_into('<I', buf, offset, dw)
        ev = (ev + 0x42424242) & 0xFFFFFFFF
        ev ^= 0x21212121
    
    # Accumulate with rol3
    acc = 0
    for ecx in range(8, 0, -1):
        offset = (ecx - 1) * 4
        dw = struct.unpack_from('<I', buf, offset)[0]
        acc ^= dw
        acc = rol32(acc, 3)
    
    return (acc & 0xFFFFFFFF) == expected_result

def keygen(name, start_value=0xAB12CD34):
    """Generate a valid serial for the given name."""
    s1, s2 = compute_serial(name, start_value)
    return f"{s1:08X}-{s2:08X}"


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
