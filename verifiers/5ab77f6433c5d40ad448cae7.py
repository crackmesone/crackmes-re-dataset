#!/usr/bin/env python3
"""
Keygen/verifier for andrewl.us UPSKiRT crackme.

Serial format: S1-S2-S3
  S1 = 24-char string from charset "#cRaCkInG4NeWbIeS" + 7 random alpha chars,
       with no duplicates in the first 17 chars from the charset.
  S2 = 24-hex-char big number
  S3 = 24-hex-char big number

Algorithm:
  1. Build m from first 12 bytes of S1 XOR'd with (S1[i+12] << 4) for i in 0..11
     i.e. for i in range(12): seed[i] ^= (seed[i+12] << 4) & 0xFF
     Then m = big integer from those 12 bytes (big-endian).

  2. Constants (hex):
     key = 0x5F94CF4E06C11B198137892
     p1  = 0x19FBD41D69AA3D86009A968D
     p2  = 0x1B6F141F98EEB619BC036051

  3. Compute S2:
     h = (p2 + m) * key
     n = (h // p2 + 1) * p2
     s2 = n - h
     (then zero-pad s2 hex to 24 chars)

  4. Compute S3:
     s3 = (s2 * p1 + m) // p2
     (then zero-pad s3 hex to 24 chars)

  5. Verification:
     Rebuild m from S1 as above.
     Check that s2 * p2 - s3 * p1 == m   (equivalently s3*p1 == s2*p2 - m)
     (From solution PDF: verify (p2*s2 - p1*s3) == m,
      which matches the keygen: s2 = n - h = ceil(h/p2)*p2 - h,
      meaning s2 ≡ -(p2+m)*key (mod p2), and the final check is
      s2*p2 - s3*p1 == m)
"""

import random
import string

# Constants (hex)
KEY = 0x5F94CF4E06C11B198137892
P1  = 0x19FBD41D69AA3D86009A968D
P2  = 0x1B6F141F98EEB619BC036051

ALFA = "#cRaCkInG4NeWbIeS"  # length 17


def fill_zeros(s, length=24):
    """Zero-pad hex string on the left to 'length' characters."""
    return s.zfill(length)


def s1_to_m(s1):
    """
    Given S1 (24-char string), compute big integer m.
    Take first 24 bytes, XOR first 12 with (byte[i+12] << 4) & 0xFF,
    then interpret the 12 result bytes as a big-endian integer.
    """
    seed = [ord(c) for c in s1]
    for i in range(12):
        seed[i] ^= (seed[i + 12] << 4) & 0xFF
    # Convert first 12 bytes to big integer (big-endian)
    m = 0
    for i in range(12):
        m = (m << 8) | seed[i]
    return m


def compute_s2_s3(m):
    """Given m, compute S2 and S3 as hex strings (24 chars, uppercase)."""
    # h = (p2 + m) * key
    h = (P2 + m) * KEY
    # n = (h // p2 + 1) * p2
    n = (h // P2 + 1) * P2
    # s2 = n - h
    s2 = n - h
    # s3 = (s2 * p1 + m) // p2
    s3 = (s2 * P1 + m) // P2
    s2_str = fill_zeros(format(s2, 'X'), 24)
    s3_str = fill_zeros(format(s3, 'X'), 24)
    return s2_str, s3_str


def generate_s1():
    """
    Generate a valid S1 (24 chars).
    First 17 chars: a permutation of indices into ALFA, with
      PermuTable[0] = 9 (fixed) and PermuTable[12] = 4 (fixed).
    Last 7 chars: random uppercase letters.
    Returns the 24-char string.
    """
    # Fixed positions: index 0 -> ALFA[9], index 12 -> ALFA[4]
    # ASSUMPTION: positions 0 and 12 are fixed per the keygen source.
    fixed = {0: 9, 12: 4}
    used = set(fixed.values())
    perm = {}
    perm[0] = 9
    perm[12] = 4
    available = list(set(range(17)) - used)
    random.shuffle(available)
    idx = 0
    for j in range(17):
        if j in perm:
            continue
        perm[j] = available[idx]
        idx += 1
    s1_chars = [ALFA[perm[j]] for j in range(17)]
    # Append 7 random uppercase letters
    for _ in range(7):
        s1_chars.append(random.choice(string.ascii_uppercase))
    return ''.join(s1_chars)


def verify(name, serial):
    """
    Verify a serial. The 'name' field is not used in the algorithm
    (the crackme only checks the serial, not a name).
    Serial format: S1-S2-S3
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    s1_str, s2_str, s3_str = parts
    if len(s1_str) != 24 or len(s2_str) != 24 or len(s3_str) != 24:
        return False

    # Check S1 charset: first 17 chars must be from ALFA with no duplicates
    alfa_set = set(ALFA)
    seen = set()
    for i in range(17):
        c = s1_str[i]
        if c not in alfa_set:
            return False
        if c in seen:
            return False
        seen.add(c)
    # Last 7 chars must be alpha (the keygen uses uppercase letters)
    # ASSUMPTION: any printable char is accepted for last 7 positions by the crackme
    # The crackme only checks the first 17 chars against the charset.

    # Parse s2, s3 as hex integers
    try:
        s2 = int(s2_str, 16)
        s3 = int(s3_str, 16)
    except ValueError:
        return False

    # Compute m from s1
    m = s1_to_m(s1_str)

    # Verification: s2 * p2 - s3 * p1 == m
    # From solution PDF equation: (p2*s2 - p1*s3) == m
    check = s2 * P2 - s3 * P1
    return check == m


def keygen(name):
    """
    Generate a valid serial for the given name.
    The name is not used in the algorithm.
    Returns a serial string S1-S2-S3.
    """
    s1_str = generate_s1()
    # Ensure m < p2 (the keygen hardcodes positions 0 and 12 to achieve this)
    m = s1_to_m(s1_str)
    s2_str, s3_str = compute_s2_s3(m)
    # Verify lengths
    if len(s2_str) != 24 or len(s3_str) != 24:
        # Retry if padding issue (shouldn't happen with fill_zeros)
        return keygen(name)
    return f"{s1_str}-{s2_str}-{s3_str}"



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
