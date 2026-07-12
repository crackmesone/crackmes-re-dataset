# Chili Crackme 11 by witeg - Partial Reverse Engineering
#
# From the writeup we can see:
# 1. The crackme uses Elliptic Curve cryptography over a small prime field
# 2. The prime modulus is p = 0x28511B (= 2642203 decimal)
# 3. Some curve parameters: param_A = [0x1E3CB, 0x269C87, 0x46185]
# 4. There is a Base64 encoding step involved
# 5. The serial is validated by EC point multiplication using parts of the B64-encoded name
# 6. The EC operations work with 96-bit (3 x 32-bit dword) numbers under mod p
#
# The full validation flow is NOT completely recoverable from the truncated writeup.
# Key missing pieces:
#   - Exact curve equation coefficients (a, b)
#   - The generator point G coordinates
#   - How the name is hashed/transformed before EC multiplication
#   - How the serial is parsed and compared to the EC result
#   - The exact structure of the 'poly' (point representation: 7 dwords)
#
# ASSUMPTION: The poly structure is [flag, x0, x1, x2, y0, y1, y2] where
#             x = (x0, x1, x2) and y = (y0, y1, y2) are 96-bit coords mod p
# ASSUMPTION: p = 0x28511B is the field prime for all coordinates
# ASSUMPTION: The B64 of the name provides scalar multiplier bytes b64[2] and b64[3]

import base64
import struct

P = 0x28511B  # Prime from dword_40409C

# ASSUMPTION: These are curve parameters but their exact role is unclear
param_A = [0x1E3CB, 0x269C87, 0x46185]

# Custom B64 alphabet (standard)
B64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def b64encode_custom(data: bytes) -> bytes:
    """Standard base64 encoding as shown in b64.asm (uses standard alphabet)."""
    # The asm implements standard base64
    return base64.b64encode(data)

def mod_inverse(a, p):
    """Modular inverse using extended Euclidean algorithm."""
    # ASSUMPTION: standard modular inverse mod p
    if a == 0:
        raise ZeroDivisionError('Inverse of zero')
    return pow(a, p - 2, p)

def ec_add(P1, P2, p):
    """
    Add two points on elliptic curve mod p.
    Points represented as (x, y) or None for point at infinity.
    ASSUMPTION: Short Weierstrass form, exact 'a' coefficient unknown.
    """
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 != y2:
            return None  # Point at infinity
        # Double
        return ec_double(P1, p)
    # Standard add
    lam = ((y2 - y1) * mod_inverse(x2 - x1, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def ec_double(P1, p):
    """
    Double a point on elliptic curve mod p.
    ASSUMPTION: curve parameter a=0 (unknown, using 0 as placeholder)
    """
    if P1 is None:
        return None
    x1, y1 = P1
    if y1 == 0:
        return None
    # ASSUMPTION: a = 0
    a = 0  # ASSUMPTION: unknown curve parameter
    lam = ((3 * x1 * x1 + a) * mod_inverse(2 * y1, p)) % p
    x3 = (lam * lam - 2 * x1) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def ec_multiply(k, G, p):
    """Scalar multiplication k*G on elliptic curve mod p."""
    result = None
    addend = G
    while k:
        if k & 1:
            result = ec_add(result, addend, p)
        addend = ec_double(addend, p)
        k >>= 1
    return result

def name_to_scalar(name: str) -> int:
    """
    ASSUMPTION: The name is B64-encoded and bytes at indices 2 and 3
    of the B64 output are used as the scalar (96-bit from 3 dwords).
    The exact transformation is not fully recoverable from the truncated writeup.
    """
    name_bytes = name.encode('ascii')
    b64_bytes = b64encode_custom(name_bytes)
    # ASSUMPTION: use b64[2], b64[3], b64[4] as little-endian dwords for scalar
    # From asm: ebx = b64[2], ecx = b64[3], edx = b64[4] (=0?)
    if len(b64_bytes) < 4:
        b64_bytes = b64_bytes + b'A' * 4
    b2 = b64_bytes[2] if len(b64_bytes) > 2 else 0
    b3 = b64_bytes[3] if len(b64_bytes) > 3 else 0
    # ASSUMPTION: scalar = (b3 << 8) | b2  (simplistic, actual is 96-bit)
    scalar = (b3 << 8) | b2
    return scalar

# ASSUMPTION: Generator point G - completely unknown, placeholder values
# ASSUMPTION: G = (Gx, Gy) on the curve y^2 = x^3 + a*x + b mod P
G = (0x1E3CB, 0x46185)  # ASSUMPTION: placeholder, actual values unknown

def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The serial encodes the expected EC point result.
    The exact encoding/comparison is not recoverable from the truncated writeup.
    This is a skeleton only - NOT the real algorithm.
    """
    # ASSUMPTION: serial is hex-encoded x-coordinate of k*G
    try:
        expected_x = int(serial, 16)
    except ValueError:
        return False
    
    k = name_to_scalar(name)
    if k == 0:
        return False
    
    # ASSUMPTION: generator point and curve are unknown
    point = ec_multiply(k, G, P)
    if point is None:
        return False
    
    # ASSUMPTION: compare x-coordinate
    return point[0] == expected_x

def keygen(name: str) -> str:
    """
    ASSUMPTION: Generate serial as hex of x-coordinate of k*G.
    NOT the real keygen - algorithm is only partially recovered.
    """
    k = name_to_scalar(name)
    point = ec_multiply(k, G, P)
    if point is None:
        return 'INVALID'
    return hex(point[0])[2:].upper()


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
