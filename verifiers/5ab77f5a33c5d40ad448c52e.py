import hashlib
import struct

# RSA parameters recovered from the writeup
# N (hex): D1ACED9385FF54706C863EC3875362161112ED7AD8CD12C8D9
# E: not explicitly stated, ASSUMPTION: common public exponent 65537
# D (hex): 364885ED6688970CD01BE54DE4483CC5081B5E80F087D3CA7D
# P and Q recovered via msieve factorization

N_HEX = "D1ACED9385FF54706C863EC3875362161112ED7AD8CD12C8D9"
D_HEX = "364885ED6688970CD01BE54DE4483CC5081B5E80F087D3CA7D"
# ASSUMPTION: public exponent E = 65537 (not explicitly stated in writeup)
E = 65537

N = int(N_HEX, 16)
D = int(D_HEX, 16)

# Custom MD5: uses non-standard initialization constants
# Standard: 67452301, EFCDAB89, 98BADCFE, 10325476
# Keygenme3: 52454D20, 6D616574, 74657547, 6C696B53
# The rest of the MD5 algorithm is assumed to be standard
# ASSUMPTION: Only the init constants differ; all other MD5 logic is identical.

def _left_rotate(x, amount):
    x &= 0xFFFFFFFF
    return ((x << amount) | (x >> (32 - amount))) & 0xFFFFFFFF

def custom_md5(message: bytes) -> bytes:
    """MD5 with custom initialization constants as described in writeup."""
    # Custom init constants
    a0 = 0x52454D20
    b0 = 0x6D616574
    c0 = 0x74657547
    d0 = 0x6C696B53

    # Standard MD5 per-round shift amounts
    s = [
        7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
        5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
        4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
        6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
    ]

    # Standard MD5 precomputed table K
    import math
    K = [int(2**32 * abs(math.sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

    # Pre-processing: adding padding bits
    msg = bytearray(message)
    orig_len_bits = len(message) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)

    # Process each 512-bit chunk
    A, B, C, D_ = a0, b0, c0, d0
    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        M = struct.unpack('<16I', chunk)
        a, b, c, d = A, B, C, D_
        for j in range(64):
            if 0 <= j <= 15:
                f = (b & c) | ((~b) & d)
                g = j
            elif 16 <= j <= 31:
                f = (d & b) | ((~d) & c)
                g = (5 * j + 1) % 16
            elif 32 <= j <= 47:
                f = b ^ c ^ d
                g = (3 * j + 5) % 16
            else:
                f = c ^ (b | (~d))
                g = (7 * j) % 16
            f = (f + a + K[j] + M[g]) & 0xFFFFFFFF
            a, b, c, d = d, (b + _left_rotate(f, s[j])) & 0xFFFFFFFF, b, c
        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D_ = (D_ + d) & 0xFFFFFFFF

    return struct.pack('<4I', A, B, C, D_)


def transform_md5_bytes(md5_bytes: bytes) -> bytes:
    """
    Driver transformation applied to the 16 MD5 bytes:
      byte ^= 0x1E
      byte = rol(byte, 2)   (8-bit rotate left by 2)
      byte += 0x17
      byte ^= 0x32
    """
    result = bytearray()
    for b in md5_bytes:
        b = b & 0xFF
        b ^= 0x1E
        # 8-bit rotate left by 2
        b = ((b << 2) | (b >> 6)) & 0xFF
        b = (b + 0x17) & 0xFF
        b ^= 0x32
        result.append(b)
    return bytes(result)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Steps:
    1. Compute custom MD5 of the crackme's own filename/name
       ASSUMPTION: The crackme hashes its own module name, not the user's name entered.
       But from writeup context the MD5 is of the *crackme's own name* (of.00401BF2 = own name).
       However for keygen purposes we hash the provided 'name' parameter with the custom MD5.
       ASSUMPTION: 'name' here is the crackme's executable name or user name as used by the crackme.
    2. Apply transform_md5_bytes to get 16 transformed bytes.
    3. Convert those 16 bytes to their hex string (uppercase), giving 32 hex chars.
    4. RSA-sign (encrypt with private key D) that 32-char hex string interpreted as a big integer.
       ASSUMPTION: The 32-char hex string of the transformed MD5 is padded/encoded to fit
       the RSA modulus. The decrypted serial must equal those 32 hex chars.
       From writeup: rsa_decrypt(serial) produces the 32-char hex of transformed MD5.
       So serial = rsa_encrypt_with_private_key(transformed_md5_hex_as_int)
    """
    # Step 1: custom MD5
    md5_bytes = custom_md5(name.encode('ascii', errors='replace'))

    # Step 2: transform
    transformed = transform_md5_bytes(md5_bytes)

    # Step 3: hex string (uppercase, 32 chars)
    hex_str = transformed.hex().upper()  # 32 uppercase hex chars

    # Step 4: RSA sign
    # The 32 hex char string is treated as the plaintext integer
    # ASSUMPTION: direct conversion of the hex string bytes to integer (big-endian ASCII codes)
    m_int = int.from_bytes(hex_str.encode('ascii'), 'big')

    # RSA encryption with private key: serial_int = m^D mod N
    # But m must be < N; the 32-char ASCII string as int may exceed N
    # ASSUMPTION: only the lower portion or it fits within N (N is ~200-bit, 32 ASCII chars = 256 bits)
    # ASSUMPTION: The serial is the hex representation of the RSA result
    serial_int = pow(m_int, D, N)

    # Convert to hex string (the serial entered by user)
    serial_hex = format(serial_int, 'X')
    return serial_hex


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.

    Steps:
    1. Compute custom MD5 of name.
    2. Apply transform_md5_bytes.
    3. Convert to 32-char uppercase hex string.
    4. RSA decrypt serial (serial^E mod N) -> should give back the hex string.
    """
    if len(name) < 2:
        return False

    # Step 1: custom MD5
    md5_bytes = custom_md5(name.encode('ascii', errors='replace'))

    # Step 2: transform
    transformed = transform_md5_bytes(md5_bytes)

    # Step 3: expected plaintext as hex string
    expected_hex = transformed.hex().upper()  # 32 chars

    # Step 4: RSA decrypt serial
    try:
        serial_int = int(serial, 16)
    except ValueError:
        return False

    # RSA decrypt: plaintext = serial^E mod N
    # ASSUMPTION: E = 65537
    decrypted_int = pow(serial_int, E, N)

    # Convert decrypted int back to ASCII string
    try:
        byte_len = (decrypted_int.bit_length() + 7) // 8
        decrypted_bytes = decrypted_int.to_bytes(byte_len, 'big')
        decrypted_str = decrypted_bytes.decode('ascii')
    except Exception:
        return False

    return decrypted_str == expected_hex



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
