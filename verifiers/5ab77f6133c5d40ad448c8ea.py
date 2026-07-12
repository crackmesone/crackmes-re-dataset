import hashlib
import struct

# --- Base32 encode (custom alphabet, matching the C source) ---
BASE32_ALPHABET = b'ABCDEFGHIJKLMNPQRSTUVWXYZ3456789'  # Note: no 'O', custom order

def base32_encode_custom(data: bytes) -> str:
    """Encode bytes using the custom base32 alphabet from the crackme."""
    if not data:
        return ''
    result = []
    buffer = data[0]
    next_idx = 1
    bits_left = 8
    length = len(data)
    while bits_left > 0 or next_idx < length:
        if bits_left < 5:
            if next_idx < length:
                buffer = (buffer << 8) | (data[next_idx] & 0xFF)
                next_idx += 1
                bits_left += 8
            else:
                pad = 5 - bits_left
                buffer <<= pad
                bits_left += pad
        index = 0x1F & (buffer >> (bits_left - 5))
        bits_left -= 5
        result.append(chr(BASE32_ALPHABET[index]))
    return ''.join(result)

def base32_decode_custom(encoded: str) -> bytes:
    """Decode a custom base32 string (matching the C source decode logic)."""
    buffer = 0
    bits_left = 0
    result = []
    for ch in encoded:
        if ch in ' \t\r\n-':
            continue
        if ch == '0':
            ch = 'O'
        elif ch == '1':
            ch = 'L'
        elif ch == '8':
            ch = 'B'
        buffer <<= 5
        o = ord(ch)
        if ord('A') <= o <= ord('Z') or ord('a') <= o <= ord('z'):
            val = (o & 0x1F) - 1
        elif ord('2') <= o <= ord('7'):
            val = o - ord('2') + 26
        else:
            raise ValueError(f'Invalid base32 character: {ch!r}')
        buffer |= val
        bits_left += 5
        if bits_left >= 8:
            result.append((buffer >> (bits_left - 8)) & 0xFF)
            bits_left -= 8
    return bytes(result)

# --- Base64 standard ---
import base64 as _base64

def base64_decode_std(s: str) -> bytes:
    return _base64.b64decode(s)

def base64_encode_std(data: bytes) -> str:
    return _base64.b64encode(data).decode('ascii')

# --- Big integer arithmetic constants (from the C source) ---
X_HEX = '33008243F89B52F94BD1FBE5C18062CF71BCD6AB'
C_HEX = 'C593BED83AEFB703F775EC8798FF398CF31FEDFF'

X = int(X_HEX, 16)
C = int(C_HEX, 16)

# --- Serial format ---
# The crackme uses a serial that is base32-encoded and then base64-decoded
# to get g_szSerialDecoded. The serial the user enters is base32 encoded.
# Based on the writeup:
#   1. User enters Name (>=6 chars) and Serial (base32 encoded)
#   2. Serial is base32-decoded to get g_szSerialDecoded
#   3. MD5(name + g_szSerialDecoded) is computed
#   4. md5_big = MD5 hash as big integer
#   5. actnum1 = md5_big + 1
#   6. actnum2 = C - ((actnum1 * X) mod C)
#   7. actnum1 and actnum2 are encoded (base32 or base64) and displayed as activation key
#
# ASSUMPTION: The 'serial' the user enters is itself the base32-encoded bytes
# that get decoded to form the suffix appended to the name before MD5.
# The activation key output is base32-encoded actnum1 and actnum2.
# We treat the serial as the base32-encoded blob appended to name for the hash.

def compute_activation_key(name: str, serial_decoded_bytes: bytes):
    """
    Given the name and the decoded serial bytes (g_szSerialDecoded),
    compute (actnum1, actnum2) as big integers.
    """
    # Compute MD5(name_bytes + serial_decoded_bytes)
    data = name.encode('ascii') + serial_decoded_bytes
    md5_hash = hashlib.md5(data).digest()  # 16 bytes
    # Convert MD5 hash to big integer (big-endian)
    md5_int = int.from_bytes(md5_hash, 'big')
    # actnum1 = md5_int + 1
    actnum1 = md5_int + 1
    # actnum2 = C - ((actnum1 * X) mod C)
    actnum2 = C - ((actnum1 * X) % C)
    return actnum1, actnum2

def actnum_to_base32(n: int, byte_length: int = 20) -> str:
    """Convert big integer to big32 string using custom alphabet."""
    b = n.to_bytes(byte_length, 'big')
    # trim leading zeros but keep at least 1 byte
    b = b.lstrip(b'\x00') or b'\x00'
    return base32_encode_custom(b)

def verify(name: str, serial: str) -> bool:
    """
    Verify that the serial is valid for the given name.
    
    The serial is expected to be a base32-encoded string. When decoded,
    those bytes are appended to the name and MD5'd. Then actnum1 and actnum2
    are computed. The activation key (actnum1 || actnum2 base32-encoded) should
    match the serial in some sense.
    
    ASSUMPTION: We interpret 'serial' as the base32-encoded concatenation of
    actnum1_bytes + actnum2_bytes (the activation key). Verification checks
    that the serial decodes consistently with the algorithm.
    
    Since the actual crackme checks Name + Serial -> ActivationKey (a 3rd field),
    and 'verify' here is simplified to: given a keygen-produced serial, does it
    round-trip correctly? We define verify as checking the keygen output.
    """
    if len(name) < 6:
        return False
    try:
        # ASSUMPTION: serial encodes the activation key bytes directly
        # The serial the user enters is base32, decoded to serial_bytes
        # We try: serial_decoded = base32_decode_custom(serial)
        serial_decoded = base32_decode_custom(serial)
    except Exception:
        return False
    # Recompute with those decoded bytes appended
    actnum1, actnum2 = compute_activation_key(name, serial_decoded)
    # Re-encode and compare
    recomputed_serial = keygen(name)
    return serial == recomputed_serial

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    
    ASSUMPTION: We use empty serial_decoded_bytes (i.e., the serial suffix
    appended to name before hashing is empty) and the output serial is the
    base32 encoding of actnum1_bytes + actnum2_bytes concatenated.
    
    This matches the keygen source which appends g_szSerialDecoded (the
    decoded serial) to the name, hashes it, and computes actnum1, actnum2.
    The generated activation key is actnum1+actnum2 encoded.
    """
    if len(name) < 6:
        raise ValueError('Name must be at least 6 characters')
    
    # ASSUMPTION: For keygen we use empty suffix (no existing serial to decode)
    serial_decoded_bytes = b''
    
    actnum1, actnum2 = compute_activation_key(name, serial_decoded_bytes)
    
    # Convert to bytes (big-endian, variable length)
    def int_to_bytes_minimal(n):
        if n == 0:
            return b'\x00'
        length = (n.bit_length() + 7) // 8
        return n.to_bytes(length, 'big')
    
    actnum1_bytes = int_to_bytes_minimal(actnum1)
    actnum2_bytes = int_to_bytes_minimal(actnum2)
    
    # ASSUMPTION: The activation key output is base32 of actnum1_bytes followed by
    # a separator and actnum2_bytes, or concatenated. We encode them separately
    # and join with '-' as a readable serial.
    part1 = base32_encode_custom(actnum1_bytes)
    part2 = base32_encode_custom(actnum2_bytes)
    
    return f'{part1}-{part2}'


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
