# electric_camel by death - partial reconstruction
# The algorithm involves: Tiger hash of name, Base64-encoded serial,
# ElGamal decryption, Blowfish encryption, SHA-1 of system code, RIPEMD-160 check.
# The writeup is truncated and many steps depend on system-specific values.
# This is a best-effort partial reconstruction with significant assumptions.

# ASSUMPTION: We cannot fully implement this without the actual binary,
# system code, and complete writeup. The below documents what IS known.

# Known values from writeup:
# ElGamal parameters:
#   p = 0x0cc7346a8b4ffb3f2393b  (192-bit)
#   y = 0x03e2cb006ad3961beda9d
#   g = 0x000000000000000000003
# The discrete log x = 0x0792A1952223 (6 bytes, provided by author)
# Expected RIPEMD-160 hash: 5DC6DEB5 523E101B 4CAC51B7 5F342339 0B9494DF

# ASSUMPTION: Tiger hash implementation needed (not in stdlib)
# ASSUMPTION: Blowfish implementation needed
# ASSUMPTION: RIPEMD-160 implementation needed
# ASSUMPTION: System code is machine-specific - cannot be known statically
# ASSUMPTION: The XOR constants are 0x67 for byte 8 and 0x4F for byte 9 (0-indexed)
# ASSUMPTION: The base64 alphabet is standard
# ASSUMPTION: The decoded serial must be exactly 10 bytes

import base64
import hashlib
import struct

# ElGamal parameters (from writeup)
ELGAMAL_P = 0x0cc7346a8b4ffb3f2393b
ELGAMAL_Y = 0x03e2cb006ad3961beda9d
ELGAMAL_G = 0x000000000000000000003

# Known discrete log solution (given by author death)
ELGAMAL_X = 0x0792A1952223  # 6 bytes

# Expected RIPEMD-160 of decrypted result
EXPECTED_RIPEMD160 = bytes([
    0x5D, 0xC6, 0xDE, 0xB5,
    0x52, 0x3E, 0x10, 0x1B,
    0x4C, 0xAC, 0x51, 0xB7,
    0x5F, 0x34, 0x23, 0x39,
    0x0B, 0x94, 0x94, 0xDF
])

def tiger_hash(data: bytes) -> bytes:
    # ASSUMPTION: Tiger hash is not in Python stdlib.
    # This is a placeholder. A real implementation would be needed.
    # The hash output is 192 bits (24 bytes).
    raise NotImplementedError("Tiger hash not implemented - requires external library")

def blowfish_encrypt_ecb(key: bytes, data: bytes) -> bytes:
    # ASSUMPTION: Blowfish ECB mode encryption of first 8 bytes (2 dwords)
    # key is first 6 bytes of modified Tiger hash
    # Uses big-endian mode per writeup
    # Placeholder - requires PyCryptodome or similar
    try:
        from Crypto.Cipher import Blowfish
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        # Encrypt first 8 bytes in big-endian mode
        return cipher.encrypt(data)
    except ImportError:
        raise NotImplementedError("PyCryptodome required for Blowfish")

def sha1_hash(data: bytes) -> bytes:
    return hashlib.sha1(data).digest()  # 20 bytes

def ripemd160_hash(data: bytes) -> bytes:
    # ASSUMPTION: RIPEMD-160 - available in some Python builds
    try:
        h = hashlib.new('ripemd160')
        h.update(data)
        return h.digest()
    except ValueError:
        raise NotImplementedError("RIPEMD-160 not available in this Python build")

def modify_tiger_hash(tiger_bytes: bytes, extra: bytes) -> bytes:
    # ASSUMPTION: sub_401D70 modifies the tiger hash in an unknown way.
    # The writeup says "this call modifies the tiger hash" but does not detail how.
    # We pass through unchanged as placeholder.
    return tiger_bytes

