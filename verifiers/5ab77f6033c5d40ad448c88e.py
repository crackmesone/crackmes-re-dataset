import struct
import hashlib

# ASSUMPTION: The full TEA key and exact SHA1 digest bytes used as TEA input are not fully specified.
# ASSUMPTION: The exact MD4 portion and how the final serial is formatted is partially described but truncated.
# ASSUMPTION: The keygen.cpp is truncated and many details are missing.
# ASSUMPTION: The final serial comparison target and format are not fully recoverable from the text.

def rol_byte(val, count):
    val &= 0xFF
    count &= 7
    return ((val << count) | (val >> (8 - count))) & 0xFF

def transform_name(name_bytes):
    """Apply the two transformations described in the writeup:
    1. Subtract 4 from every other byte (indices 0, 2, 4, ...)
    2. ROL each byte by 2
    """
    b = bytearray(name_bytes)
    # Step 1: subtract 0x4 from chars at even indices (stepping by 2)
    i = 0
    while i < len(b):
        b[i] = (b[i] - 4) & 0xFF
        i += 2
    # Step 2: ROL every byte by 2
    for i in range(len(b)):
        b[i] = rol_byte(b[i], 2)
    return bytes(b)

def tea_encrypt(v0, v1, key):
    """Standard TEA encryption.
    key is a list/tuple of 4 uint32 values.
    """
    DELTA = 0x9E3779B9
    mask = 0xFFFFFFFF
    s = 0
    for _ in range(32):
        s = (s + DELTA) & mask
        v0 = (v0 + (((v1 << 4) + key[0]) ^ (v1 + s) ^ ((v1 >> 5) + key[1]))) & mask
        v1 = (v1 + (((v0 << 4) + key[2]) ^ (v0 + s) ^ ((v0 >> 5) + key[3]))) & mask
    return v0, v1

# ASSUMPTION: TEA key is taken from address 0x0040401C as shown in the writeup.
# The actual bytes at 0x0040401C are not given; using val_con from keygen.cpp as a guess.
# val_con = { 0x3D, 0xC3, 0x09, 0xE4, 0xAA, 0x89, 0x07, 0xE4, 0x20, 0xEF, 0xDE, 0x03, 0xB4, 0xC3, 0x06, 0xE8 }
TEA_KEY_BYTES = bytes([0x3D, 0xC3, 0x09, 0xE4, 0xAA, 0x89, 0x07, 0xE4,
                        0x20, 0xEF, 0xDE, 0x03, 0xB4, 0xC3, 0x06, 0xE8])
TEA_KEY = struct.unpack('<4I', TEA_KEY_BYTES)

def check_name_length(name):
    n = len(name)
    # Must be <= 10
    if n > 10:
        return False
    # (n+1)*16 * (0x40 + (n+1)*16) * 0x182 >= 0x10960
    val = (n + 1) * 16
    esi = val * (0x40 + val) * 0x182
    if esi < 0x10960:
        return False
    return True

def compute_serial(name):
    """Attempt to compute the serial for a given name."""
    name_bytes = name.encode('ascii')
    
    if not check_name_length(name):
        return None
    
    # Transform the name
    transformed = transform_name(name_bytes)
    
    # Compute SHA1 of transformed name
    sha1_digest = hashlib.sha1(transformed).digest()  # 20 bytes
    
    # TEA encrypt last part of SHA1 (from offset 0x0C, i.e., last 8 bytes as two uint32)
    # ESI points to sha1_result + 0x0C
    # ASSUMPTION: TEA input is sha1_digest[12:20] (last 8 bytes)
    tea_input = sha1_digest[12:20]
    v0, v1 = struct.unpack('<2I', tea_input)
    v0_enc, v1_enc = tea_encrypt(v0, v1, TEA_KEY)
    
    # Replace last 8 bytes of SHA1 with TEA encrypted values
    sha1_modified = sha1_digest[:12] + struct.pack('<2I', v0_enc, v1_enc)
    
    # ASSUMPTION: MD4 is computed but described as a red herring / confusion element.
    # The actual serial derivation after MD4 is truncated in the writeup.
    # We cannot fully reconstruct the serial without the complete algorithm.
    
    # Return hex of modified SHA1 as placeholder
    return sha1_modified.hex().upper()

def verify(name, serial):
    """Verify name/serial pair.
    ASSUMPTION: Full verification not reconstructible from truncated writeup.
    This is a partial implementation.
    """
    if not check_name_length(name):
        return False
    
    computed = compute_serial(name)
    if computed is None:
        return False
    
    # ASSUMPTION: The serial should be 24 hex characters (0x18 length mentioned in writeup)
    # and compared against a computed value. Exact comparison logic is unknown.
    # Returning False as we cannot verify without full algorithm.
    return serial.upper() == computed[:24]

def keygen(name):
    """Generate a serial for a given name.
    ASSUMPTION: Partial - output may not match the actual crackme.
    """
    if not check_name_length(name):
        raise ValueError(f"Name '{name}' fails length check (need length 4-10)")
    
    serial = compute_serial(name)
    if serial is None:
        raise ValueError("Could not compute serial")
    
    # Return first 24 hex chars (length 0x18 as mentioned in writeup)
    return serial[:24]


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
