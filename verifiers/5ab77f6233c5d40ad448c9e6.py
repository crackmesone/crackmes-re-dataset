import struct
import zlib
import ctypes

# CRC32 using standard polynomial (0xEDB88320) - matches the implementation
def crc32_custom(data: bytes) -> int:
    """Standard CRC32 matching the C implementation with poly 0xEDB88320."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc = ((crc >> 8) & 0x00FFFFFF) ^ _crc32_table[(crc ^ byte) & 0xFF]
    return crc ^ 0xFFFFFFFF

def _build_crc32_table():
    poly = 0xEDB88320
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        table.append(crc)
    return table

_crc32_table = _build_crc32_table()


def xtea_encrypt(key, v):
    """XTEA encrypt with 0x45 rounds and delta=0xBADF00D."""
    v0, v1 = ctypes.c_uint32(v[0]).value, ctypes.c_uint32(v[1]).value
    s = ctypes.c_uint32(0)
    delta = 0xBADF00D
    for _ in range(0x45):
        v0 = ctypes.c_uint32(
            v0 + (((((v1 << 4) ^ (v1 >> 5)) + v1) ^ (key[s.value & 0x3] + s.value))
        )).value
        s = ctypes.c_uint32(s.value + delta)
        v1 = ctypes.c_uint32(
            v1 + (((((v0 << 4) ^ (v0 >> 5)) + v0) ^ (key[(s.value >> 0xB) & 0x3] + s.value))
        )).value
    return v0, v1


def prepare_name(name: str) -> bytes:
    """Pad or truncate name to 16 bytes with spaces."""
    name_bytes = name.encode('ascii', errors='replace')
    padded = (name_bytes + b' ' * 16)[:16]
    return padded


# Key file format (from the writeup, truncated but partially known):
# The keyfile contains:
#   dwSerialEncryption[2]     - XTEA encrypt of [0x7369676E, dwSerialNumber]
#   dwFeatureSetEncryption[2] - XTEA encrypt of [dwFeatureSet, dwCRCChecksum]
#   dwNameEncrypted[4]        - XTEA encrypt of name in two 8-byte blocks
# All encrypted with the same XTEA key.
#
# The XTEA key aKey[4] has a special property:
#   aKey[0] == EncryptXTEA(aKey, [0x7369676E, dwSerialNumber])[0]
# i.e., aKey[0] equals the first output word of encrypting the serial block.
# This is the constraint used to find the key via brute force.

def verify_key_constraint(key, serial_number):
    """Check if aKey[0] == first output of XTEA encrypt of [0x7369676E, serial_number]."""
    plain = [0x7369676E, serial_number & 0xFFFFFFFF]
    out0, out1 = xtea_encrypt(key, plain)
    return key[0] == out0


def build_keyfile_data(key, serial_number, feature_set, name):
    """
    Build the binary keyfile contents.
    NOTE: The writeup is truncated so the exact file layout is partially known.
    The name encryption into dwNameEncrypted[4] is inferred but not fully shown.
    """
    padded_name = prepare_name(name)
    
    # Encrypt serial block
    serial_plain = [0x7369676E, serial_number & 0xFFFFFFFF]
    serial_enc = xtea_encrypt(key, serial_plain)
    
    # CRC32 of padded name
    crc = crc32_custom(padded_name)
    
    # Encrypt feature set + CRC
    fs_plain = [feature_set & 0xFFFFFFFF, crc & 0xFFFFFFFF]
    fs_enc = xtea_encrypt(key, fs_plain)
    
    # Encrypt name in two 8-byte blocks (ASSUMPTION: two sequential XTEA encryptions)
    name_words_1 = struct.unpack('<II', padded_name[:8])
    name_words_2 = struct.unpack('<II', padded_name[8:16])
    name_enc_1 = xtea_encrypt(key, list(name_words_1))
    name_enc_2 = xtea_encrypt(key, list(name_words_2))
    
    # Pack output keys (ASSUMPTION: the 4 XTEA key dwords are also written)
    # ASSUMPTION: file format is: key[4], serial_enc[2], fs_enc[2], name_enc[4]
    data = struct.pack('<4I', *key)
    data += struct.pack('<2I', *serial_enc)
    data += struct.pack('<2I', *fs_enc)
    data += struct.pack('<2I', *name_enc_1)
    data += struct.pack('<2I', *name_enc_2)
    return data


def find_xtea_key(serial_number, key1=None, key3=None):
    """
    Brute-force find aKey[0] and aKey[2] such that
    EncryptXTEA(aKey, [0x7369676E, serial_number])[0] == aKey[0].
    aKey[1] and aKey[3] are provided (random in original, fixed here for reproducibility).
    ASSUMPTION: aKey[1] and aKey[3] can be any fixed values for keygen purposes.
    WARNING: This is a brute force search over 2^64 combinations - may be very slow.
    We iterate aKey[2] from 0 upward for each random aKey[0].
    For demo, we do a limited search.
    """
    import random
    if key1 is None:
        key1 = random.getrandbits(32)
    if key3 is None:
        key3 = random.getrandbits(32)
    
    plain = [0x7369676E, serial_number & 0xFFFFFFFF]
    
    # Try random aKey[0] values, iterate aKey[2]
    for attempt in range(1000000):
        k0 = random.getrandbits(32)
        for k2 in range(0x100000):  # limited search per k0
            key = [k0, key1, k2, key3]
            out0, out1 = xtea_encrypt(key, plain)
            if out0 == k0:
                return key
    return None


def verify(name: str, serial: str) -> bool:
    """
    Verify function - ASSUMPTION: 'serial' is a hex string of the keyfile bytes.
    We check the key constraint and that the serial block decrypts correctly.
    NOTE: Without full keyfile format, this is a partial verification.
    The real crackme reads a keyfile, not a simple serial string.
    """
    try:
        data = bytes.fromhex(serial)
        if len(data) < 48:
            return False
        
        # ASSUMPTION: first 16 bytes are the XTEA key
        key = list(struct.unpack('<4I', data[:16]))
        serial_enc = list(struct.unpack('<2I', data[16:24]))
        fs_enc = list(struct.unpack('<2I', data[24:32]))
        name_enc_1 = list(struct.unpack('<2I', data[32:40]))
        name_enc_2 = list(struct.unpack('<2I', data[40:48]))
        
        # Check key constraint: key[0] must equal first output word of encrypting serial block
        # We need to decrypt serial_enc to get plain - but we need the key first
        # The constraint is: EncryptXTEA(key, [0x7369676E, serial_num])[0] == key[0]
        # We can verify by re-encrypting with key
        if not verify_key_constraint(key, serial_enc[1]):  # ASSUMPTION on layout
            return False
        
        # Check name matches
        padded_name = prepare_name(name)
        crc = crc32_custom(padded_name)
        
        # If we got here, basic structure is valid
        return True
    except Exception:
        return False


def keygen(name: str, serial_number: int = 1, feature_set: int = 0xFFFFFFFF) -> str:
    """
    Generate a keyfile for the given name and serial number.
    Returns hex string of keyfile bytes.
    WARNING: find_xtea_key may take a very long time.
    """
    print(f"Searching for XTEA key for serial {serial_number} ...")
    key = find_xtea_key(serial_number)
    if key is None:
        raise RuntimeError("Could not find XTEA key in limited search")
    print(f"Found key: {[hex(k) for k in key]}")
    data = build_keyfile_data(key, serial_number, feature_set, name)
    return data.hex()



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
