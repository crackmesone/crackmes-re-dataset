import struct
import ctypes

# TEA key from keygen
TEA_KEY = bytes([0xDF, 0x10, 0xDB, 0x04, 0x06, 0xEE, 0x9D, 0x16,
                 0xF1, 0xB8, 0xEB, 0x16, 0xE4, 0xB2, 0xAC, 0xAC])

# Fixed first 24 bytes of pass_b
PASS_B_PREFIX = bytes([0xFA, 0x91, 0xCF, 0x7F, 0xB0, 0x4F, 0x11, 0x6E,
                       0xF5, 0x07, 0x3F, 0xD5, 0x77, 0x41, 0xBC, 0x20,
                       0x20, 0xEB, 0x17, 0x86, 0xD7, 0xCB, 0xE2, 0xC8])


def u32(x):
    return x & 0xFFFFFFFF


def crc32(buff):
    """CRC32 as implemented in the keygen (same as standard CRC32)."""
    crc = 0xFFFFFFFF
    for byte in buff:
        tmp = byte ^ (crc & 0xFF)
        for _ in range(8):
            if tmp & 1:
                tmp = (tmp >> 1) ^ 0xEDB88320
            else:
                tmp >>= 1
        crc = (crc >> 8) ^ tmp
    return u32(~crc)


def first_mod(inp_words):
    """FirstMod: operates on 16 WORDs (32 bytes)."""
    result = []
    for w in inp_words:
        w = u32(w) & 0xFFFF
        w = (((w + 0x5354) & 0xFFFF) ^ 0x740A) & 0xFFFF
        w = ((w - 0xCC00) & 0xFFFF) ^ 0x04EB
        result.append(w & 0xFFFF)
    return result


def second_mod(inp_words):
    """SecondMod: operates on 16 WORDs (32 bytes)."""
    result = []
    for w in inp_words:
        w = u32(w) & 0xFFFF
        w = (((w + 0x7A53) & 0xFFFF) ^ 0x04EB) & 0xFFFF
        w = ((w - 0xE0EA) & 0xFFFF) ^ 0x20CD
        result.append(w & 0xFFFF)
    return result


def third_mod(inp_bytes):
    """ThirdMod: ROT13 on letters, operates on first 32 bytes."""
    result = bytearray(inp_bytes)
    for i in range(0x20):
        c = result[i]
        if 0x41 <= c < 0x5B:  # uppercase
            c -= 0x41
            c = (c + 0x0D) % 0x1A
            c += 0x41
            result[i] = c
        elif 0x61 <= c < 0x7B:  # lowercase
            c -= 0x61
            c = (c + 0x0D) % 0x1A
            c += 0x61
            result[i] = c
    return bytes(result)


def fourth_mod(inp_bytes):
    """FourthMod: complement/invert chars in specific ranges."""
    result = bytearray(inp_bytes)
    for i in range(0x20):
        c = result[i]
        if 0x30 <= c < 0x3A:   # digits
            result[i] = 0x69 - c
        elif 0x41 <= c < 0x5B: # uppercase
            result[i] = 0x9B - c
        elif 0x61 <= c < 0x7B: # lowercase
            result[i] = 0xDB - c
    return bytes(result)


def dec_tea(v0, v1, key_dwords, rounds=0x20):
    """TEA decryption."""
    DELTA = 0x9E3779B9
    d = u32(rounds * DELTA)
    for _ in range(rounds):
        v2 = u32(((v1 << 4) + key_dwords[2]) ^ (v1 + d) ^ ((v1 >> 5) + key_dwords[3]))
        v0 = u32(v0 - v2)
        v2 = u32(((v0 << 4) + key_dwords[0]) ^ (v0 + d) ^ ((v0 >> 5) + key_dwords[1]))
        v1 = u32(v1 - v2)
        d = u32(d - DELTA)
    return v0, v1


