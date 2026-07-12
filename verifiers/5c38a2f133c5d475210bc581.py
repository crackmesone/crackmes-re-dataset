import os
import struct

# Algorithm fully recovered from solution writeup by 321test123
# Key format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX (29 chars, dashes are ignored)
# Username must be >= 4 characters
# The mapping used for encoding/decoding the password
MAPPING = list('123456789ABCDEFGHIJKLMNPQRSTUVWXYZ')
# Note: 'O' and '0' are absent from mapping - length is 34 chars
# ASSUMPTION: mapping is exactly '123456789ABCDEFGHIJKLMNPQRSTUVWXYZ' = 34 chars = 0x22
assert len(MAPPING) == 0x22, f"Mapping length is {len(MAPPING)}"


def _extend_login(login, length=16):
    """Extend login to exactly `length` bytes by repeating it cyclically (with null terminator).
    Based on description: loginloginlogin pattern with null terminator."""
    # ASSUMPTION: login is repeated with null terminators to fill 16 bytes
    # From keygen.py: ((login + '\0') * 4)[0:16]
    extended = ((login + '\0') * 4)[:length]
    return extended.encode('ascii')


def _crc16_ccitt(data):
    """CRC16-CCITT (polynomial 0x1021) over the provided bytes.
    From the keygen.py code: uses the loop with 0x8000 check and XOR with 0x1021.
    This is applied to 30 bytes of the combined array."""
    output = 0
    for x in data:
        x <<= 8
        output ^= x
        for _ in range(8):
            if (output & 0x8000) != 0:
                output = (output * 2) ^ 0x1021
            else:
                output *= 2
            output &= 0xFFFF  # keep 16 bits
    return output & 0xFFFF


def _compute_checksum(login, random14):
    """
    Build the 30-byte array from login (16 bytes) + first 14 bytes of encrypted password.
    The checksum is a 2-byte CRC16 computed over those 30 bytes.
    The encrypted password is: random14 (14 bytes) + checksum (2 bytes).
    So we compute checksum from login_extended (16 bytes) + random14 (14 bytes) = 30 bytes.
    """
    login_bytes = _extend_login(login, 16)
    arr30 = login_bytes + random14  # 16 + 14 = 30 bytes
    return _crc16_ccitt(arr30)


def _encrypted_password_to_key(enc_int):
    """
    Convert the 128-bit encrypted password integer to a 25-char key string,
    then format with dashes.
    enc_int is a big integer (up to 16 bytes).
    Encoding: repeatedly mod 0x22 to get offsets into MAPPING.
    """
    password_chars = []
    tmp = enc_int
    for _ in range(25):
        password_chars.append(MAPPING[tmp % 0x22])
        tmp //= 0x22
    if tmp != 0:
        raise ValueError('Encrypted password too large to encode in 25 chars')
    # Characters were built LSB first, reverse to get correct order
    password_chars.reverse()
    pw = ''.join(password_chars)
    return f"{pw[0:5]}-{pw[5:10]}-{pw[10:15]}-{pw[15:20]}-{pw[20:25]}"


def _key_to_encrypted_password(key):
    """
    Parse key string (with or without dashes) back to the encrypted password integer.
    Ignores dashes.
    """
    stripped = key.replace('-', '')
    if len(stripped) != 25:
        return None
    enc = 0
    for ch in stripped:
        if ch not in MAPPING:
            return None
        offset = MAPPING.index(ch)
        enc = enc * 0x22 + offset
    return enc


def _encrypted_password_to_bytes(enc_int):
    """Convert 128-bit integer to 16 bytes (little-endian)."""
    return enc_int.to_bytes(16, byteorder='little')


def verify(name, serial):
    """
    Verify a name/serial pair.
    Returns True if valid, False otherwise.
    """
    if len(name) < 4:
        return False

    # Strip dashes from serial
    stripped = serial.replace('-', '')
    if len(stripped) != 25:
        return False

    # Decode serial to encrypted password integer
    enc_int = _key_to_encrypted_password(serial)
    if enc_int is None:
        return False

    # Convert encrypted password to 16 bytes
    enc_bytes = _encrypted_password_to_bytes(enc_int)

    # The encrypted password is: random14 (bytes 0..13) + checksum (bytes 14..15)
    # checksum is stored as: high byte at index 14, low byte at index 15
    # From keygen.py: encryptedPassword = ((output & 0xFF00) << (13*8)) | ((output & 0xFF) << (15*8)) | int.from_bytes(randomBytes, ...)
    # Byte 14 (index from LSB in 16-byte little-endian):
    #   ((output & 0xFF00) << (13*8)) -> this puts the high byte of crc into byte index 15 (0-based from LSB)
    #   ((output & 0xFF) << (15*8))   -> this puts the low byte of crc into byte index 15 ... 
    # ASSUMPTION: Let's re-derive from the keygen source code directly.
    # encryptedPassword = ((output & 0xFF00) << (13*8)) | ((output & 0xFF) << (15*8)) | randomBytes_as_int
    # In little-endian bytes:
    #   bytes 0..13 = random14
    #   byte 14 = (output >> 8) & 0xFF  [from (output & 0xFF00) << 104, byte 13 = bits 104..111]
    #   byte 15 = output & 0xFF         [from (output & 0xFF) << 120, byte 15 = bits 120..127]
    # Wait, let's be careful:
    # (output & 0xFF00) << (13*8):
    #   output & 0xFF00 = crc_high_byte << 8
    #   shift left by 104 bits -> byte position 13+1=14? No.
    #   In a 128-bit integer stored little-endian:
    #     byte N corresponds to bits N*8 .. N*8+7
    #   (output & 0xFF00) = bits 8..15 of output, i.e., crc_high in bits 8..15
    #   shift left 13*8=104: now crc_high is in bits 112..119 -> byte 14
    #   (output & 0xFF) = bits 0..7 of output, i.e., crc_low
    #   shift left 15*8=120: now crc_low is in bits 120..127 -> byte 15
    # So enc_bytes[14] = crc_high_byte, enc_bytes[15] = crc_low_byte
    # i.e., crc16 = (enc_bytes[14] << 8) | enc_bytes[15]

    random14 = enc_bytes[0:14]
    stored_crc_high = enc_bytes[14]
    stored_crc_low = enc_bytes[15]
    stored_checksum = (stored_crc_high << 8) | stored_crc_low

    # Compute expected checksum
    expected_checksum = _compute_checksum(name, random14)

    return stored_checksum == expected_checksum


def keygen(name):
    """
    Generate a valid serial for the given name.
    Returns a serial string in XXXXX-XXXXX-XXXXX-XXXXX-XXXXX format.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')

    while True:
        # Generate 14 random bytes
        random14 = os.urandom(14)

        # Compute checksum
        checksum = _compute_checksum(name, random14)

        crc_high = (checksum >> 8) & 0xFF
        crc_low = checksum & 0xFF

        # Build encrypted password integer (128-bit, little-endian)
        # bytes 0..13 = random14, byte 14 = crc_high, byte 15 = crc_low
        enc_bytes = random14 + bytes([crc_high, crc_low])
        enc_int = int.from_bytes(enc_bytes, byteorder='little')

        # Try to encode to 25 chars
        try:
            serial = _encrypted_password_to_key(enc_int)
            # Verify before returning
            if verify(name, serial):
                return serial
        except ValueError:
            continue  # Try again with new random bytes



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
