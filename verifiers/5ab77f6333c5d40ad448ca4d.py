#!/usr/bin/env python3
"""
cRYPTO kEYGENME 2 by bLaCk-eye - Keygen reimplementation in Python 3

Protection: MD5, RC4, modular arithmetic

The serial format is: s1-s2  (both as hex big integers)

Validation equation (from writeup):
    (s1^(-e) * userid^(-s2)) * s2 mod n = rc4(name)
    with n = p1*p2*p3*p4  (product of 4 primes derived from name/company/userid)
    e = 0xF9B0D1F192EA5120EC1B

Keygen steps:
    1. Compute MD5(name) -> tab[0..3], MD5(company) -> tab[4..7]
    2. Perform arithmetic modifications on tab[8..15] using userid
    3. Extract p1,p2,p3,p4 as next primes from 128-bit chunks of tab
    4. n = p1*p2*p3*p4
    5. phi_n = (p1-1)*(p2-1)*(p3-1)*(p4-1)
    6. Pick random s2 in [0, n)
    7. cipher = rc4_encrypt(name, key=MD5(company))
               interpreted as bignum, then:
               cipher = cipher * userid^s2 mod n
               cipher = cipher * s2^(-1) mod n
    8. d = (-e)^(-1) mod phi_n
    9. s1 = cipher^d mod n
   10. serial = hex(s1).upper() + '-' + hex(s2).upper()
"""

import hashlib
import struct
import random
from sympy import nextprime


# ---------------------------------------------------------------------------
# RC4 implementation
# ---------------------------------------------------------------------------

