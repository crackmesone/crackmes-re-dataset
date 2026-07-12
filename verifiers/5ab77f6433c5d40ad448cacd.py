#!/usr/bin/env python3
"""
Reverse-engineered keygen for cm_funcmaze_by_gavin.soung

The crackme uses a 'function maze': a hash-like procedure maps
(Name[16], Serial[32]) -> ESI values per iteration, and those ESI
values index into a table of small functions that write bytes into
a result buffer at 0x40D500.  The target result is "SUCCESS\0",
plus DWORD [40D520] >= 5, and BYTE [40D51D] == 1.

The algorithm (as documented in the writeup) is:

1. Expand Name  to 16 bytes by repeating (uppercase).
2. Expand Serial to 32 bytes by repeating.
3. For each i in 0..15:
     a. Compute ECX from Name[i]
     b. Compute EAX from Serial[i]
     c. Adjust ECX using Serial[i+16]
     d. Wrap ECX into [0,100)
     e. ESI = (Serial[i+16] % 10) * 100 + ECX   =>  ESI in [0, 1000)
     f. Call small-function table[ESI]  (which writes to result buffer)
     g. Special case for i==9: also call neighbours if ESI conditions met

We need specific ESI values per iteration so that the result buffer
spells out "SUCCESS\0", [40D520] >= 5, and [40D51D] == 1.

Required ESI constants (from writeup):
  i=0  -> S : 0xF64 = 3940
  i=1  -> U : one of [0x66c=1644, 0x870=2160, 0x8C0=2240, 0xD64=3428]
  i=2  -> C : one of [0x990=2448, 0xD98=3480]
  i=3  -> C : one of [0x150=336, 0x418=1048, 0x5F0=1520, 0x8A0=2208, 0xFA0=4000]
  i=4  -> E : one of [0x410=1040, 0x45C=1116, 0x538=1336, 0xBF0=3056]
  i=5  -> S : one of [0x758=1880, 0xF2C=3884]
  i=6  -> S : one of [0x2C=44, 0x6A0=1696, 0xAB0=2736, 0xCFC=3324, 0xD1C=3356, 0xF24=3876]
  # finalization (triggering check): C28 = 3112  -- must appear somewhere
  i=7  -> harmless + finalization: one of [0x5A4=1444, 0x5E0=1504, 0x74=116, 0x1F8=504,
                                           0x264=612, 0x860=2144, 0xA58=2648, 0xD44=3396,
                                           0xF7C=3964, 0xC28=3112]
  i=8  -> harmless : 0xC28=3112  (finalization)
  # i=9 is special (extra calls to neighbours) -> use 0xD44=3396 (harmless)
  i=9  -> 0xD44 = 3396
  i=10..15 -> harmless: use 0x5A4=1444 each
"""

import string

# ---------------------------------------------------------------------------
# helper: expand a string to exactly 'length' bytes by repeating, uppercase
# ---------------------------------------------------------------------------
def expand(s, length, upper=False):
    if not s:
        raise ValueError("empty string")
    if upper:
        s = s.upper()
    out = []
    for j in range(length):
        out.append(ord(s[j % len(s)]))
    return out


# ---------------------------------------------------------------------------
# Compute ESI for iteration i given Name16 and Serial32 arrays
# ---------------------------------------------------------------------------
def compute_esi(name16, serial32, i):
    n = name16[i]
    s_lo = serial32[i]       # Serial[i]
    s_hi = serial32[i + 16]  # Serial[i+16]

    # ECX from Name[i]
    if not (ord('0') <= n <= ord('9')):
        ecx = 50 - (n % 10)
    else:
        ecx = 50 + (n % 10)
    # ECX in [41, 59]

    # EAX from Serial[i]
    if not (ord('0') <= s_lo <= ord('9')):
        if not (ord('A') <= s_lo <= ord('Z')):
            # lowercase a-z
            eax = s_lo - ord('=')
        else:
            eax = s_lo - ord('7')
    else:
        eax = s_lo - ord('0')
    # EAX in [0, 61]

    # adjust ECX using Serial[i+16]
    if not (ord('0') <= s_hi <= ord('9')):
        ecx -= eax
    else:
        ecx += eax

    # wrap into [0, 100)
    if ecx >= 100:
        ecx -= 100
    if ecx < 0:
        ecx += 100

    int_buf = s_hi % 10
    esi = int_buf * 100 + ecx
    return esi


