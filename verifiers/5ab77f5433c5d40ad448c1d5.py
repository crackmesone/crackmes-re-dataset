import hashlib
from Crypto.Cipher import DES, AES
from Crypto.Util.Padding import pad, unpad
import math

# ASSUMPTION: We reconstruct calcNum4() directly from the VB.NET formula.
# num4 starts at 1, then:
# num4 = Round( num4 + (((0x293b + (0x529f * Int(0x3e8))) + Asc(Str(num4))) * 60 / 50.0 * 88558.0) + 3747046.6659540348 )
# then num4 += 1
# Int(0x3e8) = Int(1000) = 1000
# Str(num4) with num4=1 in VB gives " 1" (leading space for positive numbers)
# Asc(" 1") = Asc(" ") = 32  -- first char of Str(1) in VB is space

def calc_num4():
    num4 = 1
    # VB Conversion.Int(0x3e8) = math.floor(1000) = 1000
    vb_int_3e8 = 1000
    # VB Strings.Asc(Conversions.ToString(num4)) where num4=1
    # VB Str(1) returns " 1", Asc(" 1") = ord(' ') = 32
    # ASSUMPTION: VB Str() for positive long prepends a space, so Str(1) = " 1"
    asc_val = 32  # ord(' ') from VB Str(1) = " 1"
    inner = (0x293b + (0x529f * vb_int_3e8) + asc_val) * 60
    num4 = round(num4 + (inner / 50.0 * 88558.0) + 3747046.6659540348)
    num4 += 1
    return num4


def to_ascii_hex(inp: str) -> str:
    """Convert each character to its ASCII hex (two digits, uppercase)."""
    result = ''
    for ch in inp:
        h = format(ord(ch), '02X')
        result += h
    return result


# ASSUMPTION: myDEX.rijn() is a Rijndael (AES) encryption function.
# It takes two string parameters: (data, key).
# The key and IV are derived from the second parameter (Str(num4)).
# We don't have the exact myDEX source, so we make reasonable assumptions:
# - rijn(data, key_str): uses AES with key derived from key_str
# - DEScryKey is set to rijn(Str(num4), Str(num4)) then used as DES key
# - DESencrypt uses that key

# ASSUMPTION: rijn pads key to 32 bytes (AES-256) using UTF8, zero-padded or hashed
# ASSUMPTION: rijn uses ECB mode (common in simple crackmes)
# ASSUMPTION: DESencrypt uses DES in ECB mode with the DEScryKey

def derive_aes_key(key_str: str) -> bytes:
    """Derive a 32-byte AES key from a string by zero-padding or truncating."""
    # ASSUMPTION: key is UTF-8 encoded and zero-padded to 32 bytes
    key_bytes = key_str.encode('utf-8')
    key_bytes = key_bytes[:32].ljust(32, b'\x00')
    return key_bytes


def derive_des_key(key_str: str) -> bytes:
    """Derive an 8-byte DES key from a string."""
    # ASSUMPTION: DES key is first 8 bytes of key_str encoded as UTF-8, zero-padded
    key_bytes = key_str.encode('utf-8')
    key_bytes = key_bytes[:8].ljust(8, b'\x00')
    return key_bytes


def rijn(data: str, key_str: str) -> str:
    """AES encrypt data string with key derived from key_str, return result as string.
    ASSUMPTION: AES-256 ECB mode, PKCS7 padding, result decoded as latin-1.
    """
    key = derive_aes_key(key_str)
    data_bytes = data.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded = pad(data_bytes, 16)
    encrypted = cipher.encrypt(padded)
    # ASSUMPTION: result is returned as latin-1 string to preserve bytes
    return encrypted.decode('latin-1')


def des_encrypt(data: str, des_key_str: str) -> str:
    """DES encrypt data with given key string.
    ASSUMPTION: DES ECB mode, PKCS7 padding, result as latin-1 string.
    """
    key = derive_des_key(des_key_str)
    data_bytes = data.encode('utf-8')
    cipher = DES.new(key, DES.MODE_ECB)
    padded = pad(data_bytes, 8)
    encrypted = cipher.encrypt(padded)
    return encrypted.decode('latin-1')


def keygen(name: str) -> str:
    num4 = calc_num4()
    num4_str = ' ' + str(num4)  # ASSUMPTION: VB Str(num4) prepends space for positive

    # Step 1: Set DES key = rijn(Str(num4), Str(num4))
    des_cry_key = rijn(num4_str, num4_str)

    # Step 2: DES encrypt user name
    user_cry = des_encrypt(name, des_cry_key)

    # Step 3: toASCIIhex of user_cry
    s2 = to_ascii_hex(user_cry)

    # Step 4: toASCIIhex of (s2 + s2 + s2)
    s3 = to_ascii_hex(s2 + s2 + s2)

    # Step 5: rijn(s3, Str(num4))
    s4 = rijn(s3, num4_str)

    # Step 6: toASCIIhex of s4
    s5 = to_ascii_hex(s4)

    # Step 7: Mid(s5, 23, 73) -> 1-based, chars 23..95
    # Python: s5[22:22+73]
    s6 = s5[22:22+73]

    return s6


def verify(name: str, serial: str) -> bool:
    expected = keygen(name)
    return expected == serial



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
