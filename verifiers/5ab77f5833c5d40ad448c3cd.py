import struct
import random

# TEA encryption with key = b'Flying.....Horse'
# Key as 4 DWORDs (little-endian)
_KEY_BYTES = b'Flying.....Horse'
_MAGIC = struct.unpack('<4I', _KEY_BYTES)  # (0x69796C46, 0x2E2E676E, 0x482E2E2E, 0x6573726F)

DELTA = 0x9E3779B9
MASK = 0xFFFFFFFF

def tea_encrypt_block(v0, v1, key):
    """Encrypt a pair of 32-bit integers using TEA with 32 rounds."""
    k0, k1, k2, k3 = key
    s = 0
    for _ in range(32):
        s = (s + DELTA) & MASK
        v0 = (v0 + (((v1 << 4) + k0) ^ (v1 + s) ^ ((v1 >> 5) + k1))) & MASK
        v1 = (v1 + (((v0 << 4) + k2) ^ (v0 + s) ^ ((v0 >> 5) + k3))) & MASK
    return v0, v1

def tea_decrypt_block(v0, v1, key):
    """Decrypt a pair of 32-bit integers using TEA with 32 rounds."""
    k0, k1, k2, k3 = key
    s = (DELTA * 32) & MASK
    for _ in range(32):
        v1 = (v1 - (((v0 << 4) + k2) ^ (v0 + s) ^ ((v0 >> 5) + k3))) & MASK
        v0 = (v0 - (((v1 << 4) + k0) ^ (v1 + s) ^ ((v1 >> 5) + k1))) & MASK
        s = (s - DELTA) & MASK
    return v0, v1

def _name_to_32bytes(name):
    """Encode name as bytes, zero-padded to 32 bytes."""
    nb = name.encode('ascii', errors='replace')
    nb = nb[:32]
    nb = nb + b'\x00' * (32 - len(nb))
    return bytearray(nb)

def _encrypt_name(name_bytes):
    """Apply TEA encryption to four consecutive 8-byte blocks of name_bytes in-place."""
    buf = bytearray(name_bytes)
    key = _MAGIC
    for block in range(4):
        offset = block * 8
        v0, v1 = struct.unpack_from('<II', buf, offset)
        v0, v1 = tea_encrypt_block(v0, v1, key)
        struct.pack_into('<II', buf, offset, v0, v1)
    return buf

def keygen(name):
    """Generate the serial (key) for a given name.
    
    The serial is the TEA-encrypted name formatted as 8 uppercase hex DWORDs.
    Name must not exceed 21 characters (only first 21 are used).
    The remaining bytes (22..31) are filled with zeros here (the original fills with random,
    but zeros produce a deterministic keygen).
    """
    if len(name) > 21:
        name = name[:21]
    name_bytes = _name_to_32bytes(name)
    encrypted = _encrypt_name(name_bytes)
    dwords = struct.unpack('<8I', bytes(encrypted))
    serial = ''.join('%08X' % d for d in dwords)
    return serial

def verify(name, serial):
    """Check if the serial is valid for the given name.
    
    The crackme encrypts the name with TEA and formats as hex, then compares
    against the entered serial. The check stops at the first zero byte of the
    calculated username (which is derived from decrypting the serial).
    
    Verification: decrypt serial -> should yield (a prefix of) the name.
    The crackme compares the generated username (from the key) with the entered username,
    stopping at the first zero byte of the generated string.
    """
    # Validate serial length and characters
    serial = serial.strip().upper()
    if len(serial) != 64:
        return False
    try:
        int(serial, 16)
    except ValueError:
        return False

    # Decode serial into 8 DWORDs
    dwords = [int(serial[i*8:(i+1)*8], 16) for i in range(8)]
    encrypted_bytes = struct.pack('<8I', *dwords)

    # Decrypt the four 8-byte blocks
    key = _MAGIC
    decrypted = bytearray(32)
    for block in range(4):
        offset = block * 8
        v0, v1 = struct.unpack_from('<II', encrypted_bytes, offset)
        v0, v1 = tea_decrypt_block(v0, v1, key)
        struct.pack_into('<II', decrypted, offset, v0, v1)

    # Extract the null-terminated string from decrypted bytes
    null_pos = decrypted.find(0)
    if null_pos == -1:
        calc_name = decrypted.decode('ascii', errors='replace')
    else:
        calc_name = decrypted[:null_pos].decode('ascii', errors='replace')

    # Compare with provided name (truncated to 21 chars)
    if len(name) > 21:
        name = name[:21]

    return calc_name == name


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
