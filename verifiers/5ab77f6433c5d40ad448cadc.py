import struct

NAME_MAX_LEN = 0x15  # 21
NAME_KEY_LEN = 0x1B  # 27
NAME_MIN_LEN = 0x3

ALPH = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

# The XOR encryption key (little-endian uint32 words) from the keygen source:
# auV[0]^=0xDC217AE3
# auV[1]^=0x413D6130
# auV[2]^=0xEEFC7732
# auV[3]^=0x5129A639
# auV[4]^=0x42A74033
# auV[5]^=0xDC217AE3  (only first 0x15=21 bytes used, last word partially)
# These constants represent the XOR key that transforms expanded name bytes into
# the 21-byte decryption key (i.e., expanded_name XOR xor_constants = decryption_key)
# So: expanded_name = decryption_key XOR xor_constants
# The keygen XORs the name expansion buffer with these constants to get the
# combined 21-byte value, then encodes it to 27 base64-like characters.

XOR_WORDS = [0xDC217AE3, 0x413D6130, 0xEEFC7732, 0x5129A639, 0x42A74033, 0xDC217AE3]

def _get_xor_bytes():
    """Convert the 6 XOR uint32 words to a byte array (little-endian), take first 21 bytes."""
    result = bytearray()
    for w in XOR_WORDS:
        result += struct.pack('<I', w)
    return bytes(result[:NAME_MAX_LEN])


def _expand_name(name_bytes):
    """Expand name by repeating it up to NAME_MAX_LEN (21) bytes."""
    expanded = bytearray(NAME_MAX_LEN)
    i = 0
    while i < NAME_MAX_LEN:
        remaining = NAME_MAX_LEN - i
        chunk = name_bytes[:remaining] if remaining < len(name_bytes) else name_bytes
        expanded[i:i+len(chunk)] = chunk
        i += len(name_bytes)
    return bytes(expanded[:NAME_MAX_LEN])


def _bytes_to_base64like(data):
    """Convert 21 bytes (168 bits) into 28 base64-like chars, but we only take 27.
    Each output char indexes into ALPH using 6-bit groups.
    The C code produces NAME_KEY_LEN=27 characters from NAME_MAX_LEN=21 bytes.
    21 bytes = 168 bits, 168/6 = 28, but the loop goes iI<NAME_MAX_LEN and iR increments
    producing 28 indices (for 21 bytes at 4/3 ratio). Actually 21*8/6=28, but NAME_KEY_LEN=27.
    Let's trace the C loop carefully:
    Loop runs while iI < 21. iR cycles 0,1,2,3,...
    case 0: cC = data[iI]>>2; iI not incremented
    case 1: cC = (data[iI]&3)<<4 | data[iI+1]>>4; iI++
    case 2: cC = (data[iI]&0xF)<<2 | data[iI+1]>>6; iI++
    case 3: cC = data[iI]&0x3F; iI++
    So per 4 output chars, 3 input bytes are consumed (standard base64 encoding pattern).
    21 bytes -> 28 output chars. But NAME_KEY_LEN=27, so we take first 27.
    """
    result = bytearray()
    iI = 0
    iR = 0
    while iI < NAME_MAX_LEN:
        mode = iR & 3
        if mode == 0:
            cC = data[iI] >> 2
        elif mode == 1:
            cC = (data[iI] & 3) << 4
            iI += 1
            if iI < NAME_MAX_LEN:
                cC |= data[iI] >> 4
        elif mode == 2:
            cC = (data[iI] & 0xF) << 2
            iI += 1
            if iI < NAME_MAX_LEN:
                cC |= data[iI] >> 6
        else:  # mode == 3
            cC = data[iI] & 0x3F
            iI += 1
        result.append(ALPH[cC])
        iR += 1
    return bytes(result[:NAME_KEY_LEN])


def keygen(name):
    """Generate the serial/key for a given name string."""
    if isinstance(name, str):
        name = name.encode('ascii')

    # Validate: all chars must be in ALPH
    for b in name:
        if b not in ALPH:
            return None

    if len(name) == 0:
        return None

    # Expand name to 21 bytes
    expanded = bytearray(_expand_name(name))

    # XOR with the encryption key constants
    xor_bytes = _get_xor_bytes()
    for i in range(NAME_MAX_LEN):
        expanded[i] ^= xor_bytes[i]

    # Check no null bytes (the C code rejects keys with 0x00 before end)
    if 0 in expanded:
        return None

    # Encode to base64-like representation
    key_bytes = _bytes_to_base64like(bytes(expanded))
    return key_bytes.decode('ascii')


def verify(name, serial):
    """Verify that the serial matches the expected key for the given name."""
    expected = keygen(name)
    if expected is None:
        return False
    if isinstance(serial, bytes):
        serial = serial.decode('ascii')
    return serial == expected



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
