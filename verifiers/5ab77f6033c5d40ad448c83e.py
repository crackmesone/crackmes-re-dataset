#!/usr/bin/env python3
"""
Crackme #10 by WiteG - ECDSA-based serial verification + keygen
Based on the keygen.cpp and solution.html writeups.

The crackme verifies that the ECDSA signature (r, s) is valid for BOTH:
  H1 = SHA1(username)
  H2 = SHA1(username + ", you just cracked my 10th crackme.. congrats!")
using the SAME (r, s) pair and public key Q_A (called pointH in the crackme).

The serial consists of three big numbers (hex): pointH_x, r, s
(where pointH is the x-coordinate of the public key Q_A,
 and the y-coordinate of Q_A has the same LSB as r)

Curve: secp160r1
"""

import hashlib
import random
from typing import Optional

# ---------------------------------------------------------------------------
# secp160r1 parameters
# ---------------------------------------------------------------------------
p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFF
a = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFC
b = 0x1C97BEFC54BD7A8B65ACF89F81D4D4ADC565FA45
Gx = 0x4A96B5688EF573284664698968C38BB913CBFC82
Gy = 0x23A628553168947D59DCC912042351377AC5FB32
n  = 0x100000000000000000001F4C8F927AED3CA752257

# ---------------------------------------------------------------------------
# Minimal Weierstrass elliptic curve arithmetic over Fp
# ---------------------------------------------------------------------------

def modinv(a, m):
    g, x, _ = _extended_gcd(a % m, m)
    if g != 1:
        raise ValueError("Modular inverse does not exist")
    return x % m

def _extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = _extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

# Points are represented as (x, y) or None for point at infinity
def point_add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return None  # P + (-P)
        # P == Q
        lam = (3 * x1 * x1 + a) * modinv(2 * y1, p) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def point_mul(k, P):
    Q = None
    R = P
    while k > 0:
        if k & 1:
            Q = point_add(Q, R)
        R = point_add(R, R)
        k >>= 1
    return Q

G = (Gx, Gy)

# ---------------------------------------------------------------------------
# Hash functions as described in the keygen
# ---------------------------------------------------------------------------

def sha1_big(data: bytes) -> int:
    """SHA1 digest as a big integer."""
    return int(hashlib.sha1(data).hexdigest(), 16)

def compute_hashes(name: str):
    h1 = sha1_big(name.encode())
    suffix = ", you just cracked my 10th crackme.. congrats!"
    h2 = sha1_big((name + suffix).encode())
    return h1, h2

# ---------------------------------------------------------------------------
# Verification
# The crackme checks ECDSA signature (r, s) against BOTH H1 and H2
# with public key Q_A, requiring both verifications to pass.
#
# Standard ECDSA verify:
#   u1 = s^-1 * H  (mod n)
#   u2 = s^-1 * r  (mod n)
#   J  = u1*G + u2*Q_A
#   valid if J.x == r
# ---------------------------------------------------------------------------

def ecdsa_verify_one(H: int, r: int, s: int, Q) -> bool:
    """Verify ECDSA signature (r,s) for message hash H with public key Q."""
    if Q is None:
        return False
    si = modinv(s, n)
    u1 = (H * si) % n
    u2 = (r * si) % n
    J = point_add(point_mul(u1, G), point_mul(u2, Q))
    if J is None:
        return False
    return J[0] % n == r

