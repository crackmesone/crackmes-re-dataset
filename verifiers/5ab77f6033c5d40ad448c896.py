import base64
import struct

# ---------------------------------------------------------------------------
# EncodeName  (translated directly from KeyGen.pas)
# ---------------------------------------------------------------------------
SALT_TABLE = [0x7E, 0x04, 0x71, 0xCA, 0x47, 0x6F, 0x1E, 0x7A]

def encode_name(name: str) -> bytes:
    """
    Delphi EncodeName() transliterated to Python.
    Input : name string (7 or 8 chars)
    Output: raw bytes (same length as name)
    """
    name_bytes = name.encode('latin-1')
    n = len(name_bytes)
    result = []
    int_val = 0x32
    for i in range(n):
        char_val = name_bytes[n - i - 1]          # reversed name
        int_buf = (SALT_TABLE[i % 8] ^ char_val) - int_val
        int_val = char_val
        if int_buf < 0:
            int_buf += 0xFF
        result.append(int_buf & 0xFF)
    return bytes(result)


# ---------------------------------------------------------------------------
# Serpent-CFB8  via dcpcrypt
# The crackme uses:
#   key  = MD5("_Keygen_Me_v1.9_")
#   mode = CFB-8 bit  (EncryptString / DecryptString in dcpcrypt)
#
# dcpcrypt's EncryptString pads with zeros to a block boundary,
# then Base64-encodes the result before returning it.
#
# ASSUMPTION: We replicate this with PyCryptodome Serpent in CFB-8 mode.
#             dcpcrypt uses a *specific* CFB variant (8-bit feedback / ECB-
#             encrypt of the shift-register).  PyCryptodome's CFB segment_size=8
#             should match, but byte-level compatibility is not guaranteed
#             without the actual Delphi binary for cross-checking.
# ---------------------------------------------------------------------------
try:
    from Crypto.Cipher import AES          # kept as fallback note
    from Crypto.Hash   import MD5
    # PyCryptodome does NOT ship a Serpent cipher by default.
    # We attempt to import one; if unavailable we raise a clear error.
    try:
        from Crypto.Cipher import Serpent as _SerpentModule
        _HAS_SERPENT = True
    except ImportError:
        _HAS_SERPENT = False
except ImportError:
    _HAS_SERPENT = False


def _md5_key(passphrase: str) -> bytes:
    """MD5 of the passphrase string (dcpcrypt InitStr behaviour)."""
    h = MD5.new()
    h.update(passphrase.encode('latin-1'))
    return h.digest()   # 16 bytes


KEY_STRING = '_Keygen_Me_v1.9_'


def _serpent_encrypt_string(plaintext: bytes) -> bytes:
    """
    Mimic dcpcrypt TDCP_serpent.EncryptString:
      1. pad plaintext with zeros to next 16-byte boundary
      2. encrypt in CFB-8 mode (IV = 0)
      3. return raw cipher bytes (caller base64-encodes)

    ASSUMPTION: IV is all-zero (dcpcrypt default).
    ASSUMPTION: CFB segment_size=8 matches dcpcrypt CFB8 variant.
    """
    if not _HAS_SERPENT:
        raise RuntimeError(
            'PyCryptodome Serpent not available. '
            'Install a Serpent-capable library (e.g. serpent, pycryptodomex with Serpent patch) '
            'or run the Delphi keygen directly.')
    key = _md5_key(KEY_STRING)
    # pad to block size (16 bytes)
    pad_len = (16 - len(plaintext) % 16) % 16
    padded = plaintext + b'\x00' * pad_len
    iv = b'\x00' * 16
    cipher = _SerpentModule.new(key, mode=_SerpentModule.MODE_CFB,
                                IV=iv, segment_size=8)
    return cipher.encrypt(padded)


def _serpent_decrypt_string(ciphertext: bytes) -> bytes:
    """
    Mimic dcpcrypt TDCP_serpent.DecryptString (CFB-8, IV=0).
    ASSUMPTION: same as _serpent_encrypt_string.
    """
    if not _HAS_SERPENT:
        raise RuntimeError('PyCryptodome Serpent not available.')
    key = _md5_key(KEY_STRING)
    iv = b'\x00' * 16
    cipher = _SerpentModule.new(key, mode=_SerpentModule.MODE_CFB,
                                IV=iv, segment_size=8)
    return cipher.decrypt(ciphertext)


# ---------------------------------------------------------------------------
# Keygen  (forward direction)
# ---------------------------------------------------------------------------
def keygen(name: str) -> str:
    """
    Generate a valid serial for 'name' (must be 7 or 8 characters).

    Steps (from KeyGen.pas):
      1. EncodeName -> raw bytes (name_enc)
      2. Treat name_enc as a NUL-terminated C string, pass to EncryptString
      3. EncryptString returns a base64 string
      4. BinToHex of that base64 string -> final serial (24 hex chars)
    """
    if len(name) < 7 or len(name) > 8:
        raise ValueError('Name must be 7 or 8 characters long')

    name_enc = encode_name(name)   # raw bytes, length = len(name)

    # dcpcrypt EncryptString receives a PChar (NUL-terminated); take only
    # up to first NUL byte (mirroring Delphi PChar semantics).
    # ASSUMPTION: name_enc is treated as a full byte string with possible NUL.
    str_serial = name_enc  # Delphi: strSerial := PChar(@strNameHash[0])

    encrypted = _serpent_encrypt_string(str_serial)

    # dcpcrypt EncryptString base64-encodes the output internally.
    str_ret = base64.b64encode(encrypted).decode('ascii')

    # BinToHex of base64 string bytes -> hex of ASCII codes of base64 chars
    # Delphi: BinToHex(@strRet[1], @strSerial[1], StrLen(PChar(strRet)))
    # StrLen stops at NUL; base64 output won't contain NUL normally.
    hex_serial = str_ret.encode('latin-1').hex().upper()

    # Serial must be 24 hex chars (12 bytes).  The base64 of 9 bytes is 12
    # chars; hex of those 12 chars = 24 hex chars.
    # ASSUMPTION: truncate / take first 24 chars to match the expected length.
    return hex_serial[:24]


# ---------------------------------------------------------------------------
# Verify  (reverse direction – what the crackme does)
# ---------------------------------------------------------------------------
def verify(name: str, serial: str) -> bool:
    """
    Replicate the crackme's check:
      1. Compute name_enc via EncodeName
      2. Parse serial (24 hex chars -> 12 bytes)
      3. Interpret those 12 bytes as base64 -> 9 bytes
      4. Decrypt with Serpent-CFB8 using key=MD5('_Keygen_Me_v1.9_')
      5. Compare result to name_enc
    """
    if len(name) < 7 or len(name) > 8:
        return False
    if len(serial) != 24:
        return False

    try:
        serial_bytes = bytes.fromhex(serial)          # 12 bytes
    except ValueError:
        return False

    # Those 12 bytes are ASCII chars of a base64 string
    try:
        b64_str = serial_bytes.decode('latin-1')
        decoded = base64.b64decode(b64_str)            # 9 bytes
    except Exception:
        return False

    try:
        decrypted = _serpent_decrypt_string(decoded)   # Serpent-CFB8
    except RuntimeError:
        # If Serpent not available, we can only do a structural check
        # ASSUMPTION: return False when crypto unavailable
        return False

    name_enc = encode_name(name)

    # Compare up to len(name_enc) bytes
    return decrypted[:len(name_enc)] == name_enc


# ---------------------------------------------------------------------------
# Quick self-test (runs without Serpent by testing only EncodeName)
# ---------------------------------------------------------------------------

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
