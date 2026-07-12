#!/usr/bin/env python3
"""
Prometheora keygen/verifier - reconstructed from TheSwedishLord/RootRevenant writeup.

The binary takes a single key (no 'name' field) of exactly 28 ASCII bytes.
Algorithm:
  1. Character set check: [A-Z0-9_], exactly 3 underscores, byte sum == 0x778
  2. Underscores must be at positions 10, 15, 23
  3. Last 4 bytes (positions 24-27) must be digits [0-9]
  4. Multiple SipHash-2-4-like checks on the full key and sub-slices
  5. Polynomial fingerprint checks with Murmur-style finalizer

The valid key recovered by the LCG keygen is: PR0M3TH30R_F1R3_UNL34SH_2027
"""

from __future__ import annotations

MASK64 = (1 << 64) - 1

# LCG constants from sub_430410
LCG_SEED = 0x7A3F8C91D2E5B4A6
LCG_MUL  = 0x5851F42D4C957F2D
LCG_INC  = 0x14057B7EF767814F

# data_40d993 (28 bytes XOR table)
XOR_TABLE = bytes.fromhex(
    "123210efd756ed3f5899e759df6303bf"
    "048e255bf24ab9139c22da6c"
)


def u64(x: int) -> int:
    return x & MASK64


def rol(x: int, b: int) -> int:
    b &= 63
    return u64((x << b) | (x >> (64 - b)))


def sip_round(v0, v1, v2, v3):
    v0 = u64(v0 + v1); v1 = rol(v1, 13); v1 ^= v0; v0 = rol(v0, 32)
    v2 = u64(v2 + v3); v3 = rol(v3, 16); v3 ^= v2
    v0 = u64(v0 + v3); v3 = rol(v3, 21); v3 ^= v0
    v2 = u64(v2 + v1); v1 = rol(v1, 17); v1 ^= v2; v2 = rol(v2, 32)
    return v0, v1, v2, v3


def sub_43a320(data: bytes, k0: int, k1: int) -> int:
    """SipHash-2-4 variant (sub_43a320)."""
    k0 = u64(k0); k1 = u64(k1)
    v0 = 0x736F6D6570736575 ^ k0
    v1 = 0x646F72616E646F6D ^ k1
    v2 = 0x6C7967656E657261 ^ k0
    v3 = 0x7465646279746573 ^ k1

    i = 0
    n = len(data)
    while i + 8 <= n:
        m = int.from_bytes(data[i:i+8], 'little')
        v3 ^= m
        v0,v1,v2,v3 = sip_round(v0,v1,v2,v3)
        v0,v1,v2,v3 = sip_round(v0,v1,v2,v3)
        v0 ^= m
        i += 8

    b = (n & 0xFF) << 56
    for j, c in enumerate(data[i:]):
        b |= c << (8 * j)

    v3 ^= b
    v0,v1,v2,v3 = sip_round(v0,v1,v2,v3)
    v0,v1,v2,v3 = sip_round(v0,v1,v2,v3)
    v0 ^= b
    v2 ^= 0xFF

    for _ in range(4):
        v0,v1,v2,v3 = sip_round(v0,v1,v2,v3)

    return u64(v0 ^ v1 ^ v2 ^ v3)


def mix64(x: int) -> int:
    """Murmur-style finalizer from sub_439be0."""
    x = u64(x)
    x ^= x >> 33
    x = u64(x * 0xFF51AFD7ED558CCD)
    x ^= x >> 33
    x = u64(x * 0xC4CEB9FE1A85EC53)
    x ^= x >> 33
    return u64(x)


def sconst(x: int) -> int:
    """Convert possibly negative Python int to u64."""
    return x & MASK64


# Known hash targets (from writeup)
SEG_TARGETS = [
    0x64AB81FECCE00947,
    0x6836A10A23DD8E77,
    0xB4A1E70DFF5EC991,
    0x53966B588E01C554,
]

