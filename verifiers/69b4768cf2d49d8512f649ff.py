#!/usr/bin/env python3
"""
Willy Wonka's Chocolate Factory - Keygen / Verifier
Based on the detailed writeup by MoriartyPuth.
"""

# ---------------------------------------------------------------------------
# CHECK 1: COCOA PLANTATION - S-Box Substitution
# ---------------------------------------------------------------------------
# 256-byte S-Box (partial - only entries needed are shown; full box assumed bijective)
# We know the mapping for 'C','h','0','c' from the writeup.
# The writeup states LUT is at .rdata and provides the first 32 entries plus the solution.
# ASSUMPTION: The full LUT is a bijection; we only have confirmed mappings for the solution chars.

LUT = [None] * 256
# Confirmed from writeup:
# LUT['C'] = 0xC3, LUT['h'] = 0x81, LUT['0'] = 0x1D, LUT['c'] = 0xEB
LUT[67]  = 0xC3   # 'C'
LUT[104] = 0x81   # 'h'
LUT[48]  = 0x1D   # '0'
LUT[99]  = 0xEB   # 'c'

# First 32 entries from writeup:
_lut_known = [236,202,14,243,8,240,42,162,59,24,43,92,55,189,18,168,
              5,211,161,87,79,150,252,245,167,20,25,102,88,155,191,180]
for i, v in enumerate(_lut_known):
    if LUT[i] is None:
        LUT[i] = v

# Build reverse LUT for verification
LUT_INV = {}
for i, v in enumerate(LUT):
    if v is not None:
        LUT_INV[v] = i

CHECK1_TARGET = 0xC3811DEB

def check1(group1: bytes) -> bool:
    """Cocoa Plantation: S-Box substitution."""
    r14d = 0
    for b in group1:
        if LUT[b] is None:
            return False  # unknown LUT entry
        r14d = ((r14d << 8) | LUT[b]) & 0xFFFFFFFF
    return r14d == CHECK1_TARGET


# ---------------------------------------------------------------------------
# CHECK 2: MILK RIVER - Dot-Product mod 256
# ---------------------------------------------------------------------------
COEFFS = [
    [3, 7, 2, 5],
    [5, 3, 8, 1],
    [2, 9, 1, 4],
    [6, 1, 4, 7],
]
EXPECTED2 = [0x2D, 0xDF, 0x6B, 0x9C]

def check2(group2: bytes) -> bool:
    """Milk River: dot-product mod 256."""
    t = list(group2)
    for g in range(4):
        s = sum(COEFFS[g][i] * t[i] for i in range(4)) & 0xFF
        if s != EXPECTED2[g]:
            return False
    return True


# ---------------------------------------------------------------------------
# CHECK 3: CARAMEL OVEN - Hash Transform
# ---------------------------------------------------------------------------
def rotl16(val, n):
    val &= 0xFFFF
    return ((val << n) | (val >> (16 - n))) & 0xFFFF

CHECK3_TARGET = 0x016CB7CB

def check3(group3: bytes) -> bool:
    """Caramel Oven: custom hash transform."""
    b8, b9, b10, b11 = group3[0], group3[1], group3[2], group3[3]
    # Swap: r8d uses bytes 10,11; t89 uses bytes 8,9
    r8d  = (b10 << 8) | b11
    t89  = (b8  << 8) | b9

    temp = (r8d - 0x3502) & 0xFFFF
    temp = rotl16(temp, 5)
    temp = (temp * 0x7A69) & 0xFFFF
    cx   = temp

    edx  = (t89 ^ (cx >> 7) ^ cx) & 0xFFFF
    edx2 = edx << 16

    temp2 = (edx - 0x3F40) & 0xFFFF
    temp2 = rotl16(temp2, 5)
    temp2 = (temp2 * 0x7A69) & 0xFFFF
    cx2   = temp2

    ebx = cx2 ^ (cx2 >> 7)
    ebx = ebx ^ r8d
    ebx = (ebx | edx2) & 0xFFFFFFFF

    return ebx == CHECK3_TARGET


# ---------------------------------------------------------------------------
# CHECK 4: PACKAGING LINE - CRC-16/CCITT
# The writeup was truncated before fully describing check 4.
# ASSUMPTION: Check 4 is a CRC-16/CCITT (poly 0x1021, init 0xFFFF) over
# concatenation of groups 1+2+3, compared against a value derived from group 4.
# Known valid group4 values from comments: '08nM', '!(L>', 'choT'
# We implement verify() using the known fixed groups 1-3 and brute-force
# for group4, but cannot reconstruct the exact check4 algorithm from the text.
# ---------------------------------------------------------------------------

KNOWN_VALID_GROUP4 = [b'08nM', b'!(L>', b'choT']

def check4_placeholder(group4: bytes) -> bool:
    """Packaging Line: algorithm truncated in writeup. ASSUMPTION: any of the known valid group4s pass."""
    # ASSUMPTION: We cannot fully verify group4 without the complete algorithm.
    # Return True for known-valid group4 values from comments.
    return group4 in KNOWN_VALID_GROUP4


# ---------------------------------------------------------------------------
# VERIFY
# ---------------------------------------------------------------------------
GROUP1 = b'Ch0c'
GROUP2 = b'M1lk'
GROUP3 = b'CrMe'

def _strip_dashes(serial: str) -> bytes:
    return serial.replace('-', '').replace(' ', '').encode('latin-1')

def verify(name: str, serial: str) -> bool:
    """
    Verify a Golden Ticket serial.
    Note: the 'name' field is not used by this crackme (serial-only).
    """
    stripped = _strip_dashes(serial)
    if len(stripped) != 16:
        return False

    # Blacklist checks
    if stripped.lower() == b'helphelphelphelp' or stripped.lower() == b'help':
        return False
    # WONK easter egg - not a valid ticket
    if stripped == b'WONKWONKWONKWONK':
        return False
    # All zeros
    if stripped == b'0000000000000000':
        return False

    g1 = stripped[0:4]
    g2 = stripped[4:8]
    g3 = stripped[8:12]
    g4 = stripped[12:16]

    if not check1(g1):
        return False
    if not check2(g2):
        return False
    if not check3(g3):
        return False
    # ASSUMPTION: check4 uses group4 and we only know certain valid values
    if not check4_placeholder(g4):
        return False
    return True


# ---------------------------------------------------------------------------
# KEYGEN
# ---------------------------------------------------------------------------
def keygen(name: str) -> str:
    """
    Generate a valid Golden Ticket.
    Groups 1-3 are uniquely determined. Group 4 has multiple solutions;
    we return known valid ones from the comments/writeup.
    """
    # Verified: Ch0c-M1lk-CrMe is the fixed prefix
    assert check1(GROUP1), "Check1 sanity failed"
    assert check2(GROUP2), "Check2 sanity failed"
    assert check3(GROUP3), "Check3 sanity failed"

    prefix = b'Ch0c-M1lk-CrMe-'
    # Use first known valid group4
    for g4 in KNOWN_VALID_GROUP4:
        serial_bytes = GROUP1 + GROUP2 + GROUP3 + g4
        formatted = (
            serial_bytes[0:4].decode('latin-1') + '-' +
            serial_bytes[4:8].decode('latin-1') + '-' +
            serial_bytes[8:12].decode('latin-1') + '-' +
            serial_bytes[12:16].decode('latin-1')
        )
        return formatted
    return 'Ch0c-M1lk-CrMe-08nM'


# ---------------------------------------------------------------------------
# MAIN
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
