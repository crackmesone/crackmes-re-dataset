# keygenme_2 by crackerlnn
# Based on the solution writeup which shows Blowfish encryption is used
# for serial validation. The exact validation logic (what is encrypted,
# what the expected output is, how name/serial relate) is NOT fully
# described in the truncated writeup. We implement what is known:
# - Blowfish is used with standard P-Box and S-Box initialization
# - The key is likely derived from the name
# - The serial is likely the hex/encoded ciphertext of some plaintext

try:
    from Crypto.Cipher import Blowfish
    import struct
except ImportError:
    raise ImportError("Install pycryptodome: pip install pycryptodome")

import struct

def derive_key(name: str) -> bytes:
    """Use the name as the Blowfish key (raw bytes, up to 56 bytes)."""
    # ASSUMPTION: The name is used directly as the Blowfish key.
    key = name.encode('ascii', errors='replace')
    key = key[:56]  # Blowfish max key = 56 bytes
    if len(key) == 0:
        key = b'\x00'
    return key

def get_plaintext() -> bytes:
    """Return the 8-byte plaintext block to encrypt.
    ASSUMPTION: The plaintext is a fixed known value (e.g. all zeros or
    some constant). The writeup does not specify what is encrypted.
    """
    # ASSUMPTION: plaintext is 8 zero bytes
    return b'\x00' * 8

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION:
    - Key = name bytes (up to 56 bytes)
    - Plaintext = 8 zero bytes
    - Expected serial = hex encoding of Blowfish_Encrypt(plaintext)
    - Blowfish in ECB mode (single 8-byte block)
    """
    if not name or not serial:
        return False
    try:
        key = derive_key(name)
        plaintext = get_plaintext()
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        encrypted = cipher.encrypt(plaintext)
        # ASSUMPTION: serial is the uppercase hex of the encrypted block
        expected_serial = encrypted.hex().upper()
        return serial.upper() == expected_serial
    except Exception:
        return False

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    ASSUMPTION: same as verify() above.
    """
    key = derive_key(name)
    plaintext = get_plaintext()
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    encrypted = cipher.encrypt(plaintext)
    return encrypted.hex().upper()


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