# ---------------------------------------------------------------------------
# Target ESI values per iteration (chosen from valid sets in writeup)
# ---------------------------------------------------------------------------
TARGET_ESI = [
    3940,   # i=0  S
    1644,   # i=1  U (0x66c)
    2448,   # i=2  C (0x990)
    1048,   # i=3  C (0x418)
    1040,   # i=4  E (0x410)
    1880,   # i=5  S (0x758)
    1696,   # i=6  S (0x6A0)
    3112,   # i=7  finalization C28 (0xC28)
    1444,   # i=8  harmless (0x5A4)
    3396,   # i=9  harmless D44 (special case)
    1444,   # i=10 harmless
    1444,   # i=11 harmless
    1444,   # i=12 harmless
    1444,   # i=13 harmless
    1444,   # i=14 harmless
    1444,   # i=15 harmless
]

# valid characters for name/serial
VALID_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits


# ---------------------------------------------------------------------------
# verify(name, serial) -> bool
# Checks that all 16 iterations produce the required ESI values.
# This is a necessary (but due to function-table unknowns, not fully
# verifiable in Python) condition.
# ---------------------------------------------------------------------------
def verify(name: str, serial: str) -> bool:
    # validate characters
    for c in name:
        if c not in VALID_CHARS:
            return False
    for c in serial:
        if c not in VALID_CHARS:
            return False
    if len(serial) < 1 or len(name) < 1:
        return False

    name16   = expand(name,   16, upper=True)
    serial32 = expand(serial, 32, upper=False)

    for i in range(16):
        esi = compute_esi(name16, serial32, i)
        if esi != TARGET_ESI[i]:
            return False
    return True


# ---------------------------------------------------------------------------
# Solve for a serial character pair (lo, hi) that produces a target ESI
# given Name[i] (as integer).
# ESI = (s_hi % 10) * 100 + ecx
# where ecx depends on s_lo and s_hi.
# ---------------------------------------------------------------------------
def solve_serial_chars(n: int, target_esi: int):
    """
    Find (s_lo_char, s_hi_char) in VALID_CHARS x VALID_CHARS such that
    compute_esi with Name[i]=n produces target_esi.
    Returns (lo_char, hi_char) or raises ValueError.
    """
    for s_hi_c in VALID_CHARS:
        s_hi = ord(s_hi_c)
        hi_mod10 = s_hi % 10
        needed_ecx = target_esi - hi_mod10 * 100
        if needed_ecx < 0 or needed_ecx >= 100:
            continue

        # Determine if s_hi is a digit (affects ecx adjustment direction)
        s_hi_is_digit = ord('0') <= s_hi <= ord('9')

        # ECX from Name[i]
        if not (ord('0') <= n <= ord('9')):
            base_ecx = 50 - (n % 10)
        else:
            base_ecx = 50 + (n % 10)

        # We need ecx_adjusted = needed_ecx
        # ecx_adjusted = (base_ecx +/- eax) mod-wrapped
        # Try all valid s_lo characters
        for s_lo_c in VALID_CHARS:
            s_lo = ord(s_lo_c)
            # EAX from Serial[i]
            if not (ord('0') <= s_lo <= ord('9')):
                if not (ord('A') <= s_lo <= ord('Z')):
                    eax = s_lo - ord('=')
                else:
                    eax = s_lo - ord('7')
            else:
                eax = s_lo - ord('0')

            if s_hi_is_digit:
                ecx_adj = base_ecx + eax
            else:
                ecx_adj = base_ecx - eax

            if ecx_adj >= 100:
                ecx_adj -= 100
            if ecx_adj < 0:
                ecx_adj += 100

            if ecx_adj == needed_ecx:
                return s_lo_c, s_hi_c

    raise ValueError(f"No serial chars found for n={n}, target_esi={target_esi}")


# ---------------------------------------------------------------------------
# keygen(name) -> serial string of 32 chars
# ---------------------------------------------------------------------------
def keygen(name: str) -> str:
    name16 = expand(name, 16, upper=True)
    lo_chars = []
    hi_chars = []
    for i in range(16):
        lo, hi = solve_serial_chars(name16[i], TARGET_ESI[i])
        lo_chars.append(lo)
        hi_chars.append(hi)
    serial = ''.join(lo_chars) + ''.join(hi_chars)
    return serial


# ---------------------------------------------------------------------------
# Main / demo
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
