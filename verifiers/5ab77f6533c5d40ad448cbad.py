import struct
import ctypes

# ---------------------------------------------------------------------------
# Helpers ported directly from keygen.cpp
# ---------------------------------------------------------------------------

def charconv(c):
    """charconv from keygen.cpp – maps a byte value."""
    c = c & 0xFF
    if c < 32:
        return (c + 32) & 0xFF
    elif c > 126:
        return (c - 128) & 0xFF
    elif 96 < c < 123:          # lowercase a-z -> uppercase A-Z (shift -32)
        return (c - 32) & 0xFF
    else:
        return c


def checkstr(s):
    """All 5 chars must already be fixed-points under charconv."""
    for i in range(5):
        if charconv(s[i]) != s[i]:
            return False
    return True


def strint(s):
    """Little-endian 5-byte array -> 64-bit integer."""
    m = 0
    for i in range(4, -1, -1):
        m = m * 256 + s[i]
    return m


def intstr(w):
    """64-bit integer -> little-endian 5-byte array."""
    s = [0] * 5
    w1 = w & 0xFFFFFFFFFFFFFFFF  # keep 64-bit
    for i in range(5):
        s[i] = w1 % 256
        w1 //= 256
    return s


def strconv(str2, str3, str4, str5):
    """Compute str1 from str2..str5 using the magic constant."""
    w2 = strint(str2)
    w3 = strint(str3)
    w4 = strint(str4)
    w5 = strint(str5)
    w = 44261125337190
    w = w // 255
    w1 = (w - w2 // 8 - w3 // 16 - w4 // 32 - w5 // 64) * 4
    str1 = intstr(w1)
    str1.append(0)  # 6th byte = 0
    return str1


def change1(str1, str2, str3, str4, str5):
    """Adjust str2/str4 based on str1 values, then recompute str1."""
    for i in range(4):
        if str1[i] > 128:
            str2[i + 1] = charconv(str2[i + 1] + 1)
        elif str1[i] > 96:
            str4[i + 1] = charconv(str4[i + 1] + 1)
        if str1[i] < 32:
            str4[i + 1] = charconv(str4[i + 1] - 1)
    if str1[4] < 32:
        str2[4] = charconv(str2[4] + 64 - 2 * str1[4])
    if str1[4] > 96:
        str2[4] = charconv(str2[4] + (str1[4] - 96) * 2)
    new_str1 = strconv(str2, str3, str4, str5)
    for i in range(6):
        str1[i] = new_str1[i]


def allcharxor(str1, str2, str3, str4, str5):
    a = 1
    for i in range(1, 5):
        a ^= str1[i]
    for i in range(5):
        a ^= str2[i]
    for i in range(5):
        a ^= str3[i]
    for i in range(5):
        a ^= str4[i]
    for i in range(5):
        a ^= str5[i]
    return a & 0xFF


def change2(str1, str2, str3, str4, str5, a, i1):
    i = i1 % 4
    j = i1 // 4
    if i == 0:
        str5[j] = charconv(str5[j] ^ a)
    elif i == 1:
        str4[j] = charconv(str4[j] ^ a)
    elif i == 2:
        str3[j] = charconv(str3[j] ^ a)
    elif i == 3:
        str2[j] = charconv(str2[j] ^ a)


# ---------------------------------------------------------------------------
# Keygen: produce a valid 25-char serial (5 groups of 5 printable chars)
# ASSUMPTION: the crackme accepts any serial produced by the keygen regardless
# of name – the solution write-up does not show a name-dependent derivation.
# The serial is a 25-character string split into five 5-char groups.
# ---------------------------------------------------------------------------

MAX_ITER = 100000  # safety cap


def _make_initial_strs():
    """Return four 5-byte lists that are already charconv-clean and printable."""
    # Use simple ASCII uppercase letters which are fixed-points under charconv
    # (they are in range 32-96 exclusive of a-z, so charconv returns them as-is)
    base = [ord('A'), ord('B'), ord('C'), ord('D'), ord('E')]
    s2 = list(base)
    s3 = [ord(c) for c in 'FGHIJ']
    s4 = [ord(c) for c in 'KLMNO']
    s5 = [ord(c) for c in 'PQRST']
    return s2, s3, s4, s5


def keygen(name=None):
    """
    Generate a valid serial string.
    ASSUMPTION: serial is name-independent (no name processing found in writeup).
    Returns a 25-character string (the concatenation of five 5-char groups).
    """
    str2, str3, str4, str5 = _make_initial_strs()

    # Apply charconv to each starting char (as the original keygen does after cin)
    for i in range(5):
        str2[i] = charconv(str2[i])
        str3[i] = charconv(str3[i])
        str4[i] = charconv(str4[i])
        str5[i] = charconv(str5[i])

    str1 = strconv(str2, str3, str4, str5)

    # Phase 1: make str1 a fixed-point under charconv
    iterations = 0
    while not checkstr(str1[:5]):
        change1(str1, str2, str3, str4, str5)
        iterations += 1
        if iterations > MAX_ITER:
            raise RuntimeError("Phase 1 did not converge")

    # Phase 2: make allcharxor == 0
    a = allcharxor(str1, str2, str3, str4, str5)
    idx = 0
    iterations = 0
    while a != 0:
        change2(str1, str2, str3, str4, str5, a, idx)
        str1 = strconv(str2, str3, str4, str5)
        while not checkstr(str1[:5]):
            change1(str1, str2, str3, str4, str5)
        a = allcharxor(str1, str2, str3, str4, str5)
        idx += 1
        if idx > 19:
            idx = 0
        iterations += 1
        if iterations > MAX_ITER:
            raise RuntimeError("Phase 2 did not converge")

    serial = ''.join(chr(b) for b in str1[:5]) + \
             ''.join(chr(b) for b in str2) + \
             ''.join(chr(b) for b in str3) + \
             ''.join(chr(b) for b in str4) + \
             ''.join(chr(b) for b in str5)
    return serial


# ---------------------------------------------------------------------------
# Verify: re-implement the crackme's two checks from the disassembly
#
# Check 1 (from disassembly):
#   DS:[403068] == 0x58A73066  AND  DS:[40306C] == 0x2841
#
# The serial is stored at 0x403080 (5 groups * 5 bytes = 25 bytes).
# The memory layout means:
#   bytes 0-3  of the serial area live at 403080
#   bytes at offset 0x68-0x80 = 0x-E8 ... 
#   ASSUMPTION: [403068] and [40306C] map to specific bytes of the serial.
#   Offset from 403080: 403068 - 403080 = -0x18 (before the serial area).
#   That means the check values are derived from an intermediate computation,
#   NOT directly from the raw serial bytes.
#
# The keygen ensures the two mathematical invariants hold:
#   1. strconv(str1,str2,str3,str4,str5) is self-consistent (str1 fixed-point)
#   2. allcharxor(...) == 0
#
# ASSUMPTION: these two conditions correspond exactly to the two CMP checks.
# ---------------------------------------------------------------------------

def verify(name, serial):
    """
    Verify a serial string (25 printable characters).
    ASSUMPTION: name is not used in the check (no name logic in writeup).
    The serial is split into five 5-char groups: str1..str5.
    Two conditions must hold:
      1. checkstr(str1) – all chars are charconv fixed-points
      2. allcharxor(str1..str5) == 0
      3. strconv(str2,str3,str4,str5) == str1  (mathematical consistency)
    """
    if len(serial) < 25:
        return False

    # Expect format: 5 groups of 5 chars (possibly space-separated or plain)
    # Strip spaces if present
    parts = serial.split()
    if len(parts) == 5 and all(len(p) == 5 for p in parts):
        groups = parts
    elif len(serial) == 25:
        groups = [serial[i*5:(i+1)*5] for i in range(5)]
    else:
        return False

    str1 = [ord(c) for c in groups[0]]
    str2 = [ord(c) for c in groups[1]]
    str3 = [ord(c) for c in groups[2]]
    str4 = [ord(c) for c in groups[3]]
    str5 = [ord(c) for c in groups[4]]

    # Condition 1: str1 must be a charconv fixed-point
    if not checkstr(str1):
        return False

    # Condition 2: allcharxor must be 0
    if allcharxor(str1, str2, str3, str4, str5) != 0:
        return False

    # Condition 3: str1 must equal strconv(str2,str3,str4,str5)
    expected_str1 = strconv(str2, str3, str4, str5)
    if str1 != expected_str1[:5]:
        return False

    return True


# ---------------------------------------------------------------------------
# Quick self-test
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