POLY_TARGETS = [
    0xD6F3AD7FCF60E599,
    0x61AF7543C53E1E80,
    0x2B54EF961ABDF2AF,
    0x6D7B46529261B90E,
    0xF0983FE510642916,
]

# SipHash keys for 4x7-byte segment checks
# ASSUMPTION: The third and fourth key pairs may have arithmetic errors in the writeup
# due to Python int overflow in the hex literals; using as-written.
SEG_KEYS = [
    (0x1234567890ABCDEF, sconst(-0x012345F6789ABCDF)),
    (0x23456789A1BCDF00, sconst(-0x0234568189ABCDF0)),  # ASSUMPTION: trimmed last digit
    (0x3456789AB2CDF011, sconst(-0x45678A3ABCDF0123)),
    (0x456789ABC3DF0122, sconst(-0x6789AC5CDF012345)),
]


def verify(name: str, serial: str) -> bool:
    """
    Prometheora does not use a 'name' field - only a single key/serial.
    name parameter is ignored.
    Returns True if serial passes all validation stages.
    """
    key = serial.encode('ascii') if isinstance(serial, str) else serial

    if len(key) != 0x1C:  # 28 bytes
        return False

    # Stage 1: character set [A-Z][0-9][_], exactly 3 underscores, byte sum == 0x778
    if not all((0x41 <= c <= 0x5A) or (0x30 <= c <= 0x39) or c == 0x5F for c in key):
        return False
    if key.count(0x5F) != 3:
        return False
    if sum(key) != 0x778:
        return False

    # Stage 2: underscores at specific positions, last 4 are digits
    if not (key[10] == key[15] == key[23] == 0x5F):
        return False
    if not all(0x30 <= c <= 0x39 for c in key[24:28]):
        return False

    # Stage 3: SipHash on last 4 bytes
    if sub_43a320(key[24:28], 0x5945415248415348, 0x4B45593031303230) != sconst(-0x3BCFECA119AAAD63):
        return False

    # Stage 4: three full-key SipHash checks
    if sub_43a320(key, sconst(-0x2152411035014542), 0x0123456789ABCDEF) != sconst(-0x06CFC51A936B765B):
        return False
    if sub_43a320(key, sconst(-0x0123456789ABCDF0), 0x1111111111111111) != sconst(-0x3C8EDAE5D64F271E):
        return False
    if sub_43a320(key, sconst(-0x5555555555555556), 0x5555555555555555) != sconst(-0x5B652C3D3EC4CEA2):
        return False

    # Stage 5: four 7-byte segment SipHash checks
    for i in range(4):
        h = sub_43a320(key[i*7:(i+1)*7], SEG_KEYS[i][0], SEG_KEYS[i][1])
        if h != SEG_TARGETS[i]:
            return False

    # Stage 6: polynomial fingerprint checks
    xs = [0x17, 0x2B, 0x3D, 0x4F, 0x61]
    for idx, x in enumerate(xs):
        p = 1
        v = 0
        for c in key:
            v = u64(v + p * c)
            p = u64(p * x)
        if mix64(v) != POLY_TARGETS[idx]:
            return False

    return True


def generate_key_bytes() -> bytes:
    """Recover valid key via LCG XOR keygen (sub_430410)."""
    state = LCG_SEED
    out = bytearray()
    for i in range(0x1C):
        state = u64(state * LCG_MUL + LCG_INC)
        out.append(((state >> 32) & 0xFF) ^ XOR_TABLE[i])
    return bytes(out)


def keygen(name: str) -> str:
    """
    Returns the single known valid key. 'name' is unused.
    The key is deterministically derived from the LCG stream XOR'd with data_40d993.
    """
    # ASSUMPTION: The LCG produces exactly one valid key; there is no name dependency.
    key_bytes = generate_key_bytes()
    return key_bytes.decode('ascii')



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
