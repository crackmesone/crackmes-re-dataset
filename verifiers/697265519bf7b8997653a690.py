#!/usr/bin/env python3
"""
Ragnarok KeygenMe - Yggdrasil VM Keygen
Based on reverse engineering write-up by akiselev and G3orge's verified example.
"""

import struct

TARGET = 0x13371337CAFEBABE
MASK64 = 0xFFFFFFFFFFFFFFFF

# ---------------------------------------------------------------------------
# PRNG / hashing primitives
# ---------------------------------------------------------------------------

def fnv1a_32(name: str) -> int:
    """FNV-1a 32-bit hash of the username."""
    h = 0x811C9DC5
    for ch in name.encode('latin-1'):
        h = ((h ^ ch) * 0x01000193) & 0xFFFFFFFF
    return h


def lcg_next(state: int) -> int:
    """Single LCG step: state = state * 0x41c64e6d + 0x3039 (mod 2^32)."""
    return (state * 0x41C64E6D + 0x3039) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Bytecode parameter derivation
# ---------------------------------------------------------------------------

def derive_params(name: str):
    """
    Derive C1-C4 (30-bit coefficients) and p1-p4 (15-bit offsets) from username.

    Coefficient extraction (two LCG steps per coefficient):
        s1 = lcg(state)
        s2 = lcg(s1)
        C  = ((s1 >> 16) & 0x7FFF) | (s2 & 0x7FFF0000)
    Offset extraction (one LCG step per offset):
        s  = lcg(state)
        p  = (s >> 16) & 0x7FFF
    """
    state = fnv1a_32(name)

    coeffs = []
    for _ in range(4):
        s1 = lcg_next(state)
        s2 = lcg_next(s1)
        c = ((s1 >> 16) & 0x7FFF) | (s2 & 0x7FFF0000)
        coeffs.append(c)
        state = s2  # advance state past the two steps used

    offsets = []
    for _ in range(4):
        state = lcg_next(state)
        p = (state >> 16) & 0x7FFF
        offsets.append(p)

    return coeffs, offsets


# ---------------------------------------------------------------------------
# VM equation (lifted from bytecode analysis)
# ---------------------------------------------------------------------------
#
# R1 = (C1 ^ S1) + p1
# R2 = (C2 + S2) ^ p2
# R3 = (C3 - S3) + p3          (all arithmetic mod 2^64)
# R4 = (C4 ^ S4) ^ p4
# R0 = R1 + R2 + R3 + R4
# Success: R0 == TARGET
#
# We fix S1=S2=S3=0 and solve for S4.
# ---------------------------------------------------------------------------

def _u64(x: int) -> int:
    return x & MASK64


def compute_r1(c1, p1, s1):
    return _u64((c1 ^ s1) + p1)


def compute_r2(c2, p2, s2):
    return _u64(_u64(c2 + s2) ^ p2)


def compute_r3(c3, p3, s3):
    return _u64(_u64(c3 - s3) + p3)


def compute_r4(c4, p4, s4):
    return _u64((c4 ^ s4) ^ p4)


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial key for the given username.

    Serial format: four 64-bit hex values separated by '-'.
    Example: AAAA0000BBBB1111-CCCC2222DDDD3333-EEEE4444FFFF5555-0011223344556677
    """
    parts = [p.strip() for p in serial.split('-')]
    if len(parts) != 4:
        return False
    try:
        s = [int(p, 16) & MASK64 for p in parts]
    except ValueError:
        return False

    coeffs, offsets = derive_params(name)
    c1, c2, c3, c4 = coeffs
    p1, p2, p3, p4 = offsets
    s1, s2, s3, s4 = s

    r1 = compute_r1(c1, p1, s1)
    r2 = compute_r2(c2, p2, s2)
    r3 = compute_r3(c3, p3, s3)
    r4 = compute_r4(c4, p4, s4)

    r0 = _u64(r1 + r2 + r3 + r4)
    return r0 == TARGET


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.

    Strategy: fix S1=S2=S3=0, solve for S4.

    From the equation:
        TARGET = R1 + R2 + R3 + R4   (mod 2^64)
        R4 = TARGET - (R1 + R2 + R3) (mod 2^64)
        R4 = (C4 ^ S4) ^ p4
        => C4 ^ S4 = R4 ^ p4
        => S4 = C4 ^ (R4 ^ p4)
    """
    coeffs, offsets = derive_params(name)
    c1, c2, c3, c4 = coeffs
    p1, p2, p3, p4 = offsets

    # Fix first three serial parts to zero
    s1, s2, s3 = 0, 0, 0

    r1 = compute_r1(c1, p1, s1)
    r2 = compute_r2(c2, p2, s2)
    r3 = compute_r3(c3, p3, s3)

    partial = _u64(r1 + r2 + r3)

    # Solve for R4
    r4_needed = _u64(TARGET - partial)

    # Invert R4 = (C4 ^ S4) ^ p4  =>  S4 = C4 ^ (r4_needed ^ p4)
    s4 = c4 ^ (r4_needed ^ p4)
    s4 = _u64(s4)

    serial = '{:016X}-{:016X}-{:016X}-{:016X}'.format(s1, s2, s3, s4)
    return serial


# ---------------------------------------------------------------------------
# Self-test against known-good example from comments
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
