# NOTE: This is a partial reconstruction. The algorithm is extremely complex,
# involving a custom hash (wHash), a custom block cipher (MMB/encrypt_blk),
# Rabin cryptosystem (square roots mod primes p, q), DSA-like signature,
# and bignum operations. Many internals of wHash (assembly) are not fully
# translatable without running the original binary.
#
# ASSUMPTION: We implement the high-level structure as described, but
# wHash is only partially reconstructable from the assembly.
# ASSUMPTION: The DSA/Rabin verification logic is only partially shown
# (writeup was truncated).

import struct
from ctypes import c_uint32

MASK32 = 0xFFFFFFFF

# --- MMB block cipher constants ---
# ASSUMPTION: inv[] array from keygen.cpp
inv = [0x0DAD4694, 0x06D6A34A, 0x81B5A8D2, 0x281B5A8D]

def bsw(n):
    n &= 0xFFFFFFFF
    return (((n & 0x000000FF) << 24) |
            ((n & 0x0000FF00) << 8)  |
            ((n & 0x00FF0000) >> 8)  |
            ((n & 0xFF000000) >> 24))

def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def mcinv(ax, bx, cx, dx):
    """MMB inverse MixColumn step."""
    v = [0] * 4
    v[1] = (dx ^ bx ^ ax) & MASK32
    v[3] = (dx ^ bx ^ cx) & MASK32
    v[0] = (cx ^ ax ^ bx) & MASK32
    v[2] = (cx ^ ax ^ dx) & MASK32

    if not (v[3] & 1):
        v[0] ^= 0x2AAAAAAA
    if v[0] & 1:
        v[0] ^= 0x2AAAAAAA

    for i in range(4):
        # ASSUMPTION: MOD is 0xFFFFFFFF per the #define
        v[i] = (inv[i] * v[i]) % 0xFFFFFFFF

    return v[1] & MASK32, v[0] & MASK32, v[3] & MASK32, v[2] & MASK32

def encrypt_blk(v, mulkey):
    """MMB block encryption of 4 DWORDs using mulkey[4]."""
    # Swap pairs
    v[0], v[1] = v[1], v[0]
    v[2], v[3] = v[3], v[2]

    rounds = [
        (3, 2, 1, 0),
        (2, 1, 0, 3),
        (1, 0, 3, 2),
        (0, 3, 2, 1),
        (3, 2, 1, 0),
        (2, 1, 0, 3),
    ]
    xor_indices = [
        (3, 2, 1, 0),
        (2, 1, 3, 0),  # note: v[3]^=mulkey[3], v[2]^=mulkey[0] - from source
        (1, 0, 3, 2),
        (0, 3, 2, 1),
        (3, 2, 1, 0),
        (2, 1, 0, 3),
    ]

    # Round 1
    v[0] ^= mulkey[3]; v[1] ^= mulkey[2]; v[2] ^= mulkey[1]; v[3] ^= mulkey[0]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Round 2
    v[0] ^= mulkey[2]; v[1] ^= mulkey[1]; v[3] ^= mulkey[3]; v[2] ^= mulkey[0]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Round 3
    v[0] ^= mulkey[1]; v[1] ^= mulkey[0]; v[2] ^= mulkey[3]; v[3] ^= mulkey[2]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Round 4
    v[0] ^= mulkey[0]; v[1] ^= mulkey[3]; v[2] ^= mulkey[2]; v[3] ^= mulkey[1]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Round 5
    v[0] ^= mulkey[3]; v[1] ^= mulkey[2]; v[2] ^= mulkey[1]; v[3] ^= mulkey[0]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Round 6 (no mcinv after, just XOR then swap)
    v[0] ^= mulkey[2]; v[1] ^= mulkey[1]; v[2] ^= mulkey[0]; v[3] ^= mulkey[3]
    v[0], v[1], v[2], v[3] = mcinv(v[0], v[1], v[2], v[3])
    # Final XOR
    v[0] ^= mulkey[1]; v[1] ^= mulkey[0]; v[2] ^= mulkey[3]; v[3] ^= mulkey[2]

    # Swap pairs
    v[0], v[1] = v[1], v[0]
    v[2], v[3] = v[3], v[2]
    return v

# --- wHash: partial reconstruction from assembly ---
# ASSUMPTION: wHash is a custom 64-bit hash. The assembly is complex.
# We provide a stub that returns zeros - real implementation requires
# running the original or a full assembly translation.
def wHash(data_bytes, length_val):
    """
    ASSUMPTION: This is a stub for the wHash function.
    The real wHash processes data in 8-byte blocks with a complex
    Feistel-like mixing using ROL, XOR, ADD with constant 0x456C6091,
    and IMUL with 0xAA7110C3. Output is 8 bytes.
    Without running the actual assembly or a verified port, we cannot
    produce correct output.
    """
    # ASSUMPTION: Returning zeros as placeholder
    return b'\x00' * 8

# --- Rabin / DSA verification ---
# ASSUMPTION: The verification checks a DSA-like signature (r, s) against
# a hash of (name). The primes and group parameters are given in the keygen.
# p = 0x654DA59F5E1B70B1FE728D2B55BB
# q = 0x262EFCE70A313E69AD32ECBB081F
# n = p*q (Rabin modulus)
# DSA-like group params (from truncated code):
# g = 5
# p_dsa = 0xF31CB7BBDF75F... (truncated, unknown)
# ASSUMPTION: We cannot reconstruct the full verify() without the complete DSA params.

P_RABIN = 0x654DA59F5E1B70B1FE728D2B55BB
Q_RABIN = 0x262EFCE70A313E69AD32ECBB081F
N_RABIN = P_RABIN * Q_RABIN

N2_HEX = 0x1BEBE779447C86DBC870A9ECFE0044893A8A95C1FC350D71DF0DE8B31
U2_HEX = 0x984390BC304F24B707AE19DC8516C070F935DD82D48AC546263DF011

def verify(name, serial):
    """
    ASSUMPTION: Full verification requires:
    1. Compute name hash via wHash (not fully implemented)
    2. Derive mulkey from hash
    3. Apply Rabin square root finding
    4. Apply modular exponentiation
    5. Apply MMB encrypt_blk
    6. Compute another wHash
    7. Verify DSA signature (r, s) embedded in serial
    
    Without a working wHash and complete DSA parameters,
    this function cannot be fully implemented.
    
    Returns False as placeholder.
    """
    # ASSUMPTION: Cannot implement without wHash and full DSA params
    raise NotImplementedError(
        "verify() cannot be implemented without a working wHash port "
        "and the complete DSA group parameters (p_dsa was truncated in writeup)."
    )

def keygen(name):
    """
    ASSUMPTION: keygen follows the Generate() function in keygen.cpp:
    1. Hash name with wHash to get mulkey
    2. Compute Rabin square roots of hash mod (p,q)
    3. CRT combine to get xx[0]
    4. Compute powmod(xx[0], U2_HEX, N2_HEX)
    5. Encrypt with MMB using mulkey
    6. Hash combined data with wHash
    7. Sign with DSA (using random k)
    8. Format serial as hex string
    
    Cannot be fully implemented without working wHash.
    """
    raise NotImplementedError(
        "keygen() cannot be implemented without a working wHash port "
        "and complete DSA parameters."
    )


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
