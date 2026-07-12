#!/usr/bin/env python3
"""
Basis#2 RSA - Wiener by Amenesia
Reverse-engineered keygen/verify implementation.

Algorithm:
  1. Compute MD5(name) -> 16 bytes -> big integer Hash_M
  2. Parse license (serial) as a hex big integer M
  3. Compute M^E mod N
  4. Compare result with Hash_M

For keygen: license = Hash_M^D mod N
Where D is recovered via Wiener's continued-fraction attack on (E, N).
"""

import hashlib
from math import isqrt, gcd

# ── Public key from the crackme source ───────────────────────────────────────
N = int(
    "7D4C538A3766CA67C73534105AB812817E0E3C5F1CC3853136AAC"
    "8279D501EB51572226C060D420A70331348B6E0F1974DFB969B7BE30E31F812"
    "8EAF3A0CBE4D5C134528AD61E707AC3E6233BF5755DA4FDB63E48AC053A00D2"
    "27C3A9B031FC282157CB3071ECA94013140ABC1F886DE9EBF6ED1C39965ECF4"
    "6846BF74BFC681",
    16,
)

E = int(
    "44D7A0FD047CA62C70DF9C4E4B77D22CDC7A07FF325E4302CAC6E"
    "C7F79321E325338EDFCB86F56F8E67D5458559446F9840F69E220326AA75FFD"
    "F60679B1A7E1EF8ABBC3DC873B3C19ED7C0A59667AF746E4877907AB2FF9C85"
    "BBFEAF3AF8013676E05EA735EDF6AE8D5FE8B130D7B805CC28844B921C3100F"
    "A7282DA359DBA7",
    16,
)

# ── Factors recovered via Wiener attack (from bLaCk-eye's writeup) ───────────
P = int(
    "C107516C875698ED29319A7C8C45ADECB0A7C9A0D0616E7B2BEEF408216BD645C039EA"
    "BB81615AEDA9C54636D14A83814A219705C4B37E1403F872757396E883",
    16,
)
Q = int(
    "62C893E3DDBEEB366239A1EDBADECEC3F3D953E43D90C1206B80B54C88B2AC203455EE"
    "B427C6ED31F5683D014E16E37D207A2500EA436FF3D5E438C25E3FDAB",
    16,
)


def _compute_private_key() -> int:
    """Derive private exponent D from known factors P, Q, E."""
    phi = (P - 1) * (Q - 1)
    # D = modular inverse of E mod phi
    D = pow(E, -1, phi)
    return D


D = _compute_private_key()


def _md5_to_int(name: str) -> int:
    """Compute MD5 of name bytes and return as a big integer (big-endian)."""
    h = hashlib.md5(name.encode('latin-1')).digest()  # 16 bytes
    return int.from_bytes(h, 'big')


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.

    serial is expected as a hex string (the 'license' field from the crackme).
    The crackme does:
        M = parse_hex(serial)
        result = M^E mod N
        check  result == MD5(name) as big integer
    """
    try:
        M = int(serial.replace(' ', '').replace('\n', ''), 16)
    except ValueError:
        return False

    hash_m = _md5_to_int(name)
    result = pow(M, E, N)
    return result == hash_m


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    license = MD5(name)^D mod N  (hex-encoded, upper-case)
    """
    hash_m = _md5_to_int(name)
    license_int = pow(hash_m, D, N)
    # Encode as hex string (upper-case, even number of nibbles)
    hex_str = hex(license_int)[2:].upper()
    if len(hex_str) % 2:
        hex_str = '0' + hex_str
    return hex_str


# ── Wiener attack (for reference / standalone use) ────────────────────────────
def _continued_fraction_convergents(e, n):
    """Yield convergents (num, den) of the continued fraction expansion of e/n."""
    a_prev, a_curr = 0, 1
    b_prev, b_curr = 1, 0
    while n:
        q = e // n
        e, n = n, e % n
        a_prev, a_curr = a_curr, q * a_curr + a_prev
        b_prev, b_curr = b_curr, q * b_curr + b_prev
        yield a_curr, b_curr


def wiener_attack(e, n):
    """
    Wiener's low-private-exponent attack.
    Returns D if found, else None.
    """
    for k, dg in _continued_fraction_convergents(e, n):
        if k == 0:
            continue
        # Check if (e*dg - 1) is divisible by k
        if (e * dg - 1) % k != 0:
            continue
        phi_candidate = (e * dg - 1) // k
        # N = p*q,  phi = (p-1)(q-1) = N - (p+q) + 1
        # so p+q = N - phi_candidate + 1
        b = n - phi_candidate + 1
        # discriminant of x^2 - b*x + n == 0
        disc = b * b - 4 * n
        if disc < 0:
            continue
        sqrt_disc = isqrt(disc)
        if sqrt_disc * sqrt_disc != disc:
            continue
        # Found valid factorisation
        p = (b + sqrt_disc) // 2
        q = (b - sqrt_disc) // 2
        if p * q == n:
            # Recover D: smallest positive d such that e*d ≡ 1 (mod phi)
            phi = (p - 1) * (q - 1)
            d = pow(e, -1, phi)
            return d
    return None



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