def rc4_keysetup(key: bytes) -> list:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def rc4_crypt(data: bytes, key: bytes) -> bytes:
    S = rc4_keysetup(key)
    i = j = 0
    out = bytearray()
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(byte ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


# ---------------------------------------------------------------------------
# MD5 helper (returns list of 4 uint32 LE words)
# ---------------------------------------------------------------------------

def md5_words(data: bytes):
    digest = hashlib.md5(data).digest()
    return list(struct.unpack('<4I', digest))


# ---------------------------------------------------------------------------
# Build the tab array and primes from name/company/userid
# ---------------------------------------------------------------------------

def build_params(name: bytes, company: bytes, userid_bytes: bytes):
    """
    Returns (p1, p2, p3, p4, n, phi_n, big_userid, company_md5)
    
    ASSUMPTION: The 'while(i<3)' loop arithmetic in the C code uses
    32-bit signed/unsigned overflow semantics. We emulate with masks.
    """
    # Parse userid as 4 x uint32 big-endian hex (from '%l8X%l8X%l8X%l8X')
    # ASSUMPTION: sscanf with %l8X reads 4 groups of 8 hex chars as unsigned 32-bit
    if len(userid_bytes) < 32:
        raise ValueError('userid must be 32 hex chars (4x8)')
    uid_hex = userid_bytes.decode('ascii', errors='replace').strip()
    if len(uid_hex) < 32:
        raise ValueError('userid too short')
    id_ = [
        int(uid_hex[0:8],  16),
        int(uid_hex[8:16], 16),
        int(uid_hex[16:24],16),
        int(uid_hex[24:32],16),
    ]

    tab = [0] * 16

    # Hash name -> tab[0..3]
    name_words = md5_words(name)
    tab[0:4] = name_words

    # Hash company -> tab[4..7]
    company_words = md5_words(company)
    tab[4:8] = company_words

    # tab[8] and tab[12] modifications
    MASK = 0xFFFFFFFF
    tab[8]  = ((tab[0] + tab[4]) * id_[2]) & MASK
    tab[12] = ((tab[3] + tab[7]) ^ id_[3]) & MASK

    # The while(i<3) loop
    # ASSUMPTION: All arithmetic is 32-bit (wrapping), matching C int/unsigned behavior
    i = 0
    while i < 3:
        ebpC = tab[5 + i] & MASK
        esi  = (((tab[8 + i] << 6) & MASK) + ((tab[5 + i] ^ 0xFFFFFFFF) & MASK)) & MASK
        ecx  = tab[1 + i] & MASK
        edx  = (((ecx >> 4) & MASK) + id_[0]) & MASK
        ecx  = (ecx ^ 0xFFFFFFFF) & MASK
        esi  = (esi ^ edx) & MASK
        i   += 1
        edx2 = tab[11 + i] & MASK
        tab[8 + i] = esi
        edx2 = ((edx2 * 8) & MASK + ecx) & MASK
        ecx2 = (((ebpC >> 7) & MASK) - id_[1]) & MASK
        edx2 = (edx2 ^ ecx2) & MASK
        tab[12 + i] = edx2

    # Convert tab to bytes: 4 chunks of 16 bytes each
    def words_to_bytes_be(words_slice):
        """Convert list of 4 uint32 to 16-byte big-endian block.
        ASSUMPTION: bytes_to_big in MIRACL reads big-endian bytes."""
        return b''.join(struct.pack('>I', w & 0xFFFFFFFF) for w in words_slice)

    chunk0 = words_to_bytes_be(tab[0:4])
    chunk1 = words_to_bytes_be(tab[4:8])
    chunk2 = words_to_bytes_be(tab[8:12])
    chunk3 = words_to_bytes_be(tab[12:16])

    p1 = nextprime(int.from_bytes(chunk0, 'big'))
    p2 = nextprime(int.from_bytes(chunk1, 'big'))
    p3 = nextprime(int.from_bytes(chunk2, 'big'))
    p4 = nextprime(int.from_bytes(chunk3, 'big'))

    n     = p1 * p2 * p3 * p4
    phi_n = (p1 - 1) * (p2 - 1) * (p3 - 1) * (p4 - 1)

    # big_userid from the 4 id words as bytes (16 bytes big-endian)
    userid_big_bytes = b''.join(struct.pack('>I', x) for x in id_)
    big_userid = int.from_bytes(userid_big_bytes, 'big')

    # MD5 of company for RC4 key
    company_md5 = hashlib.md5(company).digest()

    return p1, p2, p3, p4, n, phi_n, big_userid, company_md5


# ---------------------------------------------------------------------------
# Keygen
# ---------------------------------------------------------------------------

def keygen(name: str, company: str, userid_hex: str) -> str:
    """
    Generate a valid serial for (name, company, userid_hex).
    userid_hex should be 32 hex chars (128-bit).
    Returns 'S1-S2' both in uppercase hex.
    """
    name_b    = name.encode('ascii')
    company_b = company.encode('ascii')
    userid_b  = userid_hex.strip().encode('ascii')

    if len(name_b) < 3 or len(company_b) < 3:
        raise ValueError('name and company must be at least 3 chars')
    if name_b == company_b:
        raise ValueError('name and company must differ')

    p1, p2, p3, p4, n, phi_n, big_userid, company_md5 = build_params(name_b, company_b, userid_b)

    e = 0xF9B0D1F192EA5120EC1B
    neg_e = -e
    # d = (-e)^(-1) mod phi_n
    d = pow(neg_e % phi_n, -1, phi_n)

    # Random s2 in [0, n)
    s2 = random.randint(0, n - 1)

    # Compute userid^s2 mod n
    userid_pow_s2 = pow(big_userid, s2, n)

    # s2^(-1) mod n
    s2_inv = pow(s2, -1, n)

    # RC4-encrypt name (32 bytes, zero-padded) with key = MD5(company)
    name_padded = name_b[:32].ljust(32, b'\x00')
    encrypted_name = rc4_crypt(name_padded, company_md5)

    # cipher = int(encrypted_name)
    cipher = int.from_bytes(encrypted_name, 'big')

    # cipher = cipher * userid^s2 * s2^(-1) mod n
    cipher = (cipher * userid_pow_s2 % n * s2_inv) % n

    # s1 = cipher^d mod n
    s1 = pow(cipher, d, n)

    serial = hex(s1)[2:].upper() + '-' + hex(s2)[2:].upper()
    return serial


# ---------------------------------------------------------------------------
# Verify  (re-derive s1 from s2 and check)
# ---------------------------------------------------------------------------

def verify(name: str, company: str, userid_hex: str, serial: str) -> bool:
    """
    Verify a serial. serial must be 'S1-S2' in hex.
    """
    try:
        parts = serial.strip().split('-')
        if len(parts) != 2:
            return False
        s1_hex, s2_hex = parts
        s1_given = int(s1_hex, 16)
        s2       = int(s2_hex, 16)
    except Exception:
        return False

    name_b    = name.encode('ascii')
    company_b = company.encode('ascii')
    userid_b  = userid_hex.strip().encode('ascii')

    if len(name_b) < 3 or len(company_b) < 3 or name_b == company_b:
        return False

    p1, p2, p3, p4, n, phi_n, big_userid, company_md5 = build_params(name_b, company_b, userid_b)

    if s2 <= 0 or s2 >= n:
        return False

    e = 0xF9B0D1F192EA5120EC1B
    neg_e = -e
    d = pow(neg_e % phi_n, -1, phi_n)

    # Recompute expected s1
    userid_pow_s2 = pow(big_userid, s2, n)
    s2_inv = pow(s2, -1, n)

    name_padded = name_b[:32].ljust(32, b'\x00')
    encrypted_name = rc4_crypt(name_padded, company_md5)
    cipher = int.from_bytes(encrypted_name, 'big')
    cipher = (cipher * userid_pow_s2 % n * s2_inv) % n
    s1_expected = pow(cipher, d, n)

    return s1_given == s1_expected


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


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
