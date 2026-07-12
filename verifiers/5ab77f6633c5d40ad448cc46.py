#!/usr/bin/env python3
"""
Reverse-engineered ECDSA verifier/keygen for crackme_0026 by happytown.

Algorithm (ECDSA over a small curve using MIRACL lib):
  Curve: y^2 = x^3 + a*x + b (mod p)
    a = 0x2982
    b = 0x3408
    p = 0xAEBF94CEE3E707
    G = (0x7A3E808599A525, 0x28BE7FAFD2A052)  # generator
  Q_A = (0x9F70A02013BC9B, 0x9E0B275B93CF5E)  # public key
    n = 0xAEBF94D5C6AA71                        # group order
  d_A = 0x9D3F1E3CDDA5E5                        # private key (recovered via ECDLP)

Serial format: "<r_hex>-<s_hex>"  (hex strings, no leading zeros trimmed by MIRACL)

Verification:
  h   = SHA1(name) as big integer
  r,s = parse serial
  s_inv = pow(s, -1, n)
  u1  = s_inv * h  (mod n)
  u2  = s_inv * r  (mod n)
  P   = u1*G + u2*Q_A
  accept iff P.x == r

Key generation:
  k   = random
  r   = (k*G).x
  s   = pow(k,-1,n) * (h + r*d_A) % n
  serial = r_hex + '-' + s_hex
"""

import hashlib
import random
from typing import Optional, Tuple

# ── Curve parameters ──────────────────────────────────────────────────────────
A  = 0x2982
B  = 0x3408
P  = 0xAEBF94CEE3E707
N  = 0xAEBF94D5C6AA71           # group order
Gx = 0x7A3E808599A525
Gy = 0x28BE7FAFD2A052
Qx = 0x9F70A02013BC9B
Qy = 0x9E0B275B93CF5E
# Private key recovered by ECDLP solver (d_A * G = Q_A)
D_A = 0x9D3F1E3CDDA5E5

Point = Optional[Tuple[int, int]]  # None == point at infinity


def _modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def _point_add(P1: Point, P2: Point) -> Point:
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None
        # point doubling
        lam = (3 * x1 * x1 + A) * _modinv(2 * y1, P) % P
    else:
        lam = (y2 - y1) * _modinv(x2 - x1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def _point_mul(k: int, Pt: Point) -> Point:
    result: Point = None
    addend = Pt
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _sha1_bignum(name: str) -> int:
    """SHA-1 of the name string, interpreted as big-endian integer (20 bytes)."""
    digest = hashlib.sha1(name.encode('ascii')).digest()
    return int.from_bytes(digest, 'big')


def _parse_serial(serial: str) -> Tuple[int, int]:
    parts = serial.split('-')
    if len(parts) != 2:
        raise ValueError("Serial must be r-s")
    r = int(parts[0], 16)
    s = int(parts[1], 16)
    return r, s


def verify(name: str, serial: str) -> bool:
    """Return True if serial is a valid ECDSA signature for name."""
    if len(name) < 3 or len(name) > 24:
        return False
    try:
        r, s = _parse_serial(serial)
    except Exception:
        return False
    if r <= 0 or r >= N or s <= 0 or s >= N:
        return False

    h = _sha1_bignum(name)
    s_inv = _modinv(s, N)
    u1 = s_inv * h % N
    u2 = s_inv * r % N

    G: Point = (Gx, Gy)
    Q: Point = (Qx, Qy)

    # u1*G + u2*Q_A
    P1 = _point_mul(u1, G)
    P2 = _point_mul(u2, Q)
    result = _point_add(P1, P2)

    if result is None:
        return False
    return result[0] == r


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 3 or len(name) > 24:
        raise ValueError("Name must be 3-24 characters")

    h = _sha1_bignum(name)
    G: Point = (Gx, Gy)

    while True:
        # k should be a 56-bit random number (as in the original keygen)
        k = random.getrandbits(55) | 1  # odd to help with gcd, but any k works
        k = random.randrange(1, N)

        if pow(k, 1, N) == 0:  # k must be invertible mod n
            continue
        try:
            k_inv = _modinv(k, N)
        except Exception:
            continue

        kG = _point_mul(k, G)
        if kG is None:
            continue
        r = kG[0] % N
        if r == 0:
            continue

        # s = k^-1 * (h + r * d_A) mod n
        s = k_inv * (h + r * D_A) % N
        if s == 0:
            continue

        # Format: uppercase hex, matching MIRACL's cotstr output
        serial = f"{r:X}-{s:X}"
        return serial



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