def verify(name: str, serial: str) -> bool:
    """
    serial is expected as 'pointH_x:r:s' (hex values separated by ':')
    where pointH_x is the x-coordinate of the public key Q_A.

    The crackme also checks that the y-coordinate of Q_A has same LSB as r,
    so we recover the full public key from pointH_x here.
    """
    if len(name) < 4:
        return False
    try:
        parts = serial.strip().split(":")
        if len(parts) != 3:
            return False
        pointH_x = int(parts[0], 16)
        r = int(parts[1], 16)
        s = int(parts[2], 16)
    except Exception:
        return False

    if r <= 0 or r >= n or s <= 0 or s >= n:
        return False

    # Recover Q_A from pointH_x (two possible y values)
    # y^2 = x^3 + ax + b  (mod p)
    rhs = (pow(pointH_x, 3, p) + a * pointH_x + b) % p
    # Tonelli-Shanks / Fermat for p = 3 mod 4 shortcut
    # p % 4 == 3? Let's check
    if p % 4 == 3:
        y_candidate = pow(rhs, (p + 1) // 4, p)
    else:
        # ASSUMPTION: generic sqrt not implemented; use sympy or similar
        raise NotImplementedError("Square root mod p for p not 3 mod 4")

    if pow(y_candidate, 2, p) != rhs:
        return False  # invalid x coordinate

    # Pick the y that has same LSB as r (as required by the keygen)
    r_lsb = r % 2
    if y_candidate % 2 == r_lsb:
        Q_A = (pointH_x, y_candidate)
    else:
        Q_A = (pointH_x, p - y_candidate)

    H1, H2 = compute_hashes(name)

    ok1 = ecdsa_verify_one(H1, r, s, Q_A)
    ok2 = ecdsa_verify_one(H2, r, s, Q_A)
    return ok1 and ok2

# ---------------------------------------------------------------------------
# Keygen
# Algorithm from keygen.cpp:
#
# Choose random k.
# r = x-coord of k*G  (mod n)
#
# We need SAME (r,s) to verify for both H1 and H2, so we need a d_A such that:
#   s = k^{-1}*(H1 + r*d_A)  (mod n)
#   s = (N-k)^{-1}*(H2 + r*d_A)  (mod n)   [i.e., k replaced by N-k]
#
# From keygen.cpp:
#   ta = N - k
#   d_A = (k*H2 - (N-k)*H1) * ((N-k)*r - k*r)^{-1}  (mod n)
#   s   = k^{-1} * (H1 + r*d_A)  (mod n)
#   Q_A = d_A * G
#   Require: y(Q_A) LSB == r LSB
# ---------------------------------------------------------------------------

def keygen(name: str) -> Optional[str]:
    """Generate a valid serial for the given name."""
    if len(name) < 4:
        raise ValueError("Name too short (need >= 4 chars)")

    H1, H2 = compute_hashes(name)

    for _attempt in range(1000):
        # Choose random k in [1, n-1]
        k = random.randint(1, n - 1)

        # r = x-coord of k*G
        kG = point_mul(k, G)
        if kG is None:
            continue
        r = kG[0] % n
        if r == 0:
            continue

        # ta = N - k
        ta = (n - k) % n
        if ta == 0:
            continue

        # Numerator:   k*H2 - (N-k)*H1  (mod n)
        num_dA = (k * H2 - ta * H1) % n

        # Denominator: (N-k)*r - k*r = r*(N-k-k) = r*(N-2k)  (mod n)
        #   But from code: (N-k)*r - k*r
        den_dA = (ta * r - k * r) % n
        if den_dA == 0:
            continue

        try:
            den_dA_inv = modinv(den_dA, n)
        except ValueError:
            continue

        d_A = (num_dA * den_dA_inv) % n
        if d_A == 0:
            continue

        # Compute Q_A = d_A * G
        Q_A = point_mul(d_A, G)
        if Q_A is None:
            continue
        pointH_x, pointH_y = Q_A

        # Require: LSB(y(Q_A)) == LSB(r)
        if (pointH_y % 2) != (r % 2):
            continue

        # s = k^{-1} * (H1 + r*d_A)  (mod n)
        try:
            k_inv = modinv(k, n)
        except ValueError:
            continue
        s = (k_inv * (H1 + r * d_A)) % n
        if s == 0:
            continue

        # Sanity check
        if verify(name, f"{pointH_x:X}:{r:X}:{s:X}"):
            return f"{pointH_x:X}:{r:X}:{s:X}"

    return None  # failed after max attempts (should be very rare)



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