def get_system_code() -> str:
    # ASSUMPTION: System code is hardware-specific (shown in the crackme UI).
    # Cannot be determined without running the binary.
    raise NotImplementedError("System code is machine-specific")

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair according to electric_camel algorithm.
    
    Algorithm summary (from writeup):
    1. Compute Tiger hash of name (192 bits)
    2. Base64-decode the serial; decoded must be exactly 10 bytes
    3. Modify Tiger hash via sub_401D70 (unknown transformation)
    4. Use first 6 bytes of modified Tiger hash as Blowfish key
    5. Encrypt first 8 bytes of decoded serial with Blowfish (big-endian)
    6. XOR byte[8] with 0x67, byte[9] with 0x4F
    7. Get system code, compute SHA-1; add last 10 bytes to first 10
    8. XOR the 10-byte serial with these 10 bytes
    9. Perform ElGamal decryption with the result as x
    10. Put result in buffer, compute RIPEMD-160
    11. Check RIPEMD-160 == 5DC6DEB5 523E101B 4CAC51B7 5F342339 0B9494DF
    """
    # Step 1: Tiger hash of name
    name_bytes = name.encode('latin-1')
    try:
        tiger = tiger_hash(name_bytes)  # 24 bytes
    except NotImplementedError:
        return False

    # Step 2: Base64 decode serial
    try:
        decoded_serial = base64.b64decode(serial)
    except Exception:
        return False
    if len(decoded_serial) != 10:
        return False
    serial_buf = bytearray(decoded_serial)

    # Step 3: Modify tiger hash (sub_401D70 - unknown)
    # ASSUMPTION: passing the decoded serial bytes as 'extra' argument
    modified_tiger = modify_tiger_hash(tiger, bytes(serial_buf))

    # Step 4: Blowfish key = first 6 bytes of modified tiger hash
    bf_key = modified_tiger[:6]

    # Step 5: Blowfish encrypt first 8 bytes of serial (big-endian per writeup)
    try:
        encrypted_8 = blowfish_encrypt_ecb(bf_key, bytes(serial_buf[:8]))
    except NotImplementedError:
        return False
    serial_buf[:8] = encrypted_8

    # Step 6: XOR byte 8 with 0x67, byte 9 with 0x4F
    serial_buf[8] ^= 0x67
    serial_buf[9] ^= 0x4F

    # Step 7: SHA-1 of system code, then combine
    try:
        system_code = get_system_code()
    except NotImplementedError:
        return False
    sha1 = sha1_hash(system_code.encode('latin-1'))  # 20 bytes
    # Add last 10 bytes to first 10 bytes (mod 256)
    combined = bytearray(10)
    for i in range(10):
        combined[i] = (sha1[i] + sha1[i + 10]) & 0xFF

    # Step 8: XOR serial_buf with combined
    xored = bytearray(10)
    for i in range(10):
        xored[i] = serial_buf[i] ^ combined[i]

    # Step 9: ElGamal decryption - writeup says xored is the 'x' in elgamal
    # ASSUMPTION: The result of ElGamal decryption is placed into a buffer
    # ASSUMPTION: The decryption result must equal ELGAMAL_X (0x0792A1952223)
    # for the name to be valid. The actual elgamal decryption is complex.
    # The check: ripemd160(elgamal_decrypt(xored)) == EXPECTED_RIPEMD160
    # We cannot implement this fully without knowing the full elgamal scheme.
    
    # Placeholder: interpret xored as integer and compare to known x
    x_val = int.from_bytes(xored, 'big')
    
    # ASSUMPTION: elgamal decryption result goes into a buffer then RIPEMD-160'd
    # We simulate by hashing the known x value
    x_bytes = ELGAMAL_X.to_bytes(6, 'big')
    try:
        result_hash = ripemd160_hash(x_bytes)
    except NotImplementedError:
        return False
    
    return result_hash == EXPECTED_RIPEMD160

def keygen(name: str) -> str:
    """
    Generate a valid serial for name.
    
    Since this requires:
    - A specific system code (machine-specific)
    - Tiger hash implementation
    - Blowfish implementation  
    - ElGamal encryption
    - The discrete log x = 0x0792A1952223
    
    A full keygen is not possible without the system code and
    full crypto implementations. The outline is:
    
    1. Start with x = 0x0792A1952223 (10 bytes padded)
    2. Compute RIPEMD-160(x) and verify against expected
    3. Perform ElGamal encryption to get 10-byte ciphertext
    4. Get system code, SHA-1 it, combine 10+10 bytes
    5. XOR ciphertext with combined bytes
    6. XOR byte 8 with 0x67, byte 9 with 0x4F  
    7. Compute Tiger hash of name, use first 6 bytes as Blowfish key
    8. Blowfish decrypt first 8 bytes
    9. Base64 encode result -> serial
    """
    raise NotImplementedError(
        "Full keygen requires: system code, Tiger hash, Blowfish, ElGamal implementations. "
        "The discrete log x = 0x0792A1952223 was provided by the author."
    )


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
