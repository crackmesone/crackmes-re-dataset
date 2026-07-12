#!/usr/bin/env python3
"""
Crypto KeygenMe 3 by black_eye
Solved/implemented by reverse-engineering the writeup.

Protection:
  1. Compute Whirlpool hash of the name (512 bits).
  2. Split hash into two 256-bit halves: h1, h2.
  3. hxor = h1 XOR h2
  4. Find next prime p > hxor such that p % 3 == 1
  5. Solve Diophantine equation using Cornacchia's algorithm:
         x^2 + 3*y^2 = p
     (d=3, so equation is x^2 + d*y^2 = p)
  6. x = activation, y = serial

Verification:
  activation^2 + 3 * serial^2 == p

NOTE: A full Python Whirlpool implementation is needed.
We use the 'whirlpool' package or a fallback reference implementation.
"""

import math
import struct
from sympy import nextprime, isprime, sqrt_mod, isqrt

# ASSUMPTION: We use a Python whirlpool implementation.
# The 'whirlpool' package (pip install whirlpool) or a reference implementation.
# If not available, we provide a stub that raises NotImplementedError.
def whirlpool_digest(data: bytes) -> bytes:
    try:
        import whirlpool as _wp
        h = _wp.new(data)
        return bytes.fromhex(h.hexdigest())
    except ImportError:
        # ASSUMPTION: fallback stub - replace with real implementation
        raise NotImplementedError(
            "Whirlpool hash not available. Install 'whirlpool' package: pip install whirlpool"
        )


def get_hxor(name: str) -> int:
    """Compute hxor = h1 XOR h2 from whirlpool hash of name."""
    name_bytes = name.encode('ascii')
    digest = whirlpool_digest(name_bytes)  # 64 bytes = 512 bits
    assert len(digest) == 64, "Whirlpool must produce 64 bytes"
    h1_bytes = digest[:32]   # first 256 bits
    h2_bytes = digest[32:]   # second 256 bits
    h1 = int.from_bytes(h1_bytes, 'big')
    h2 = int.from_bytes(h2_bytes, 'big')
    return h1 ^ h2


def get_prime(hxor: int) -> int:
    """Find next prime p > hxor such that p % 3 == 1."""
    p = nextprime(hxor)
    while p % 3 != 1:
        p = nextprime(p)
    return p


def isqrt_exact(n: int):
    """Return integer square root if n is a perfect square, else None."""
    if n < 0:
        return None
    r = isqrt(n)
    if r * r == n:
        return r
    return None


def cornacchia(d: int, p: int):
    """
    Cornacchia's algorithm (Algorithm 1.5.2 from Cohen).
    Solve x^2 + d*y^2 = p for prime p and 0 < d < p.
    Returns (x, y) if solution exists, else None.
    """
    # Step 1: Check Jacobi symbol of (-d) mod p == 1 (i.e., not -1)
    # We use sympy's sqrt_mod to test if -d is a QR mod p
    neg_d = (-d) % p
    x0 = sqrt_mod(neg_d, p)
    if x0 is None:
        return None

    # Step 2: Ensure x0 > sqrt(p)
    limit = isqrt(p)
    # Adjust x0: we want x0 in range (sqrt(p), p)
    # Per Cohen: find x0 s.t. x0 > sqrt(p)
    # The standard approach: pick x0, then if x0 <= sqrt(p), use p - x0
    # But we need to run the Euclidean-like reduction starting from p, x0
    # First make sure x0 > p/2 or handle both candidates
    if x0 <= limit:
        x0 = p - x0
    if x0 <= limit:
        # Neither candidate works at this stage; try the other sqrt candidate
        other = p - x0
        if other > limit:
            x0 = other
        else:
            return None

    # Step 3: Euclidean algorithm reduction
    a, b = p, x0
    while b > limit:
        a, b = b, a % b

    # Now b <= sqrt(p)
    # Step 4: Check if (p - b^2) / d is a perfect square
    b_sq = b * b
    num = p - b_sq
    if num < 0:
        return None
    if num % d != 0:
        return None
    c_sq = num // d
    c = isqrt_exact(c_sq)
    if c is None:
        return None

    return (b, c)


def keygen(name: str):
    """Generate (activation, serial) for given name."""
    hxor = get_hxor(name)
    p = get_prime(hxor)
    d = 3
    result = cornacchia(d, p)
    if result is None:
        return None
    x, y = result
    # x = activation, y = serial
    return (x, y)


def verify(name: str, serial: str) -> bool:
    """
    Verify a (activation, serial) pair for given name.
    serial is expected as a string; activation must be derived or provided separately.
    
    ASSUMPTION: The crackme checks activation^2 + 3*serial^2 == p.
    For a standalone verify we need both activation and serial.
    Here we accept serial as 'activation:serial' combined string for full check.
    """
    try:
        if ':' in serial:
            parts = serial.split(':')
            activation = int(parts[0], 16)
            serial_num = int(parts[1], 16)
        else:
            # ASSUMPTION: if only serial provided, try to derive activation
            serial_num = int(serial, 16)
            hxor = get_hxor(name)
            p = get_prime(hxor)
            # Check if p - 3*serial_num^2 is a perfect square
            remainder = p - 3 * serial_num * serial_num
            if remainder < 0:
                return False
            activation = isqrt_exact(remainder)
            if activation is None:
                return False
            return activation * activation + 3 * serial_num * serial_num == p

        hxor = get_hxor(name)
        p = get_prime(hxor)
        return activation * activation + 3 * serial_num * serial_num == p
    except Exception:
        return False



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
