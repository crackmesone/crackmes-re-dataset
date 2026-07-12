# The writeup is heavily encoded/garbled (appears to be a double-encoded text file),
# making it extremely difficult to extract a clean algorithm. Below is what can be
# inferred from readable fragments:
#
# 1. The crackme reads a file named 'key.dat'
# 2. It reads 256 (0x100) characters from the file
# 3. It checks if file size is 0x1e30 (30*0x100?) bytes long
# 4. The file content is XOR-decrypted with bytes 'T','M','G' (0x54, 0x4D, 0x47) cycling
#    i.e.: byte[0] ^= 'T', byte[1] ^= 'M', byte[2] ^= 'G', repeating
# 5. After decryption, the decrypted buffer is treated as RSA-240 encrypted data
#    (the writeup mentions RSA-240 decryption, powmod, bytes_to_big, etc.)
# 6. The decrypted content is compared against a known plaintext involving 'Thigo'
#    and the user name.
# 7. The format of the plaintext before encryption appears to be:
#    'Thigo', <6 random chars [a-z]>, <name padded to 30 chars with 0x00 bytes>
# 8. The 6 random chars must hash (SHA-1) to specific bytes such that:
#    BYTE1 = 0x55h xor 0x8bh = 0xdeh
#    BYTE2 = 0x8bh xor 0x4ch = 0xc7h  (ASSUMPTION based on fragment)
#    BYTE3 = 0x65h xor 0xech = 0x89h  (ASSUMPTION)
#
# ASSUMPTION: The RSA modulus N and exponent e/d are not fully recoverable from the writeup.
# ASSUMPTION: The exact SHA-1 usage and chaining variables are partially described.
# ASSUMPTION: The 6-char verb is 'ufound' based on the writeup fragment 'ufound'.

import struct

# XOR key cycling through 'T','M','G'
XOR_KEY = [0x54, 0x4D, 0x47]  # 'T', 'M', 'G'

def xor_decrypt(data: bytes) -> bytes:
    """XOR decrypt data with cycling key TMG."""
    result = bytearray(data)
    for i in range(len(result)):
        result[i] ^= XOR_KEY[i % 3]
    return bytes(result)

def xor_encrypt(data: bytes) -> bytes:
    """XOR encrypt data with cycling key TMG (same as decrypt, XOR is symmetric)."""
    return xor_decrypt(data)

# ASSUMPTION: RSA-240 parameters; the writeup mentions RSA-240 decryption.
# The modulus N from writeup fragment:
# N = 0xB9B9CDA76CC75A4F3A1AA643202E0C6B245B56977480C9DA8D8F29F47 (partial, not fully recovered)
# d = 0xE80762BC29285C2AB1B141DE146F7B343D1EADA5BAEC090E93A16E1 (ASSUMPTION)
# e = 0x10001 (standard RSA public exponent, ASSUMPTION)

# From the writeup, the known values:
# N (partial) shown as: B9B9CDA766CC75A4F3A1AA643202E0C6B245B569774 8F8C9DA8D8F29F47
# encryption key d = 0xE807...h (not fully recoverable)

# ASSUMPTION: The verb used is 'ufound' (readable from writeup)
VERB = 'ufound'

def build_plaintext(name: str) -> bytes:
    """
    Build the plaintext before RSA encryption:
    Format: 'Thigo' + 6_char_verb + name_padded_to_30_chars_with_null
    Total: 5 + 6 + 30 = 41 bytes minimum, padded to 30 chars total for name part.
    ASSUMPTION: exact padding/format based on writeup fragments.
    """
    prefix = b'Thigo'
    verb_bytes = VERB.encode('ascii')  # 6 chars [a-z]
    # Pad name to 30 characters with 0x00
    name_bytes = name.encode('ascii')
    name_padded = name_bytes.ljust(30, b'\x00')[:30]
    plaintext = prefix + verb_bytes + name_padded
    return plaintext

def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The serial/key.dat file content, when XOR-decrypted with TMG,
    and then RSA-decrypted, should equal the plaintext built from name.
    Since we cannot fully recover RSA keys, this is a stub.
    """
    # The key.dat file content would be the 'serial' here as hex or bytes
    try:
        if isinstance(serial, str):
            # Assume serial is hex-encoded content of key.dat
            key_data = bytes.fromhex(serial)
        else:
            key_data = serial
        
        # Step 1: XOR decrypt the file content
        decrypted = xor_decrypt(key_data[:30])
        
        # Step 2: Build expected plaintext
        expected = build_plaintext(name)
        
        # ASSUMPTION: Without RSA keys, we can only check XOR layer.
        # In the real crackme, decrypted would be RSA-decrypted first.
        # The first 5 bytes of decrypted RSA output should be 'Thigo'
        # and the next 6 should be 'ufound', rest is name.
        
        # Check if XOR-decrypted data matches expected plaintext directly
        # (This is only valid if there's no RSA layer, which is likely wrong)
        if len(decrypted) < len(expected):
            return False
        
        return decrypted[:len(expected)] == expected
    except Exception:
        return False

def keygen(name: str) -> bytes:
    """
    Generate a key.dat file content for the given name.
    ASSUMPTION: Without the RSA private key, we can only generate the XOR-encrypted
    version of the plaintext. The real keygen would need RSA encryption.
    """
    plaintext = build_plaintext(name)
    
    # Pad to 30 characters total as mentioned in writeup
    # 'put 30 characters in your file'
    padded = plaintext.ljust(30, b'\x00')[:30]
    
    # XOR encrypt to produce key.dat content
    # ASSUMPTION: In reality, RSA encryption happens before XOR
    key_data = xor_encrypt(padded)
    
    return key_data

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
