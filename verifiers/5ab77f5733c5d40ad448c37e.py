# Rijndael crackme by tommy
# Serial validation: name is AES-encrypted with key "crackmes.de" (as bytes),
# and the resulting ciphertext is the valid serial.
#
# From the writeup:
# - The crackme uses Rijndael (AES) block cipher
# - The key is "crackmes.de"
# - The name is encrypted with that key to produce the serial
# - Phil Fresle's VB AES implementation is used
# - The serial shown for name "ORacLE_nJ" is given at the end of the writeup
#
# ASSUMPTION: AES is used in ECB mode with PKCS7 or zero-padding to 16 bytes,
#             key is "crackmes.de" zero-padded or truncated to 16 bytes.
# ASSUMPTION: The serial is the hex or raw bytes of the encrypted name.
# ASSUMPTION: Key size is 128-bit (the key "crackmes.de" is 11 bytes, padded to 16).

from Crypto.Cipher import AES
import binascii

KEY_STR = "crackmes.de"

def _pad_key(key_str: str) -> bytes:
    """Pad or truncate key to 16 bytes (128-bit AES)"""
    key_bytes = key_str.encode('latin-1')
    # ASSUMPTION: zero-padded to 16 bytes
    return key_bytes[:16].ljust(16, b'\x00')

def _pad_message(msg: bytes, block_size: int = 16) -> bytes:
    """Zero-pad message to multiple of block_size"""
    # ASSUMPTION: zero padding (VB implementation likely uses zero padding)
    remainder = len(msg) % block_size
    if remainder == 0:
        return msg
    return msg + b'\x00' * (block_size - remainder)

def _encrypt_name(name: str) -> bytes:
    """Encrypt name bytes with AES ECB using key crackmes.de"""
    key = _pad_key(KEY_STR)
    msg = _pad_message(name.encode('latin-1'))
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(msg)

def _decrypt_serial(serial_bytes: bytes) -> bytes:
    """Decrypt serial bytes with AES ECB using key crackmes.de"""
    key = _pad_key(KEY_STR)
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(serial_bytes)

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    encrypted = _encrypt_name(name)
    # ASSUMPTION: serial is represented as hex string
    return binascii.hexlify(encrypted).decode('ascii').upper()

def verify(name: str, serial: str) -> bool:
    """Verify that the serial matches the AES encryption of name with key crackmes.de."""
    # Accept serial as hex string
    try:
        serial_bytes = binascii.unhexlify(serial.replace('-', '').replace(' ', ''))
    except Exception:
        # ASSUMPTION: serial might be raw bytes passed as latin-1 string
        serial_bytes = serial.encode('latin-1')
    
    # The serial should decrypt back to the (padded) name
    try:
        decrypted = _decrypt_serial(serial_bytes)
    except Exception:
        return False
    
    # Compare decrypted to zero-padded name
    name_padded = _pad_message(name.encode('latin-1'))
    return decrypted == name_padded


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
