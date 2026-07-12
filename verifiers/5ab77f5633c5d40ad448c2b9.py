# tkm_trial_2004 by amenesia
# ECC-based serial check using MIRACL big number library
# The crackme uses Elliptic Curve Cryptography over a 128-bit prime field.
#
# From the writeup we can extract the ECC curve parameters and some constants.
# The writeup is truncated so we cannot fully reconstruct the verification equation.
# We implement what we can derive from the visible assembly.
#
# Curve parameters (from cinstr calls in the binary):
#   p2 = 0xFFFFFFFE000000006FAFED9C3353F08D  (possibly p^2 or related)
#   a  = 0x416D656E65736961  ("Amenesia" in hex ASCII!)
#   b  = 0x1B35B7093FEE5AE601A
#   p  = 0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF  (field prime)
#   Gx = 0x71263A72C2FDFB8FE851182B408210A4  (base point x)
#   (Gy not shown in truncated writeup)
#
# The serial consists of two parts:
#   Serial_1 (field 3 in dialog, length >= 4)
#   Serial_2 (field 4 in dialog, length >= 1)
#
# ASSUMPTION: The check is a standard ECDSA-like or scalar-multiplication check:
#   scalar_from(Serial_1) * G == point_derived_from(name, Serial_2)
# or equivalently:
#   point_from_name_hash * Serial_2_scalar == Serial_1_scalar * G
#
# Because the writeup is truncated, we cannot determine:
#   1. How the name is hashed/converted to a big number
#   2. The exact verification equation
#   3. The y-coordinate of the base point
#   4. Whether Serial_1/Serial_2 are hex strings or decimal
#
# We provide a skeleton with all known constants.

try:
    from sympy.ntheory.residues import n_order
except ImportError:
    pass

# Known curve parameters
P  = 0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF  # field prime
A  = 0x416D656E65736961                  # curve coefficient a ("Amenesia")
B  = 0x1B35B7093FEE5AE601A               # curve coefficient b
GX = 0x71263A72C2FDFB8FE851182B408210A4  # base point x
# ASSUMPTION: GY must be computed from curve equation; not given in truncated writeup
P2 = 0xFFFFFFFE000000006FAFED9C3353F08D  # unknown role - possibly group order or p^2 mod something

def mod_sqrt(n, p):
    """Tonelli-Shanks square root mod p."""
    if pow(n, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(n, (p + 1) // 4, p)
    # General Tonelli-Shanks
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(n, q, p), pow(n, (q + 1) // 2, p)
    while True:
        if t == 1:
            return r
        i, tmp = 1, (t * t) % p
        while tmp != 1:
            tmp = (tmp * tmp) % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, (b * b) % p, (t * b * b) % p, (r * b) % p

def point_add(P1, P2, a, p):
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if y1 != y2:
            return None  # point at infinity
        # Point doubling
        lam = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mult(k, point, a, p):
    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend, a, p)
        addend = point_add(addend, addend, a, p)
        k >>= 1
    return result

def get_base_point():
    """Compute base point G = (GX, GY) on the curve y^2 = x^3 + A*x + B mod P."""
    rhs = (pow(GX, 3, P) + A * GX + B) % P
    gy = mod_sqrt(rhs, P)
    if gy is None:
        raise ValueError("GX is not on the curve with given parameters")
    # ASSUMPTION: we pick the smaller root; real code may pick either
    return (GX, gy)

def name_to_big(name):
    """Convert name string to a big integer.
    ASSUMPTION: name bytes are used directly (little-endian or big-endian).
    The actual hash/conversion is not shown in the truncated writeup."""
    b = name.encode('ascii', errors='replace')
    val = 0
    for byte in b:
        val = (val << 8) | byte
    return val

def verify(name, serial):
    """
    ASSUMPTION: serial format is 'SERIAL1:SERIAL2' where both are hex strings.
    The actual verification equation is not fully known from the truncated writeup.
    This implements a plausible ECC check:
      serial1_int * G == serial2_int * name_point
    but this is ASSUMED, not confirmed.
    """
    if ':' not in serial:
        return False
    parts = serial.split(':', 1)
    serial1_str, serial2_str = parts[0].strip(), parts[1].strip()
    if len(serial1_str) < 4 or len(serial2_str) < 1:
        return False
    try:
        s1 = int(serial1_str, 16)
        s2 = int(serial2_str, 16)
    except ValueError:
        return False

    try:
        G = get_base_point()
    except ValueError:
        # ASSUMPTION: parameters might be slightly off due to truncation
        return False

    # ASSUMPTION: group order is P2 (common in such crackmes)
    order = P2

    name_val = name_to_big(name)

    # ASSUMPTION: verification is s1*G == s2 * (name_val * G)
    # i.e., s1 = s2 * name_val (mod order)
    lhs = scalar_mult(s1 % order, G, A, P)
    rhs = scalar_mult((s2 * name_val) % order, G, A, P)

    return lhs == rhs

def keygen(name):
    """
    ASSUMPTION: generate serial such that s1 = s2 * name_val (mod order).
    We pick a random s2 and compute s1.
    """
    import random
    order = P2
    name_val = name_to_big(name)
    if name_val == 0:
        raise ValueError("Name results in zero - cannot generate serial")
    s2 = random.randint(1, order - 1)
    s1 = (s2 * name_val) % order
    return f"{s1:032X}:{s2:032X}"


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
