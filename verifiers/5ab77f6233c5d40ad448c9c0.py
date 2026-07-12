import base64
import struct

try:
    from pyDes import des, CBC, PAD_PKCS5
    HAS_PYDES = True
except ImportError:
    HAS_PYDES = False

try:
    from Crypto.Cipher import DES
    HAS_PYCRYPTO = True
except ImportError:
    HAS_PYCRYPTO = False

# DES key and IV (same value): b'DiplomkA'
KEY = bytes([0x44, 0x69, 0x70, 0x6c, 0x6f, 0x6d, 0x6b, 0x41])

# Expected base64-encoded ciphertext for first 38 bytes of file content
EXPECTED_CONTENT_B64 = 'n6oAtBbtvN2lmnwIguxE9MBZlpqdtQrf68pThEpfB8Zmzmvpu5TPPw=='
# Expected base64-encoded ciphertext for last 15 chars of the file path
EXPECTED_FILENAME_B64 = '2x2S4WJlj7vAkXgGnN+WCQ=='

# Decrypted plaintext values (derived from decrypting the above with DES CBC, key=IV=KEY)
# Content: '* Licencny subor *\r\n* Diplomka 2015  *'  (38 chars)
REQUIRED_CONTENT = b'* Licencny subor *\r\n* Diplomka 2015  *'
# Filename suffix: '\\Licencny_subor' or '\\Licencny_suborv' (15 chars)
# Both writeups agree the file must be named 'Licencny_subor'
REQUIRED_FILENAME_SUFFIX = b'\\Licencny_subor'

def _pkcs5_pad(data: bytes, block_size: int = 8) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def _des_encrypt_b64(plaintext: str) -> str:
    """Encrypt plaintext with DES CBC (key=IV=KEY) and return base64 string."""
    data = plaintext.encode('utf-8') if isinstance(plaintext, str) else plaintext
    data_padded = _pkcs5_pad(data)
    if HAS_PYCRYPTO:
        cipher = DES.new(KEY, DES.MODE_CBC, KEY)
        ct = cipher.encrypt(data_padded)
    elif HAS_PYDES:
        k = des(KEY, CBC, KEY, pad=None, padmode=PAD_PKCS5)
        ct = k.encrypt(data)
    else:
        raise RuntimeError('No DES library available. Install pycryptodome or pyDes.')
    return base64.b64encode(ct).decode('ascii')

def _des_decrypt(b64_ciphertext: str) -> bytes:
    """Decrypt base64 DES CBC ciphertext (key=IV=KEY) and return plaintext bytes."""
    ct = base64.b64decode(b64_ciphertext)
    if HAS_PYCRYPTO:
        cipher = DES.new(KEY, DES.MODE_CBC, KEY)
        pt = cipher.decrypt(ct)
        # strip PKCS5 padding
        pad_len = pt[-1]
        return pt[:-pad_len]
    elif HAS_PYDES:
        k = des(KEY, CBC, KEY, pad=None, padmode=PAD_PKCS5)
        return k.decrypt(ct)
    else:
        raise RuntimeError('No DES library available. Install pycryptodome or pyDes.')

def _kryptuj_des(text: str) -> str:
    """Mimics the C# KryptujDES method."""
    return _des_encrypt_b64(text)

def verify(name: str, serial: str) -> bool:
    """
    Simulates the Testuj() check.
    'name'   = the file path (e.g. 'C:\\path\\Licencny_subor')
    'serial' = the full content of the license file as a string

    The algorithm:
    1. Read file content into class field 'meno' (= serial here).
    2. Make local copy 'local_meno' = serial.
    3. Try to remove first 56 (0x38) chars from class field; on failure set to ''.
    4. If class field is now null/empty, prepend '0x38' to local_meno.
    5. Truncate local_meno to first 38 (0x26) chars.
    6. KryptujDES(local_meno) must == EXPECTED_CONTENT_B64
    7. KryptujDES(last 15 chars of file path/name) must == EXPECTED_FILENAME_B64
    """
    # Step 1 & 2
    class_meno = serial
    local_meno = serial

    # Step 3
    try:
        if len(class_meno) < 56:
            raise ValueError('too short')
        class_meno = class_meno[56:]  # Remove(0, 0x38)
    except Exception:
        class_meno = ''

    # Step 4
    if not class_meno:  # null or empty
        local_meno = '0x38' + local_meno

    # Step 5: keep first 38 chars
    local_meno = local_meno[:0x26]  # Remove(0x26, len-0x26) means keep first 38

    # Step 6: encrypt and compare
    enc_content = _kryptuj_des(local_meno)
    if enc_content != EXPECTED_CONTENT_B64:
        return False

    # Step 7: last 15 chars of the file path
    file_suffix = name[-15:]
    enc_filename = _kryptuj_des(file_suffix)
    if enc_filename != EXPECTED_FILENAME_B64:
        return False

    return True

def keygen(name: str) -> str:
    """
    Generate a valid license file content for a given user name.

    Constraints:
    - File must be named 'Licencny_subor' (no extension).
    - First 38 bytes: '* Licencny subor *\r\n* Diplomka 2015  *'
    - Bytes 39-56 (18 bytes): any padding (e.g. 'a' * 18)
    - Remaining bytes: name (at least 1 char)
    """
    # The file MUST be named 'Licencny_subor'; name parameter is the user/owner name
    header = '* Licencny subor *\r\n* Diplomka 2015  *'  # exactly 38 chars
    padding = 'a' * 18  # fills bytes 38..55 (18 bytes of filler)
    if not name:
        name = 'User'
    file_content = header + padding + name
    return file_content

def self_test():
    """Verify the algorithm using known-good test vectors from the writeup."""
    # Decrypt and confirm the plaintext
    try:
        pt1 = _des_decrypt(EXPECTED_CONTENT_B64)
        pt2 = _des_decrypt(EXPECTED_FILENAME_B64)
        print(f'Decrypted content : {pt1}')
        print(f'Decrypted filename: {pt2}')
    except RuntimeError as e:
        print(f'Warning: {e}')
        print('Skipping DES self-test. Install pycryptodome: pip install pycryptodome')
        return

    # Test keygen + verify
    user_name = 'Matteo'
    file_path = 'C:\\some\\path\\Licencny_subor'
    content = keygen(user_name)
    result = verify(file_path, content)
    print(f'keygen("{user_name}") -> verify result: {result}')
    print(f'License file content:\n{content}')


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
