#!/usr/bin/env python3
"""
Keygen for Numernia's 'Keygenme Tre'

Algorithm: Nyberg-Rueppel (ECNR) signature scheme
  Curve: y^2 = x^3 + 621x + 645 over GF(p), p = 3410286041003
  Generator P = (1926452604425, 1986356512487)
  Public key Q = (291423732751, 437711818455)
  Private key x = 2408408535581
  Group order n = 3410284165198

Serial format: XXXXXX-XXXX-XXXX-XXX-XXXX-XXXX-XXX-NM
  (37 chars total, last 2 chars are always 'NM')
  Fields: m(6 hex) | r(11 hex) | s(11 hex) | 'NM'
  r and s are split across the dashes.
"""

import random
import math

# Curve parameters
P_PRIME = 3410286041003
A = 621
B = 645
GX = 1926452604425
GY = 1986356512487
QX = 291423732751
QY = 437711818455
PRIV_X = 2408408535581
GROUP_ORDER = 3410284165198

G = (GX, GY)
Q_PUB = (QX, QY)

# --- Elliptic curve arithmetic over GF(P_PRIME) ---

def modinv(a, m):
    return pow(a, -1, m)

def ec_add(P1, P2, p=P_PRIME, a=A):
    """Add two points on the elliptic curve."""
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return None  # Point at infinity
        # Point doubling
        lam = (3 * x1 * x1 + a) * modinv(2 * y1, p) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def ec_mul(k, point, p=P_PRIME, a=A):
    """Scalar multiplication on elliptic curve."""
    result = None
    addend = point
    k = k % GROUP_ORDER
    while k:
        if k & 1:
            result = ec_add(result, addend, p, a)
        addend = ec_add(addend, addend, p, a)
        k >>= 1
    return result

# --- Message generation ---

def gen_message():
    """
    Generate a random 3-byte (24-bit) message m such that
    the position of the MSB (counting from LSB=0) is odd.
    Equivalently: ceil(log2(m)) mod 2 == 0 in MAGMA,
    which means the bit-length of m is even.
    Also: the PARI script says (24 - index_of_first_set_bit) % 2 == 0
    where index is 0-based from MSB in a 24-bit vector.
    
    From the MAGMA script: Ceiling(Log(2,m)) mod 2 == 0
    Ceiling(Log(2,m)) == bit_length(m) for m > 1
    So bit_length(m) must be even.
    """
    while True:
        m = random.randint(1, (1 << 24) - 1)
        bl = m.bit_length()
        if bl % 2 == 0:
            return m

# --- Signature generation ---

def sign(m):
    """Generate ECNR signature (r, s) for message m."""
    n = GROUP_ORDER
    while True:
        k = random.randint(1, n - 1)
        kG = ec_mul(k, G)
        if kG is None:
            continue
        r = (kG[0] + m) % n
        s = (k - PRIV_X * r) % n
        return r, s

# --- Signature verification ---

def verify_signature(m, r, s):
    """
    Nyberg-Rueppel verification:
    Compute sG + rQ, take x-coordinate, then check:
    r - x_coord(sG + rQ) == m  (mod n)
    i.e. x_coord(sG + rQ) == (r - m) mod n
    """
    n = GROUP_ORDER
    sG = ec_mul(s, G)
    rQ = ec_mul(r, Q_PUB)
    combo = ec_add(sG, rQ)
    if combo is None:
        return False
    recovered_m = (r - combo[0]) % n
    return recovered_m == m

# --- Serial encoding/decoding ---

def encode_serial(m, r, s):
    """
    Encode m (24-bit), r (44-bit), s (44-bit) into serial string.
    m -> 6 hex chars (24 bits = 6 hex digits)
    r -> 11 hex chars (44 bits = 11 hex digits)
    s -> 11 hex chars (44 bits = 11 hex digits)
    Total data: 6+11+11 = 28 hex chars + 'NM' = 30
    Format: MMMMMM-RRRR-RRRR-RRR-SSSS-SSSS-SSS-NM
    """
    m_hex = format(m, '06X')           # 6 hex chars
    r_hex = format(r, '011X')          # 11 hex chars
    s_hex = format(s, '011X')          # 11 hex chars
    
    # Combined string: m(6) + r(11) + s(11) + NM = 30 chars
    combined = m_hex + r_hex + s_hex + 'NM'
    # Positions of '-': 6, 10, 14, 17, 21, 25, 28 (1-indexed: 7,11,15,18,22,26,29)
    # From assembly: indices 6,11,16,20,25,30,34 (0-indexed in 37-char string)
    # Format: [0..5]-[6..9]-[10..13]-[14..16]-[17..20]-[21..24]-[25..27]-[28..29]
    # That is: 6 chars - 4 chars - 4 chars - 3 chars - 4 chars - 4 chars - 3 chars - 2 chars
    s0 = combined[0:6]    # MMMMMM
    s1 = combined[6:10]   # RRRR
    s2 = combined[10:14]  # RRRR
    s3 = combined[14:17]  # RRR
    s4 = combined[17:21]  # SSSS
    s5 = combined[21:25]  # SSSS
    s6 = combined[25:28]  # SSS
    s7 = 'NM'
    
    return f"{s0}-{s1}-{s2}-{s3}-{s4}-{s5}-{s6}-{s7}"

def decode_serial(serial):
    """
    Decode a serial string into (m, r, s).
    Returns None if format is invalid.
    """
    if len(serial) != 37:
        return None
    
    # Check dashes at positions 6,11,16,20,25,30,34 (0-indexed)
    dash_positions = [6, 11, 16, 20, 25, 30, 34]
    for pos in dash_positions:
        if serial[pos] != '-':
            return None
    
    # Check last two chars are 'NM'
    if serial[35:37] != 'NM':
        return None
    
    # Extract parts
    parts = serial.split('-')
    if len(parts) != 8:
        return None
    if parts[7] != 'NM':
        return None
    
    # Reconstruct hex strings
    m_hex = parts[0]                                          # 6 chars
    r_hex = parts[1] + parts[2] + parts[3]                   # 4+4+3 = 11 chars
    s_hex = parts[4] + parts[5] + parts[6]                   # 4+4+3 = 11 chars
    
    try:
        m = int(m_hex, 16)
        r = int(r_hex, 16)
        s = int(s_hex, 16)
    except ValueError:
        return None
    
    return m, r, s

# --- Public API ---

def verify(name, serial):
    """
    Verify a serial. Note: the crackme does NOT appear to use the name
    in the verification (it's a pure serial check).
    # ASSUMPTION: name is not used in serial verification based on the writeups
    which only describe a standalone serial check with no name involvement.
    """
    decoded = decode_serial(serial)
    if decoded is None:
        return False
    
    m, r, s = decoded
    
    # Check m has even bit_length (MSB on odd position from LSB)
    if m == 0:
        return False
    if m.bit_length() % 2 != 0:
        return False
    
    # Verify the ECNR signature
    return verify_signature(m, r, s)

def keygen(name=None):
    """
    Generate a valid serial.
    # ASSUMPTION: name is not used (pure serial keygen)
    """
    m = gen_message()
    r, s = sign(m)
    return encode_serial(m, r, s)


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
            print(_sv)
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
