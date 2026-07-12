# Crackme "Optimize" by kao - Key/Serial Validation Algorithm
# Reconstructed from writeup by stan4oo
#
# Algorithm summary:
# 1. Name must be 3..32 chars. If < 10 chars, extend by repeating name chars until 10 chars.
# 2. Serial is read; length must satisfy: (len(serial) // 4) * 3 == len(extended_name)
#    i.e., len(serial) = len(extended_name) * 4 // 3
#    For name len 10 (extended), serial len = (10 * 4) / 3 -- must be integer, so we need len divisible by 3
#    Actually: hash_len = (serial_len >> 2) * 3  => hash_len == extended_name_len
#    => serial_len must be multiple of 4, and (serial_len//4)*3 == extended_name_len
# 3. Each group of 4 serial bytes is processed:
#    a. Each byte goes through a substitution (second part / 0040103B routine)
#    b. Then a bit-packing loop converts 4 bytes -> 3 bytes (base64-like decode)
# 4. The resulting bytes must equal the (extended) name bytes.
#
# The substitution at 0040103B maps a serial character to a 6-bit value:
#   if char == '=' (0x3D): value = 0, EDX-- (padding)
#   elif char <= '/' (0x2F): value = (char - 0x2B) >> 2 + 0x3E  (handles '+' and '/')
#     '+' = 0x2B => (0x2B-0x2B)>>2 + 0x3E = 0x3E = 62
#     '/' = 0x2F => (0x2F-0x2B)>>2 + 0x3E = 1 + 62 = 63
#   elif char <= '9' (0x39): value = char + 4   # '0'-'9' -> 52-61
#   else (A-Z, a-z):
#     value = char - 0x41
#     if value > 0x19: value -= 6  # a-z: 0x61-0x41=0x20, 0x20-6=0x1A=26 => a->26, z->51
#
# This is essentially standard Base64 decoding with alphabet:
# A-Z=0-25, a-z=26-51, 0-9=52-61, +=62, /=63, ==padding
# (Standard base64 alphabet!)
#
# The bit-packing (first loop) takes 4 6-bit values and packs them into 3 bytes,
# then BSWAP and shifts produce 3 output bytes -- this matches standard base64 decode.
#
# ASSUMPTION: The algorithm is essentially standard Base64 encoding.
# The serial is the base64 encoding of the (extended) name.
# The keyfile part is NOT implemented here (it requires a separate file).

import base64

def extend_name(name):
    """Extend name to at least 10 chars by repeating it."""
    if len(name) >= 10:
        return name
    result = list(name)
    i = 0
    while len(result) < 10:
        result.append(name[i % len(name)])
        i += 1
    return ''.join(result)

# The substitution mapping (from 0040103B disassembly)
def serial_char_to_value(c):
    """Map a serial character to its 6-bit value, returns -1 for padding."""
    b = ord(c)
    if b == 0x3D:  # '='
        return 0  # padding
    elif b <= 0x2F:  # '+' or '/'
        return ((b - 0x2B) >> 2) + 0x3E
    elif b <= 0x39:  # '0'-'9'
        return b + 4
    else:
        val = b - 0x41
        if val > 0x19:
            val -= 6
        return val

def value_to_serial_char(v):
    """Inverse: map a 6-bit value to a serial character."""
    # Reverse the mapping
    # val <= 25: A-Z
    if 0 <= v <= 25:
        return chr(v + 0x41)  # 'A'-'Z'
    # val 26-51: a-z
    elif 26 <= v <= 51:
        return chr(v + 6 + 0x41)  # v+6+0x41: 26+6+0x41=0x61='a'
    # val 52-61: '0'-'9'
    elif 52 <= v <= 61:
        return chr(v - 4)
    elif v == 62:
        return '+'
    elif v == 63:
        return '/'
    else:
        return '='

def decode_serial(serial):
    """Decode serial to bytes using the crackme's algorithm."""
    # serial length must be multiple of 4
    if len(serial) % 4 != 0:
        return None
    result = []
    for i in range(0, len(serial), 4):
        group = serial[i:i+4]
        # Get 4 6-bit values
        vals = [serial_char_to_value(c) for c in group]
        # Pack 4x6 bits into 3 bytes
        # Standard base64 decode bit packing
        b0 = ((vals[0] << 2) | (vals[1] >> 4)) & 0xFF
        b1 = ((vals[1] << 4) | (vals[2] >> 2)) & 0xFF
        b2 = ((vals[2] << 6) | (vals[3])) & 0xFF
        result.extend([b0, b1, b2])
    return bytes(result)

def encode_to_serial(data):
    """Encode bytes to serial using the crackme's base64-like algorithm."""
    # Pad data to multiple of 3
    result = []
    padding = (3 - len(data) % 3) % 3
    data = data + b'\x00' * padding
    for i in range(0, len(data), 3):
        b0, b1, b2 = data[i], data[i+1], data[i+2]
        v0 = (b0 >> 2) & 0x3F
        v1 = ((b0 << 4) | (b1 >> 4)) & 0x3F
        v2 = ((b1 << 2) | (b2 >> 6)) & 0x3F
        v3 = b2 & 0x3F
        result.append(value_to_serial_char(v0))
        result.append(value_to_serial_char(v1))
        if i + 1 < len(data) - padding:
            result.append(value_to_serial_char(v2))
        else:
            result.append('=')
        if i + 2 < len(data) - padding:
            result.append(value_to_serial_char(v3))
        else:
            result.append('=')
    return ''.join(result)

def verify(name, serial):
    """Verify that serial is valid for name."""
    # Name length check
    if len(name) < 3 or len(name) > 32:
        return False
    # Extend name if needed
    ext_name = extend_name(name)
    # Serial length check: (len(serial)//4)*3 must equal len(ext_name)
    if len(serial) % 4 != 0:
        return False
    expected_hash_len = (len(serial) // 4) * 3
    if expected_hash_len != len(ext_name):
        return False
    # Decode serial and compare with extended name
    decoded = decode_serial(serial)
    if decoded is None:
        return False
    return decoded == ext_name.encode('ascii')

def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) < 3 or len(name) > 32:
        raise ValueError("Name must be 3..32 chars")
    ext_name = extend_name(name)
    return encode_to_serial(ext_name.encode('ascii'))


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
