import hashlib
from base64 import b64encode

# The DES key is derived from the SHA1 hash of the string '5167449'
# clsx.K = 5167449 (computed from xa()/xb() math, fixed constant)
# TheKey = first 8 bytes of SHA1('5167449')

def _get_des_key():
    K_str = '5167449'
    sha1 = hashlib.sha1(K_str.encode('utf-8')).digest()
    return sha1[:8]  # D4 ED 34 93 1C 48 AC 08

# DES IV from clsx constructor
VECTOR = bytes([0x12, 0x44, 0x16, 0xee, 0x88, 0x15, 0xdd, 0x41])

# Precomputed TheKey (verified against writeup)
THE_KEY = bytes([0xd4, 0xed, 0x34, 0x93, 0x1c, 0x48, 0xac, 0x08])


def _des_encrypt_cbc_pkcs5(key, iv, plaintext_bytes):
    """DES CBC encryption with PKCS5 padding (block size 8)."""
    # PKCS5 padding
    block_size = 8
    pad_len = block_size - (len(plaintext_bytes) % block_size)
    padded = plaintext_bytes + bytes([pad_len] * pad_len)

    def _des_encrypt_block(key8, block8):
        """Single DES block encryption using the des library if available,
        otherwise fall back to PyCryptodome."""
        try:
            from Crypto.Cipher import DES as _DES
            cipher = _DES.new(key8, _DES.MODE_ECB)
            return cipher.encrypt(block8)
        except ImportError:
            pass
        try:
            from pyDes import des as _pydes, ECB as _ECB, PAD_NORMAL as _PAD_NORMAL
            d = _pydes(key8, _ECB, pad=None, padmode=_PAD_NORMAL)
            return d.encrypt(block8)
        except ImportError:
            pass
        raise ImportError('Install pycryptodome or pyDes: pip install pycryptodome')

    ciphertext = b''
    prev = iv
    for i in range(0, len(padded), block_size):
        blk = bytes(a ^ b for a, b in zip(padded[i:i+block_size], prev))
        enc = _des_encrypt_block(key, blk)
        ciphertext += enc
        prev = enc
    return ciphertext


def _serial_from_name(name):
    """Compute serial: DES-CBC-PKCS5(name) -> base64 -> hex uppercase of each char."""
    key = THE_KEY
    iv = VECTOR
    plaintext = name.encode('utf-8')
    encrypted = _des_encrypt_cbc_pkcs5(key, iv, plaintext)
    b64 = b64encode(encrypted).decode('ascii')
    # Convert each ASCII character of the base64 string to its hex representation
    serial = ''.join('%02X' % ord(c) for c in b64)
    return serial


def keygen(name):
    """Generate the serial for the given username."""
    return _serial_from_name(name)


def verify(name, serial):
    """Return True if serial matches the expected serial for name."""
    expected = _serial_from_name(name)
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
