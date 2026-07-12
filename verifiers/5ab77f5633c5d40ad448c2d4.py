#!/usr/bin/env python3
"""
Keygen for madeinqc's Keygen-me 1
Based on the solution by e1xis from crackmes.de
"""

# The target values that prevVal1 must equal for each position (mod 8)
COMPARE_TO = [0x09, 0x0D, 0xFF, 0x23, 0x15, 0xFF, 0x1D, 0xD7]
# Note: 0xFF is treated as signed -1 in the original C code (char comparison)
# We need to handle sign: these are signed chars
def to_signed_char(v):
    v = v & 0xFF
    if v >= 128:
        return v - 256
    return v

COMPARE_TO_SIGNED = [to_signed_char(x) for x in COMPARE_TO]
# => [9, 13, -1, 35, 21, -1, 29, -41 ... wait let me recheck]
# 0xFF as signed char = -1, 0xD7 as signed char = -41
# So: [9, 13, -1, 35, 21, -1, 29, -41]


def check_characters(uc: int, pc: int, idx: int) -> bool:
    """
    Reconstructed algorithm from the crackme's PasswordCheck routine.
    uc = username char (as signed int)
    pc = serial char (as signed int)
    idx = position index
    Returns True if the pair is valid for position idx.
    """
    # The buggy extended Euclidean algorithm as implemented in the crackme
    val1 = 0      # ebp_1c
    val2 = 1      # ebp_20
    prev_val1 = 1 # ebp_14
    prev_val2 = 0 # ebp_18
    a = uc        # ebp_4
    b = pc        # ebp_8

    while b != 0:
        rem = a % b   # ebp_24  (Python % is always non-negative for positive b, but b could be negative)
        div = int(a / b)  # ebp_28 (C integer division, truncate toward zero)
        # In C, integer division truncates toward zero
        # We replicate C behavior:
        if b != 0:
            # C-style truncated division
            div = int(a / b)  # already truncated
            rem = a - div * b

        a = b
        b = rem

        new_val1 = prev_val1 - val1 * div   # ebp_2c
        # BUG in crackme: uses prev_val1 instead of prev_val2
        new_val2 = prev_val1 - val2 * div   # ebp_30

        prev_val1 = val1
        prev_val2 = val2

        val1 = new_val1
        val2 = new_val2

    expected = COMPARE_TO_SIGNED[idx % 8]
    return prev_val1 == expected


def gcd(a: int, b: int) -> int:
    while b != 0:
        a, b = b, a % b
    return a


def ext_euclidean_rec(a: int, b: int):
    """Returns (x, y) such that a*x + b*y = gcd(a,b), matching the C recursive helper."""
    if b == 0 or a % b == 0:
        return (0, 1)
    x, y = ext_euclidean_rec(b, a % b)
    return (y, x - y * (a // b))


def generate_serial_char(uc: int, expected: int) -> int:
    """
    Find a serial character c (0..254) such that:
      - extendedEuclideanRec(uc, c).first == expected
      - uc * x + c * y == gcd(uc, c)
      - c is alphanumeric: a-z, A-Z, 0-9
    Returns the character code, or raises ValueError if not found.
    """
    for c in range(1, 255):
        d = gcd(uc, c)
        x, y = ext_euclidean_rec(uc, c)
        if x == expected and uc * x + c * y == d:
            if (ord('a') <= c <= ord('z')) or (ord('A') <= c <= ord('Z')) or (ord('0') <= c <= ord('9')):
                return c
    raise ValueError(f"No valid serial char found for uc={uc}, expected={expected}")


def keygen(name: str) -> str:
    """
    Generate a serial for the given username.
    If no serial char can be found for a username character, the username character
    is shifted upward (as in the original keygen) until a match is found.
    Returns (possibly modified username, serial) but here we just return serial.
    Note: The modified username is also printed as a side effect.
    """
    serial_chars = []
    username_chars = list(name)

    for i in range(len(username_chars)):
        expected = COMPARE_TO_SIGNED[i % 8]
        shift = 0
        found = False
        while not found:
            uc = ord(username_chars[i]) + shift
            try:
                sc = generate_serial_char(uc, expected)
                # Modify username char if shifted
                username_chars[i] = chr(uc)
                serial_chars.append(chr(sc))
                found = True
            except ValueError:
                shift += 1
                if shift > 1000:
                    raise ValueError(f"Could not find valid pair for position {i}")

    modified_name = ''.join(username_chars)
    if modified_name != name:
        print(f"[Note: username modified to '{modified_name}' for valid serial generation]")
    return ''.join(serial_chars)


def verify(name: str, serial: str) -> bool:
    """
    Verify that a (name, serial) pair is valid.
    Both must be at least 4 characters long.
    Each character pair (name[i], serial[i]) is checked with check_characters.
    """
    if len(name) < 4 or len(serial) < 4:
        return False
    # Check up to the length of the shorter string
    # ASSUMPTION: the crackme checks each position up to the length of the username
    length = min(len(name), len(serial))
    if length < 4:
        return False
    for i in range(length):
        uc = ord(name[i])
        pc = ord(serial[i])
        if not check_characters(uc, pc, i):
            return False
    return True



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
