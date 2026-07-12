import hashlib
import struct

# TEA encryption/decryption constants
# Key from the crackme: "[BCG][FCG][DFCG]" - 16 bytes
# ASSUMPTION: The key is exactly the ASCII bytes of "[BCG][FCG][DFCG]" (16 bytes)
TEA_KEY_STR = b"[BCG][FCG][DFCG]"

def tea_encrypt(v0, v1, key):
    """Standard TEA encryption of two 32-bit values with 128-bit key."""
    k0, k1, k2, k3 = key
    delta = 0x9E3779B9
    mask = 0xFFFFFFFF
    total = 0
    for _ in range(32):
        total = (total + delta) & mask
        v0 = (v0 + (((v1 << 4) + k0) ^ (v1 + total) ^ ((v1 >> 5) + k1))) & mask
        v1 = (v1 + (((v0 << 4) + k2) ^ (v0 + total) ^ ((v0 >> 5) + k3))) & mask
    return v0, v1

def tea_decrypt(v0, v1, key):
    """Standard TEA decryption of two 32-bit values with 128-bit key."""
    k0, k1, k2, k3 = key
    delta = 0x9E3779B9
    mask = 0xFFFFFFFF
    total = (delta * 32) & mask
    for _ in range(32):
        v1 = (v1 - (((v0 << 4) + k2) ^ (v0 + total) ^ ((v0 >> 5) + k3))) & mask
        v0 = (v0 - (((v1 << 4) + k0) ^ (v1 + total) ^ ((v1 >> 5) + k1))) & mask
        total = (total - delta) & mask
    return v0, v1

def get_tea_key():
    """Parse the 16-byte TEA key into four 32-bit little-endian words."""
    k = TEA_KEY_STR
    return struct.unpack('<4I', k)

def md5_name(name):
    """Compute MD5 of the name and return the hex digest string (32 chars)."""
    return hashlib.md5(name.encode('ascii', errors='replace')).hexdigest()

def keygen(name):
    """
    Generate a valid 16-character serial for the given name.

    Steps (from writeup):
      1. MD5 the name -> 32-char hex string, take first 16 hex chars as 8 bytes
         which represent two 32-bit little-endian integers (the 'expected value').
      2. TEA-ENCRYPT those two values with the predefined key to get the serial.
      3. Format the result as a 16-char hex string (the serial).

    ASSUMPTION: The 'expected value' for comparison is derived from the first
    8 bytes (16 hex chars) of the MD5 hex digest of the name, interpreted as
    two little-endian 32-bit integers.

    ASSUMPTION: The serial is the 16-char hex representation (8 bytes) of the
    TEA-encrypted result of the MD5-derived value.

    ASSUMPTION: Standard TEA (not XTEA or XXTEA) is used.
    """
    key = get_tea_key()
    md5hex = md5_name(name)  # 32 hex chars

    # ASSUMPTION: Use first 16 hex chars (8 bytes) as the input block
    block_hex = md5hex[:16]
    block_bytes = bytes.fromhex(block_hex)
    v0, v1 = struct.unpack('<2I', block_bytes)

    # The writeup says: serial is TEA-decrypted -> md5 value.
    # So to get the serial from md5 value, we TEA-encrypt the md5 value.
    e0, e1 = tea_encrypt(v0, v1, key)

    serial_bytes = struct.pack('<2I', e0, e1)
    serial = serial_bytes.hex().upper()  # 16 hex chars
    return serial

def verify(name, serial):
    """
    Verify a name/serial pair.

    The crackme:
      1. Computes MD5 of name (hex string).
      2. Takes serial as hex, converts to bytes, TEA-decrypts it.
      3. Compares decrypted serial to (portion of) MD5 of name.

    Returns True if the serial is valid for the name.
    """
    if len(serial) != 16:
        return False
    try:
        serial_bytes = bytes.fromhex(serial)
    except ValueError:
        return False

    key = get_tea_key()
    s0, s1 = struct.unpack('<2I', serial_bytes)

    # TEA-decrypt the serial
    d0, d1 = tea_decrypt(s0, s1, key)

    # Compute expected value from MD5 of name
    md5hex = md5_name(name)
    block_hex = md5hex[:16]  # ASSUMPTION: first 16 hex chars
    block_bytes = bytes.fromhex(block_hex)
    v0, v1 = struct.unpack('<2I', block_bytes)

    return (d0 == v0) and (d1 == v1)


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
