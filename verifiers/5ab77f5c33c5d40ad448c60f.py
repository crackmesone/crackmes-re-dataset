#!/usr/bin/env python3
"""
Keygenme 6 by qptj - Reverse engineered serial validator.

From the solution writeup, the crackme uses Elliptic Curve Discrete Logarithm Problem (ECDLP)
over a prime field.

Curve parameters (from job.txt in the solution):
  GF := GF(1012325832444403)        -- prime p
  E  := EllipticCurve([GF|1012325832444400, 876059939881460])  -- a, b
  G  := E![472617234852198, 294947133781418]   -- base point
  K  := E![563102923360204, 103148785834121]   -- public point (K = k*G for unknown k)
  Group order hint: 1012325868058745  (from FactorCount comment)

The name is hashed/converted to a scalar, then used in an EC multiplication.
The serial is in the format: XXXXXXXXXXXXXX-YYYYYYYYYYYYYY (13 chars, dash, 13 chars)
where XXXXXXXXXXXXXX and YYYYYYYYYYYYYY are the x,y coordinates of a point on the curve
or some derived value.

NOTE: The exact name-to-scalar mapping (sub_401150) is not fully described in the writeup.
The serial format: 14th character (index 13) must be '-'.

Based on ECDLP structure: serial encodes a point P such that P = hash(name) * G or similar.
The check at sub_405680 likely verifies that the user-supplied point satisfies the curve equation
and some relationship to the name.
"""

# ASSUMPTION: Using Python's modular arithmetic for elliptic curve operations.

p = 1012325832444403
a = 1012325832444400
b = 876059939881460
Gx = 472617234852198
Gy = 294947133781418
Kx = 563102923360204
Ky = 103148785834121
# ASSUMPTION: group order from the comment in job.txt
n = 1012325868058745


def modinv(x, m):
    return pow(x, m - 2, m)


def point_add(P, Q):
    """Add two points on the elliptic curve y^2 = x^3 + ax + b over GF(p)"""
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if y1 != y2 or y1 == 0:
            return None  # point at infinity
        # Point doubling
        lam = (3 * x1 * x1 + a) * modinv(2 * y1, p) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def point_mul(k, P):
    """Scalar multiplication using double-and-add"""
    result = None
    addend = P
    k = k % n
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def name_to_scalar(name):
    """
    Convert name string to a scalar for EC multiplication.
    ASSUMPTION: The exact algorithm (sub_401150) is not described in the writeup.
    A common approach: sum of (char_value * position) or simple hash.
    Using a simple sum-based approach as a placeholder.
    """
    # ASSUMPTION: This is a guess at the name hashing function sub_401150.
    # The writeup mentions name is passed to sub_401150 which produces some intermediate value.
    val = 0
    for i, c in enumerate(name):
        val = (val * 31 + ord(c)) % n
    if val == 0:
        val = 1
    return val


def format_serial(point):
    """
    Format a curve point as serial: XXXXXXXXXXXXXX-YYYYYYYYYYYYYY
    The 14th character (index 13) must be '-'.
    Each coordinate is formatted as a 13-digit decimal string.
    ASSUMPTION: The serial format encodes the x and y coordinates zero-padded to 13 digits.
    """
    x, y = point
    # ASSUMPTION: serial = str(x).zfill(13) + '-' + str(y).zfill(13)
    xs = str(x).zfill(13)
    ys = str(y).zfill(13)
    return xs + '-' + ys


def parse_serial(serial):
    """
    Parse serial string into (x, y) point coordinates.
    """
    if len(serial) < 14 or serial[13] != '-':
        return None
    try:
        x = int(serial[:13])
        y = int(serial[14:])
        return (x, y)
    except ValueError:
        return None


def on_curve(P):
    """Check if point P lies on the curve."""
    if P is None:
        return True
    x, y = P
    return (y * y - x * x * x - a * x - b) % p == 0


def keygen(name):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: The scheme is: compute k = hash(name), then P = k * G, serial = format(P).
    Alternatively: P = k * G where G is the base point, or using the public key K somehow.
    """
    G = (Gx, Gy)
    k = name_to_scalar(name)
    P = point_mul(k, G)
    if P is None:
        # ASSUMPTION: fallback
        return None
    return format_serial(P)


def verify(name, serial):
    """
    Verify that the serial is valid for the given name.
    
    Checks:
    1. Name length >= 2
    2. Serial length > 2
    3. Serial[13] == '-'
    4. The point encoded in the serial matches the expected point derived from name.
    
    ASSUMPTION: The verification computes expected = hash(name) * G and compares
    with the point decoded from serial. The exact comparison function (sub_405680)
    is not fully described.
    """
    if len(name) < 2:
        return False
    if len(serial) <= 2:
        return False
    if len(serial) < 14 or serial[13] != '-':
        return False
    
    point = parse_serial(serial)
    if point is None:
        return False
    
    # ASSUMPTION: point must lie on the curve
    if not on_curve(point):
        return False
    
    G = (Gx, Gy)
    k = name_to_scalar(name)
    expected = point_mul(k, G)
    
    if expected is None:
        return False
    
    # ASSUMPTION: direct comparison of computed point with serial-encoded point
    return point == expected



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
