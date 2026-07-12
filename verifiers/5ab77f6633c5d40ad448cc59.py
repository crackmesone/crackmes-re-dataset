#!/usr/bin/env python3
"""
Reverse-engineered keygen/verifier for 'd_racinez_moi' by waganono.

The writeup shows:
1. An extended Euclidean algorithm (standard).
2. A Chinese Remainder Theorem solver.
3. A custom 'wagalphabet' encoding (base-32-like alphabet).
4. A hash/transform applied to the name (transform_prefix0 - body NOT shown).
5. The serial is encoded using the wagalphabet_lookahead table.

The core mathematical operation hinted at by the crackme name ('racine' = root)
and the CRT code is solving x^2 = N (mod p*q), i.e. finding a modular square root.

Since transform_prefix0 body is NOT provided, the name->hash step is ASSUMED.
Since the modulus (p, q) used in the crackme is NOT shown, they are ASSUMED.

MARKED ASSUMPTIONS BELOW.
"""

from math import gcd

# --- wagalphabet (base-32 lookahead table, index 0..255+) ---
# Reconstructed from the writeup
_CHARS = "A1B2C3D4E59-7H8IJKLMNOPQRSTUVWYZ"
assert len(_CHARS) == 32  # 32 symbols

def _build_wagalphabet():
    table = []
    # single chars: indices 0-31
    for c in _CHARS:
        table.append(c)
    # two-char combos: first char index * 32 + second char index => indices 32+
    for c1 in _CHARS:
        for c2 in _CHARS:
            table.append(c1 + c2)
    return table

WAGALPHABET = _build_wagalphabet()

def wagalphabet_encode(n: int) -> str:
    """Encode a non-negative integer using the wagalphabet lookahead.
    Single chars cover 0-31, two-char combos cover 32-1055.
    For larger numbers we repeatedly extract base-32 digits.
    # ASSUMPTION: encoding is little-endian base-32 using the _CHARS alphabet.
    """
    if n == 0:
        return _CHARS[0]
    digits = []
    while n > 0:
        digits.append(n % 32)
        n //= 32
    return ''.join(_CHARS[d] for d in digits)

def wagalphabet_decode(s: str) -> int:
    """Decode a wagalphabet-encoded string back to an integer.
    # ASSUMPTION: little-endian base-32.
    """
    result = 0
    base = 1
    for ch in s:
        idx = _CHARS.find(ch)
        if idx == -1:
            raise ValueError(f"Invalid wagalphabet character: {ch}")
        result += idx * base
        base *= 32
    return result

# --- Extended Euclidean ---
def extended_euclidean(u: int, v: int):
    """Returns (f1, f2, gcd) such that f1*u + f2*v == gcd."""
    u1, u2, u3 = 1, 0, u
    v1, v2, v3 = 0, 1, v
    while v3 != 0:
        q = u3 // v3
        t1 = u1 - v1 * q
        t2 = u2 - v2 * q
        t3 = u3 - v3 * q
        u1, u2, u3 = v1, v2, v3
        v1, v2, v3 = t1, t2, t3
    return u1, u2, u3

# --- Chinese Remainder Theorem (2 moduli) ---
def crt(a1: int, n1: int, a2: int, n2: int) -> int:
    """Solve x = a1 (mod n1), x = a2 (mod n2). n1,n2 coprime."""
    r1, s1, _ = extended_euclidean(n1, n2)
    r2, s2, _ = extended_euclidean(n2, n1)
    e1 = s1 * n2
    e2 = s2 * n1
    x = e1 * a1 + e2 * a2
    return x

# --- Modular square root (Tonelli-Shanks, for prime modulus) ---
def sqrt_mod_prime(n: int, p: int) -> int:
    """Returns r such that r^2 = n (mod p), or None."""
    if pow(n, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(n, (p + 1) // 4, p)
    # Tonelli-Shanks
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m = s
    c = pow(z, q, p)
    t = pow(n, q, p)
    r = pow(n, (q + 1) // 2, p)
    while True:
        if t == 0:
            return 0
        if t == 1:
            return r
        i = 1
        tmp = (t * t) % p
        while tmp != 1:
            tmp = (tmp * tmp) % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

# --- Name hash (transform_prefix0) ---
# ASSUMPTION: The name is hashed by summing character ordinals and doing some
# transformation. The actual transform_prefix0 body was NOT provided in the writeup.
# We assume a simple polynomial hash as a placeholder.
def name_hash(name: str) -> int:
    """# ASSUMPTION: transform_prefix0 body not shown. Using placeholder hash."""
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h

# ASSUMPTION: The crackme uses two fixed prime factors p and q (RSA-like).
# Their actual values are NOT shown in the writeup. Placeholder small primes used.
P = 0xFFFFFFFB  # ASSUMPTION: placeholder prime
Q = 0xFFFFFFEF  # ASSUMPTION: placeholder prime
MODULUS = P * Q

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    Steps (as inferred from the writeup):
    1. Hash the name to get a value H.
    2. Find x such that x^2 = H (mod MODULUS) using CRT + modular sqrt.
    3. Encode x using wagalphabet.
    # ASSUMPTION: Many details (actual hash, actual p/q, encoding direction) are unknown.
    """
    H = name_hash(name) % MODULUS
    # Find square roots mod p and mod q
    r_p = sqrt_mod_prime(H % P, P)
    r_q = sqrt_mod_prime(H % Q, Q)
    if r_p is None or r_q is None:
        # Try H+1, H+2, ... until we find a quadratic residue mod both p and q
        # ASSUMPTION: crackme adjusts H or picks a different hash
        for delta in range(1, 10000):
            H2 = (H + delta) % MODULUS
            r_p = sqrt_mod_prime(H2 % P, P)
            r_q = sqrt_mod_prime(H2 % Q, Q)
            if r_p is not None and r_q is not None:
                H = H2
                break
        else:
            raise ValueError("Could not find QR for this name")
    # CRT to combine
    x = crt(r_p, P, r_q, Q) % MODULUS
    return wagalphabet_encode(x)

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial.
    Decode serial, square it, compare to hash of name mod MODULUS.
    # ASSUMPTION: actual hash and modulus unknown.
    """
    try:
        x = wagalphabet_decode(serial)
    except ValueError:
        return False
    H = name_hash(name) % MODULUS
    return pow(x, 2, MODULUS) == H


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
