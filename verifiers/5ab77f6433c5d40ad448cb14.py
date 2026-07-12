import struct
import hashlib

# Extended TEA (XTEA variant as described in the assembly)
def _xtea_encode(data_words, key_words, rounds=32):
    """Encode two 32-bit words using Extended TEA as in the assembly."""
    DELTA = 0x9E3779B9
    MASK = 0xFFFFFFFF
    y, z = data_words[0] & MASK, data_words[1] & MASK
    s = 0
    for _ in range(rounds):
        # First half: update y using z
        tmp = (((z << 4) ^ (z >> 5)) + z) ^ (s + key_words[s & 3])
        s = (s + DELTA) & MASK
        y = (y + tmp) & MASK
        # Second half: update z using y
        tmp2 = (((y << 4) ^ (y >> 5)) + y) ^ (s + key_words[(s >> 11) & 3])
        z = (z + tmp2) & MASK
    return [y, z]

def _xtea_decode(data_words, key_words, rounds=32):
    """Decode two 32-bit words using Extended TEA as in the assembly."""
    DELTA = 0x9E3779B9
    MASK = 0xFFFFFFFF
    y, z = data_words[0] & MASK, data_words[1] & MASK
    s = (DELTA * rounds) & MASK  # 0xC6EF3720 for 32 rounds
    for _ in range(rounds):
        # First: undo z update
        tmp = (((y << 4) ^ (y >> 5)) + y) ^ (s + key_words[(s >> 11) & 3])
        # Note: in decode assembly, sum is decremented AFTER using it for z, but BEFORE for y
        # From assembly: sub edi, ebx (z -= ...) uses old sum, then sum -= DELTA, then sub esi (y -= ...) uses new sum
        old_s = s
        s = (s - DELTA) & MASK
        z = (z - tmp) & MASK
        # Second: undo y update
        tmp2 = (((z << 4) ^ (z >> 5)) + z) ^ (s + key_words[s & 3])
        y = (y - tmp2) & MASK
    return [y, z]

def ripemd128(data):
    """Compute RIPEMD-128 hash. Python's hashlib supports ripemd128 in some builds."""
    try:
        h = hashlib.new('ripemd128', data)
        return h.digest()
    except ValueError:
        # ASSUMPTION: If ripemd128 not available, fall back to a stub
        # Real algorithm requires RIPEMD-128
        raise RuntimeError("RIPEMD-128 not available in this Python build. Install a compatible version or use PyCryptodome.")

def _calc(val):
    """CRC-like transformation from calc proc in assembly."""
    MASK = 0xFFFFFFFF
    POLY = 0b11101101101110001000001110100000  # 0xEDB88320 standard CRC32 poly
    # From assembly: xor eax, 11101101101110001000001300100000b
    # The binary literal in source: 11101101101110001000001300100000
    # Let's parse it carefully: 11101101 10111000 10000011 00100000
    # = 0xEDB88320 -- this IS the standard CRC32 polynomial
    POLY = 0xEDB88320
    val = (~val) & MASK
    for _ in range(32):
        if val & 1:
            val = ((val >> 1) ^ POLY) & MASK
        else:
            val = (val >> 1) & MASK
    val = (~val) & MASK
    return val

def _name_to_serial_bytes(name):
    """Core keygen logic from keygen.asm DlgProc."""
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    name_len = len(name_bytes)
    
    # Compute RIPEMD-128 of name
    # Call: push offset Buffer; push eax (length); push offset szName; call _RIPEMD128
    hash_bytes = ripemd128(name_bytes)
    
    # Buffer = RIPEMD128 result (16 bytes = 4 dwords)
    buffer = list(struct.unpack_from('<4I', hash_bytes))
    
    # Apply calc() to each dword
    for i in range(4):
        buffer[i] = _calc(buffer[i])
    
    # Key = "LiGHT KeYGeNmE b" (16 bytes)
    key_str = b"LiGHT KeYGeNmE b"
    key = list(struct.unpack_from('<4I', key_str))
    
    # ExTEA_decode buffer[0:2] with key
    w0 = _xtea_decode([buffer[0], buffer[1]], key)
    buffer[0], buffer[1] = w0[0], w0[1]
    
    # ExTEA_decode buffer[2:4] with key
    w1 = _xtea_decode([buffer[2], buffer[3]], key)
    buffer[2], buffer[3] = w1[0], w1[1]
    
    # Convert back to bytes (16 bytes total)
    result = struct.pack('<4I', buffer[0], buffer[1], buffer[2], buffer[3])
    return result

def keygen(name):
    """Generate serial for a given name."""
    serial_bytes = _name_to_serial_bytes(name)
    # Format as hex string (uppercase, 2 chars per byte) = 32 hex chars
    serial = ''.join('%02X' % b for b in serial_bytes)
    return serial

def verify(name, serial):
    """Verify a name/serial pair."""
    expected = keygen(name)
    return serial.upper() == expected.upper()


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
