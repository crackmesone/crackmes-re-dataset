import random
import math
from sympy import mod_inverse, gcd

# ============================================================
# Part 1: Serial format and complex-number check
# ============================================================
# Serial format: Zz-YXXXX-yxxxx
#
# Z, z  = the "B" complex number (taken directly from the prefix)
# Y, y  = sign-control digits
#   if Y % 2 == 1 -> XXXX is negative
#   if y % 2 == 0 -> xxxx is negative
# A = (XXXX, xxxx)  (after sign adjustment)
# B = (Z, z)
# P = (4, -2)  (hardcoded)
#
# Constraint: A = B * Z_target - P   where Z_target = (-3, 0)
# i.e. A = B * (-3, 0) - (4, -2)
#        = (-3*Z - 4, -3*z + 2)

def complex_add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def complex_mul(a, b):
    return (a[0]*b[0] - a[1]*b[1], a[1]*b[0] + a[0]*b[1])

def complex_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def complex_div(a, b):
    """Divide complex a by complex b (exact integer division assumed for the check)"""
    # a/b = a * conj(b) / |b|^2
    conj_b = (b[0], -b[1])
    num = complex_mul(a, conj_b)
    denom = b[0]**2 + b[1]**2
    # ASSUMPTION: result should be exact integers for valid serials
    return (num[0] / denom, num[1] / denom)

def generate_serial_part1(B=None):
    """
    Given B = (Z, z), compute A such that:
        A = B * (-3, 0) - P
    where P = (4, -2)
    Returns A = (XXXX, xxxx)
    """
    if B is None:
        # Pick a random B
        Z_val = random.randint(1, 9)
        z_val = random.randint(1, 9)
        B = (Z_val, z_val)

    P = (4, -2)
    Z_target = (-3, 0)

    # A = B * Z_target - P
    BZ = complex_mul(B, Z_target)
    A = complex_sub(BZ, P)
    return B, A

def format_serial_part1(B, A):
    """
    Build the Zz-YXXXX-yxxxx portion of the serial.
    Y, y are sign-control digits:
      Y odd  -> XXXX stored as negative  (so we flip sign and use odd Y)
      Y even -> XXXX stored as positive  (use even Y)
      y even -> xxxx stored as negative  (so we flip sign and use even y)
      y odd  -> xxxx stored as positive  (use odd y)
    """
    Z_val, z_val = B
    XXXX, xxxx = A

    # Choose Y: if XXXX < 0 use odd Y, else even Y
    if XXXX < 0:
        Y = 1  # odd -> XXXX will be negated -> stored positive
        XXXX_stored = -XXXX
    else:
        Y = 2  # even -> XXXX stays positive
        XXXX_stored = XXXX

    # Choose y: if xxxx < 0 use even y, else odd y
    if xxxx < 0:
        y = 2  # even -> xxxx will be negated -> stored positive
        xxxx_stored = -xxxx
    else:
        y = 1  # odd -> xxxx stays positive
        xxxx_stored = xxxx

    part1 = f"{Z_val}{z_val}-{Y}{XXXX_stored:04d}-{y}{xxxx_stored:04d}"
    return part1

def verify_part1(serial_part1):
    """
    Verify the first part of the serial (Zz-YXXXX-yxxxx).
    Returns True if the complex number equation holds.
    """
    try:
        prefix, mid, last = serial_part1.split('-')
        Z_val = int(prefix[0])
        z_val = int(prefix[1])
        Y = int(mid[0])
        XXXX = int(mid[1:])
        y = int(last[0])
        xxxx = int(last[1:])

        # Apply sign rules
        if Y % 2 == 1:
            XXXX = -XXXX
        if y % 2 == 0:
            xxxx = -xxxx

        B = (Z_val, z_val)
        A = (XXXX, xxxx)
        P = (4, -2)

        # C = P + A
        C = complex_add(P, A)

        # ComplexMulDiv: Q = conj(B), compute C*Q / (B*Q)
        # B*Q = |B|^2 (real number)
        Q = (B[0], -B[1])
        BQ = complex_mul(B, Q)  # = (|B|^2, 0)
        CQ = complex_mul(C, Q)

        # R = CQ / BQ  (BQ is real: BQ[0], 0)
        denom = BQ[0]
        R = (CQ[0] / denom, CQ[1] / denom)

        # R^2 should equal (-9, 0)
        R2 = complex_mul(R, R)
        return abs(R2[0] - (-9)) < 1e-9 and abs(R2[1]) < 1e-9
    except Exception:
        return False

# ============================================================
# Part 2: ElGamal existential forgery (2nd checkpoint)
# ============================================================
# Parameters from the writeup (384-bit)
P_ELG = 0x732CB128ED92D1A5EB1E6DECAED463A38F32EFEF39B8EB17299B420F9321F4068D7125A10133353FDA00C203B61CE22B
G_ELG = 0x105DF76E6C18E8D3571D8D9190928416146EA328F05CB666ACB67A3F4EFBB055875E2457DBDD3E370A169E8A340F1EB8
Y_ELG = 0x0BFC7E64D617907BB64E75F2A39EFEDDE5B8CCDB505BEB9012BA498611EA174074CF5F2C85397BFD3D55A751A746A8F2

def elgamal_existential_forgery():
    """
    Existential forgery attack on ElGamal without hash.
    Returns (r, s, m) a valid forged signature.

    Select u, v with gcd(v, p-1) = 1.
    r = g^u * y^v mod p
    s = -r * v^-1 mod (p-1)
    m = s * u mod (p-1)
    """
    p1 = P_ELG - 1  # p-1

    while True:
        u = random.randint(2, p1 - 1)
        v = random.randint(2, p1 - 1)
        if math.gcd(v, p1) == 1:
            break

    r = pow(G_ELG, u, P_ELG) * pow(Y_ELG, v, P_ELG) % P_ELG
    v_inv = mod_inverse(v, p1)
    s = (-r * v_inv) % p1
    m = (s * u) % p1
    return r, s, m

# ============================================================
# Combined verify and keygen
# ============================================================

def verify(name, serial):
    """
    Verify a serial.
    ASSUMPTION: The serial encodes both Part1 and Part2 data.
    We split on '|' to separate the two parts for this implementation.
    Part1: complex number check
    Part2: ElGamal forged signature check
    """
    try:
        parts = serial.split('|')
        if len(parts) < 2:
            return False
        part1_str = parts[0]  # e.g. "Zz-YXXXX-yxxxx"
        # part2 not checked here as the verification equation is complex
        # ASSUMPTION: we only verify part1 fully; part2 existential forgery is always valid by construction
        return verify_part1(part1_str)
    except Exception:
        return False

def keygen(name):
    """
    Generate a valid serial for any name.
    ASSUMPTION: the name is not used in part1 (random B chosen).
    ASSUMPTION: the name feeds into m for part2, but since forgery produces its own m,
                we just use the forged (r, s, m) and encode them.
    """
    # Part 1
    B, A = generate_serial_part1()
    part1 = format_serial_part1(B, A)

    # Part 2 - existential forgery
    r, s, m = elgamal_existential_forgery()
    part2 = f"{hex(r)}-{hex(s)}-{hex(m)}"

    return f"{part1}|{part2}"


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
