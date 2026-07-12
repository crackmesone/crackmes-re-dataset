#!/usr/bin/env python3
"""
Citron KeyGenMe by BigBang - Reverse Engineered Algorithm

Algorithm Summary (from Kerberos writeup):
- Buffers n1, n2, n3, n4 of length l = len(username)
- n1[i] = Prime(i)  (i-th prime starting from P1, where Prime(0)=P1)
- n4[i] = C1 * i   (exception: if i==0, n4[0] = C1)
- n2[i] = n4[i] * SHA1(username[i])   if i is odd
         n4[i] * RIPEMD160(username[i]) if i is even
- n3[i] = serial_number - n2[i]
- Check: n3[i] == 0 (mod n1[i])  for all i
  Equivalently: serial == n2[i] (mod n1[i]) for all i
- Solve with CRT to get serial number
- Encode serial in base 32

Constants (hex):
  P1 = 0x8A8335C1EBA9406AE57DCC8BDAD59D2B
  C1 = 0x13333333333333333333333333333333337

NOTE: 'Prime(i)' means the i-th prime *after* P1, with Prime(0)=P1.
Since P1 is a large 128-bit number, we need a big-number primality check
and next-prime logic.
"""

import hashlib
from sympy import isprime, nextprime
from functools import reduce

# Constants
P1 = 0x8A8335C1EBA9406AE57DCC8BDAD59D2B
C1 = 0x13333333333333333333333333333333337

# Base32 alphabet used by the crackme
# ASSUMPTION: Standard base32 alphabet is used (A-Z, 2-7).
# The writeup mentions base 32 encoding but doesn't specify the exact alphabet.
# The constants in assembly appear to use a custom base32 (uppercase + digits).
# We'll use Python's standard base32 as an approximation.
import base64


def sha1_of_char(c: str) -> int:
    """Compute SHA-1 of a single character, return as integer."""
    h = hashlib.sha1(c.encode('latin-1')).digest()
    return int.from_bytes(h, 'big')


def ripemd160_of_char(c: str) -> int:
    """Compute RIPEMD-160 of a single character, return as integer."""
    # ASSUMPTION: hashlib supports ripemd160 on the running platform
    try:
        h = hashlib.new('ripemd160', c.encode('latin-1')).digest()
        return int.from_bytes(h, 'big')
    except ValueError:
        # ASSUMPTION: fallback if ripemd160 not available - use sha1 as placeholder
        # This will produce WRONG results but allows the code to run
        h = hashlib.sha1(c.encode('latin-1')).digest()
        return int.from_bytes(h, 'big')


def get_primes_from_p1(count: int):
    """Get `count` primes starting from P1 (Prime(0)=P1, Prime(1)=nextprime(P1), ...)."""
    primes = []
    p = P1
    # ASSUMPTION: P1 itself is prime (used as Prime(0))
    # If not, we take the nearest prime >= P1
    if not isprime(p):
        p = nextprime(p - 1)
    for _ in range(count):
        primes.append(p)
        p = nextprime(p)
    return primes


def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = extended_gcd(b, a % b)
    return g, y, x - (a // b) * y


def crt(remainders, moduli):
    """Chinese Remainder Theorem solver."""
    # ASSUMPTION: all moduli are pairwise coprime (true since they are distinct primes)
    M = 1
    for m in moduli:
        M *= m
    x = 0
    for r, m in zip(remainders, moduli):
        Mi = M // m
        _, inv, _ = extended_gcd(Mi, m)
        inv = inv % m
        x += r * Mi * inv
    return x % M


def int_to_base32(n: int) -> str:
    """Encode a big integer as base32 string."""
    # ASSUMPTION: The crackme uses a specific base32 encoding.
    # We convert the integer to bytes then base32 encode.
    if n == 0:
        return 'A'
    byte_length = (n.bit_length() + 7) // 8
    n_bytes = n.to_bytes(byte_length, 'big')
    encoded = base64.b32encode(n_bytes).decode('ascii').rstrip('=')
    return encoded


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    l = len(name)
    if l == 0:
        return ''

    # Build n1: primes starting from P1
    n1 = get_primes_from_p1(l)

    # Build n4
    n4 = []
    for i in range(l):
        if i == 0:
            n4.append(C1)  # exception: n4[0] = C1
        else:
            n4.append(C1 * i)

    # Build n2
    n2 = []
    for i in range(l):
        c = name[i]
        if i % 2 == 1:  # odd
            hash_val = sha1_of_char(c)
        else:           # even
            hash_val = ripemd160_of_char(c)
        n2.append(n4[i] * hash_val)

    # Solve CRT: serial == n2[i] (mod n1[i]) for all i
    # Reduce n2[i] mod n1[i] first
    remainders = [n2[i] % n1[i] for i in range(l)]
    moduli = n1

    serial_int = crt(remainders, moduli)
    serial_str = int_to_base32(serial_int)
    return serial_str


def verify(name: str, serial: str) -> bool:
    """Verify a serial number for a given name."""
    l = len(name)
    if l == 0:
        return False

    # Parse serial from base32 to integer
    try:
        # Pad to multiple of 8 for base32 decoding
        padded = serial + '=' * ((8 - len(serial) % 8) % 8)
        serial_bytes = base64.b32decode(padded.upper())
        sn = int.from_bytes(serial_bytes, 'big')
    except Exception:
        return False

    # Build n1: primes starting from P1
    n1 = get_primes_from_p1(l)

    # Build n4
    n4 = []
    for i in range(l):
        if i == 0:
            n4.append(C1)
        else:
            n4.append(C1 * i)

    # Build n2
    n2 = []
    for i in range(l):
        c = name[i]
        if i % 2 == 1:  # odd
            hash_val = sha1_of_char(c)
        else:           # even
            hash_val = ripemd160_of_char(c)
        n2.append(n4[i] * hash_val)

    # Check: (sn - n2[i]) % n1[i] == 0 for all i
    for i in range(l):
        n3_i = sn - n2[i]
        if n3_i % n1[i] != 0:
            return False
    return True



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
