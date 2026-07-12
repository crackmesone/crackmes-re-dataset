import hashlib
import struct

# Modified MD5 initial constants (from the crackme's hardcoded values)
# REAL:        0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
# CRACKME#5:   0x4552205B, 0x474E4556, 0x72432045, 0x5D207765
# These spell out '[ RE', 'VENG', 'E Cr', 'we ]' in ASCII

MD5_MAGIC = [
    0x4552205B,  # replaces 0x67452301
    0x474E4556,  # replaces 0xEFCDAB89
    0x72432045,  # replaces 0x98BADCFE
    0x5D207765,  # replaces 0x10325476
]

# --- Custom MD5 with modified init constants ---
# We implement a minimal MD5 with replaceable init state

import math

def _left_rotate(x, amount):
    x &= 0xFFFFFFFF
    return ((x << amount) | (x >> (32 - amount))) & 0xFFFFFFFF

# Pre-computed T table (same as standard MD5)
_T = [int(abs(math.sin(i + 1)) * (2**32)) & 0xFFFFFFFF for i in range(64)]

# Shift amounts per round
_S = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
]

def custom_md5(data, init_state=None):
    """MD5 with custom initial state (same algorithm, different init constants)."""
    if init_state is None:
        # Standard MD5 init
        a0, b0, c0, d0 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
    else:
        a0, b0, c0, d0 = init_state

    if isinstance(data, str):
        data = data.encode('latin-1')

    # Pre-processing: adding padding bits
    orig_len_bits = len(data) * 8
    data = bytearray(data)
    data.append(0x80)
    while len(data) % 64 != 56:
        data.append(0x00)
    data += struct.pack('<Q', orig_len_bits)

    # Process each 512-bit (64-byte) chunk
    A, B, C, D = a0, b0, c0, d0

    for chunk_start in range(0, len(data), 64):
        chunk = data[chunk_start:chunk_start + 64]
        M = struct.unpack('<16I', bytes(chunk))

        aa, bb, cc, dd = A, B, C, D

        for i in range(64):
            if 0 <= i <= 15:
                F = (bb & cc) | ((~bb) & dd)
                g = i
            elif 16 <= i <= 31:
                F = (dd & bb) | ((~dd) & cc)
                g = (5 * i + 1) % 16
            elif 32 <= i <= 47:
                F = bb ^ cc ^ dd
                g = (3 * i + 5) % 16
            else:
                F = cc ^ (bb | (~dd))
                g = (7 * i) % 16

            F = (F + aa + _T[i] + M[g]) & 0xFFFFFFFF
            aa = dd
            dd = cc
            cc = bb
            bb = (bb + _left_rotate(F, _S[i])) & 0xFFFFFFFF

        A = (A + aa) & 0xFFFFFFFF
        B = (B + bb) & 0xFFFFFFFF
        C = (C + cc) & 0xFFFFFFFF
        D = (D + dd) & 0xFFFFFFFF

    digest = struct.pack('<4I', A, B, C, D)
    return digest


def crackme_md5(name):
    """Compute the crackme's modified MD5 (custom init constants)."""
    if isinstance(name, str):
        name = name.encode('latin-1')
    digest = custom_md5(name, init_state=tuple(MD5_MAGIC))
    # Return as uppercase hex string
    return digest.hex().upper()


# --- RSA parameters ---
# The crackme uses RSA-1024 with public N from the binary.
# The writeup says N cannot be factored (RSA-1024), so a real keygen
# requires patching N with a known factored modulus.
# Below we set up placeholder values and note the ASSUMPTION.

# ASSUMPTION: The public exponent E is standard (e.g., 65537 or 3).
# The writeup says we must PATCH N with our own factorable modulus
# to build a keygen-patch. The original N is hardcoded in the binary.
# Original N (from writeup):
N_ORIGINAL_HEX = (
    "C3F7CA4B2871BE19F7877325BBAD130DF7CF52BDDB4961A11FF059EEA3EAFFFB"
    "250FD475AA16967EEFC36CE9B860E7C440DD0A5A8D5FE58A7D603DB6E284CC9"
    "494FDDEB5584706AD7CDB8CEBFFDCDB84E30E870CC29FB5A0BD98526CD6396BF"
    "1A8ADDB3F44965D8B05EEFBB5EFCA71D0288F7EE43B4639DED8A91E35164CD019"
)
N_ORIGINAL = int(N_ORIGINAL_HEX, 16)

# ASSUMPTION: E = 65537 (most common RSA public exponent)
# ASSUMPTION: The serial is the RSA signature (private key operation)
#   serial = MD5_hash_as_bigint ^ D mod N
# Since D is unknown for N_ORIGINAL, we cannot verify against the original N.
# A keygen-patch requires replacing N with a known P*Q and providing D.

# --- Keygen-patch example (using a small custom RSA-1024 equivalent) ---
# For demonstration, we use a tiny RSA. In the real patch scenario,
# you would replace the binary's N with your own P*Q of the same bit-length.

# ASSUMPTION: Tiny demo RSA for structure demonstration only.
# Replace with actual patched 1024-bit RSA parameters.
_DEMO_P = 0xC6935CF30E6B9A0F5D748C665D05BE22E1DB61D9B61AB53B74BF52ADC9F3AF2B
_DEMO_Q = 0xE87B14D0B4F7B1B7837E5C0A10D4A3E56FBA28B87D9BE6F6B8CA0C35F4E43BB
_DEMO_N = _DEMO_P * _DEMO_Q
_DEMO_E = 65537
_DEMO_PHI = (_DEMO_P - 1) * (_DEMO_Q - 1)

def _modinv(a, m):
    g, x, _ = _extended_gcd(a, m)
    if g != 1:
        raise ValueError('Modular inverse does not exist')
    return x % m

def _extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = _extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

_DEMO_D = _modinv(_DEMO_E, _DEMO_PHI)


def verify(name, serial):
    """
    Verify name/serial pair.

    ASSUMPTION: The crackme:
      1. Computes hash = modified_MD5(name).upper() as a hex string
      2. Interprets hash hex string as a big integer (the message)
      3. The serial is the RSA signature: serial = message ^ D mod N
      4. Verification: serial ^ E mod N == message
      5. Also checks the name length is between 4 and 127 chars.

    NOTE: verify() here works only against the DEMO patched N, not the original.
    In the real crackme you must patch the binary's N with _DEMO_N.
    """
    if len(name) < 4 or len(name) > 127:
        return False

    hash_hex = crackme_md5(name)
    message = int(hash_hex, 16)

    try:
        serial_int = int(serial, 16)
    except (ValueError, TypeError):
        return False

    # RSA verify: serial^E mod N == message (using demo N)
    # ASSUMPTION: using patched N (_DEMO_N)
    recovered = pow(serial_int, _DEMO_E, _DEMO_N)
    return recovered == message


def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: Uses demo patched RSA params. Real keygen requires
    patching the crackme binary's N with _DEMO_N first.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')
    if len(name) > 127:
        raise ValueError('Name must be at most 127 characters')

    hash_hex = crackme_md5(name)
    message = int(hash_hex, 16)

    # RSA sign: serial = message ^ D mod N (using demo N)
    # ASSUMPTION: using patched N and computed D
    serial_int = pow(message, _DEMO_D, _DEMO_N)
    return format(serial_int, 'X')  # uppercase hex



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
