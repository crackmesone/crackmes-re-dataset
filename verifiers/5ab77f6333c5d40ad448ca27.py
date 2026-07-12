#!/usr/bin/env python3
"""
Reverse-engineered keygen for 'Nitroito - Crackme#1 by jps'
Based on writeup by xyzero.

Serial format: WWWWWW-XXXXXX-YYYYYY-ZZZZZZ  (total 27 chars including dashes)
Name must be >= 5 characters.
"""

# The base mask string (size 0x32 = 50 bytes)
MASKSTRING = (
    b'1234567890'
    b'ABCDEFGHIJ'
    b'KLMNOPQRST'
    b'UVWXYZ'
    b'\xC1\xC9\xCD\xD3'
    b'\xDA\xC0\xC8\xCC\xD2\xD9\xC2\xCA\xCE\xD4'
)
assert len(MASKSTRING) == 0x32, f"maskstring length={len(MASKSTRING)}"


def build_mask(name: str) -> list:
    """Merge name into the base maskstring.
    The name bytes replace the first len(name) bytes of the maskstring.
    """
    mask = list(MASKSTRING)
    name_bytes = name.encode('latin-1')
    for i, b in enumerate(name_bytes[:0x32]):
        mask[i] = b
    return mask


def compute_k2(mask: list) -> int:
    """Step (a)/(f): compute k2 from a mask array."""
    k1 = 0
    for i in range(0x32):
        k1 = k1 + ((mask[i] + (i + 1)) * 2)
    k2 = k1 + 0x32
    # Treat as 32-bit unsigned
    k2 = k2 & 0xFFFFFFFF
    return k2


def compute_k4_forward(k2: int, mask: list) -> int:
    """Step (b): compute k4 using forward mask order.
    k3 = k2 XOR (mask[0x32-i-1] * (1+i))
    k4 = k4 + k3
    k5 = k2 XOR (i+1)
    k6 = k4 OR k5
    k4 = k6
    """
    k4 = 0
    for i in range(0x32):
        k3 = (k2 ^ (mask[0x32 - i - 1] * (1 + i))) & 0xFFFFFFFF
        k4 = (k4 + k3) & 0xFFFFFFFF
        k5 = (k2 ^ (i + 1)) & 0xFFFFFFFF
        k6 = (k4 | k5) & 0xFFFFFFFF
        k4 = k6
    return k4


def compute_k4_reverse(k2: int, mask: list) -> int:
    """Step (d) variant: compute k4 using reverse mask order (for XXXXXX and YYYYYY).
    k3 = (k2 XOR mask[i]) * (1+i)
    k4 = k4 + k3
    k5 = k2 XOR (i+1)
    k6 = k4 OR k5
    k4 = k6
    """
    # ASSUMPTION: the 'reverse' variant uses mask[i] (not mask[0x32-i-1]) and same k4 accumulation logic
    k4 = 0
    for i in range(0x32):
        k3 = ((k2 ^ mask[i]) * (1 + i)) & 0xFFFFFFFF
        k4 = (k4 + k3) & 0xFFFFFFFF
        k5 = (k2 ^ (i + 1)) & 0xFFFFFFFF
        k6 = (k4 | k5) & 0xFFFFFFFF
        k4 = k6
    return k4


def k4_to_segment(k4: int, reverse: bool = False) -> str:
    """Step (c): convert k4 to a 6-character segment.
    k7 = k4 / 0x1A
    k8 = k4 MOD 0x1A
    k9 = k8 & 0xFF
    k4 = k7
    if k9 - 0xA < 0: char = chr(k8 + 0x30)   # digit-ish
    else:
        k9 -= 0x1A
        if k9 < 0: char = chr(k8 + 0x37)      # uppercase letter
        else: # ASSUMPTION: fallback, treat as letter
            char = chr(k8 + 0x37)
    """
    chars = []
    k4_val = k4
    for _ in range(6):
        k7 = k4_val // 0x1A
        k8 = k4_val % 0x1A
        k9 = k8 & 0xFF
        k4_val = k7
        k9_check = k9 - 0xA
        if k9_check < 0:
            c = chr(k8 + 0x30)
        else:
            k9_check2 = k9_check - 0x1A
            if k9_check2 < 0:
                c = chr(k8 + 0x37)
            else:
                # ASSUMPTION: wrap or treat same as letter branch
                c = chr((k8 % 26) + 0x41)
        chars.append(c)
    if reverse:
        chars = chars[::-1]
    return ''.join(chars)


def build_mask1(mask: list) -> list:
    """Step (e): mask1[i] = mask[i] + maskstring[i]*2  (mod 256 assumed)"""
    mask1 = []
    for i in range(0x32):
        val = (mask[i] + MASKSTRING[i] * 2) & 0xFF
        mask1.append(val)
    return mask1


def keygen(name: str) -> str:
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")

    # Build first mask (name merged into maskstring)
    mask = build_mask(name)

    # Compute first k2
    k2 = compute_k2(mask)

    # WWWWWW: forward accumulation, no reversal
    k4_w = compute_k4_forward(k2, mask)
    W = k4_to_segment(k4_w, reverse=False)

    # XXXXXX: reverse-order accumulation, then invert string
    k4_x = compute_k4_reverse(k2, mask)
    X = k4_to_segment(k4_x, reverse=True)

    # Build mask1 for second half
    mask1 = build_mask1(mask)

    # New k2 for mask1
    k2b = compute_k2(mask1)

    # YYYYYY: reverse-order accumulation with mask1, then invert string
    # Step (g): k3 = (k2 XOR mask1[i])*(1+i) and invert
    k4_y = compute_k4_reverse(k2b, mask1)
    Y = k4_to_segment(k4_y, reverse=True)

    # ZZZZZZ: forward accumulation with mask1 (same as b but using mask1)
    # Step (g): k3 = k2 XOR (mask1[0x32-i-1])*(1+i)
    k4_z = compute_k4_forward(k2b, mask1)
    Z = k4_to_segment(k4_z, reverse=False)

    serial = f"{W}-{X}-{Y}-{Z}"
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    if len(name) < 5:
        return False
    if len(serial) != 27:
        return False
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    # Check dashes at positions 6, 13, 20
    if serial[6] != '-' or serial[13] != '-' or serial[20] != '-':
        return False
    expected = keygen(name)
    return serial == expected



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