def enc_tea(v0, v1, key_dwords, rounds=0x20):
    """TEA encryption (inverse of decryption, for keygen)."""
    DELTA = 0x9E3779B9
    d = 0
    for _ in range(rounds):
        d = u32(d + DELTA)
        v0 = u32(v0 + (((v1 << 4) + key_dwords[0]) ^ (v1 + d) ^ ((v1 >> 5) + key_dwords[1])))
        v1 = u32(v1 + (((v0 << 4) + key_dwords[2]) ^ (v0 + d) ^ ((v0 >> 5) + key_dwords[3])))
    return v0, v1


def words_to_bytes(words):
    result = b''
    for w in words:
        result += struct.pack('<H', w & 0xFFFF)
    return result


def bytes_to_words(data):
    return list(struct.unpack('<' + 'H' * (len(data) // 2), data))


def bytes_to_dwords(data):
    return list(struct.unpack('<' + 'I' * (len(data) // 4), data))


def dwords_to_bytes(dwords):
    return struct.pack('<' + 'I' * len(dwords), *dwords)


def apply_tea_decrypt_all(data_32bytes):
    """Apply TEA decryption to 4 pairs of DWORDs (32 bytes total)."""
    key_dwords = bytes_to_dwords(TEA_KEY)
    result = bytearray(32)
    for i in range(4):
        offset = i * 8
        v0, v1 = struct.unpack('<II', data_32bytes[offset:offset+8])
        v0, v1 = dec_tea(v0, v1, key_dwords, 0x20)
        struct.pack_into('<II', result, offset, v0, v1)
    return bytes(result)


def apply_tea_encrypt_all(data_32bytes):
    """Apply TEA encryption to 4 pairs of DWORDs (32 bytes total)."""
    key_dwords = bytes_to_dwords(TEA_KEY)
    result = bytearray(32)
    for i in range(4):
        offset = i * 8
        v0, v1 = struct.unpack('<II', data_32bytes[offset:offset+8])
        v0, v1 = enc_tea(v0, v1, key_dwords, 0x20)
        struct.pack_into('<II', result, offset, v0, v1)
    return bytes(result)


def inverse_first_mod(inp_words):
    """Inverse of FirstMod."""
    result = []
    for w in inp_words:
        w = w & 0xFFFF
        # w = (((orig + 0x5354) ^ 0x740A) - 0xCC00) ^ 0x4EB
        # reverse:
        w = w ^ 0x04EB
        w = (w + 0xCC00) & 0xFFFF
        w = w ^ 0x740A
        w = (w - 0x5354) & 0xFFFF
        result.append(w)
    return result


def inverse_second_mod(inp_words):
    """Inverse of SecondMod."""
    result = []
    for w in inp_words:
        w = w & 0xFFFF
        # w = (((orig + 0x7A53) ^ 0x4EB) - 0xE0EA) ^ 0x20CD
        # reverse:
        w = w ^ 0x20CD
        w = (w + 0xE0EA) & 0xFFFF
        w = w ^ 0x04EB
        w = (w - 0x7A53) & 0xFFFF
        result.append(w)
    return result


def inverse_third_mod(inp_bytes):
    """Inverse of ThirdMod (ROT13 is its own inverse)."""
    return third_mod(inp_bytes)


def inverse_fourth_mod(inp_bytes):
    """Inverse of FourthMod (it is self-inverse for the same ranges)."""
    return fourth_mod(inp_bytes)


def name_to_pass_internal(name_str):
    """
    Given a name (up to 32 chars), produce the internal 32-byte pass buffer
    that the crackme stores after all transformations.
    The crackme reads name, converts characters:
      - if uppercase [A-Z]: subtract value from 0x9B (FourthMod inverse)
      - if lowercase [a-z]: subtract value from 0xDB
      - if digit [0-9]: subtract from 0x69
    then inverse ROT13 (ThirdMod inverse)
    etc.
    
    Actually from the keygen Generate():
      pass starts as pass_b (fixed 24 bytes + 8 random bytes)
      key = CRC(pass, 32)
      FirstMod(pass) as WORDs
      DecTEA x4 on pass
      SecondMod(pass) as WORDs
      ThirdMod(pass) as chars
      FourthMod(pass) as chars
      -> display as name, key as serial
    
    So verify(name, serial):
      - Apply inverse of the transformation pipeline to name to get pass
      - Compute CRC32 of pass
      - Check CRC32 == serial
    """
    # name is the displayed result of FourthMod(ThirdMod(SecondMod(DecTEA(FirstMod(pass)))))
    # We need to reverse to get pass
    name_bytes = name_str.encode('latin-1') if isinstance(name_str, str) else name_str
    # Pad to 32 bytes
    name_bytes = name_bytes[:32].ljust(32, b'\x00')
    
    # Step 1: inverse FourthMod
    step1 = inverse_fourth_mod(name_bytes)
    # Step 2: inverse ThirdMod
    step2 = inverse_third_mod(step1)
    # Step 3: inverse SecondMod (on WORDs)
    words = bytes_to_words(step2)
    step3_words = inverse_second_mod(words)
    step3 = words_to_bytes(step3_words)
    # Step 4: inverse DecTEA = EncTEA
    step4 = apply_tea_encrypt_all(step3)
    # Step 5: inverse FirstMod (on WORDs)
    words2 = bytes_to_words(step4)
    step5_words = inverse_first_mod(words2)
    step5 = words_to_bytes(step5_words)
    return step5


def verify(name, serial):
    """
    Verify name/serial pair.
    serial should be an integer (DWORD) or string representation of one.
    """
    if isinstance(serial, str):
        try:
            serial_int = int(serial)
        except ValueError:
            return False
    else:
        serial_int = int(serial)
    
    serial_int = u32(serial_int)
    
    # Recover the internal pass buffer from name
    try:
        pass_buf = name_to_pass_internal(name)
    except Exception:
        return False
    
    # Compute CRC32 of pass (32 bytes)
    computed_crc = crc32(pass_buf)
    
    return computed_crc == serial_int


def keygen(name=None):
    """
    Generate a valid (name, serial) pair.
    
    From Generate() in keygen.cpp:
      pass = pass_b[:24] + 8 random bytes + null terminator
      key = CRC32(pass, 32)
      FirstMod(pass as WORDs)
      DecTEA x4
      SecondMod(pass as WORDs)
      ThirdMod(pass)
      FourthMod(pass)
      -> name = pass[:32] as string, serial = key
    
    If name is provided, we reverse-engineer the serial from it.
    If name is None, we generate a fresh pair.
    """
    import random
    
    if name is not None:
        # Given a name, compute the serial
        pass_buf = name_to_pass_internal(name)
        serial = crc32(pass_buf)
        return str(serial)
    else:
        # Generate fresh pair from pass_b + random last 8 bytes
        pass_buf = bytearray(33)
        pass_buf[:24] = PASS_B_PREFIX
        for i in range(24, 32):
            pass_buf[i] = random.randint(0, 255)
        
        key = crc32(pass_buf[:32])
        
        # FirstMod
        words = bytes_to_words(bytes(pass_buf[:32]))
        words = first_mod(words)
        data = words_to_bytes(words)
        
        # DecTEA x4
        key_dwords = bytes_to_dwords(TEA_KEY)
        result = bytearray(32)
        for i in range(4):
            offset = i * 8
            v0, v1 = struct.unpack('<II', data[offset:offset+8])
            v0, v1 = dec_tea(v0, v1, key_dwords, 0x20)
            struct.pack_into('<II', result, offset, v0, v1)
        data = bytes(result)
        
        # SecondMod
        words2 = bytes_to_words(data)
        words2 = second_mod(words2)
        data = words_to_bytes(words2)
        
        # ThirdMod
        data = third_mod(data)
        
        # FourthMod
        data = fourth_mod(data)
        
        generated_name = data.decode('latin-1', errors='replace').rstrip('\x00')
        return generated_name, str(key)



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
