import struct
import ctypes

# ============================================================
# GrannysQuest Keygen / Verifier
# Based on two independent writeups (Kanker1337Off + ap3x)
# ============================================================

# ------ Helpers ------

def fib(n):
    """Standard 0-indexed Fibonacci: fib(0)=0, fib(1)=1"""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def rol32(value, shift):
    """Rotate left 32-bit"""
    shift &= 31
    value &= 0xFFFFFFFF
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF

def ror32(value, shift):
    """Rotate right 32-bit"""
    shift &= 31
    value &= 0xFFFFFFFF
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF

# ============================================================
# DAY 1: Granny's Birthday (ddmmyyyy)
# ============================================================
# Validation:
#   1. Input must be exactly 8 digit characters.
#   2. ascii_sum = sum of ASCII codes of all 8 chars.
#   3. x = ascii_sum ^ 0x29A  (^ 666)
#   4. x = ROL32(x, 4)
#   5. x = x * 5
#   6. x must equal 62240
#
# Reverse:
#   62240 / 5 = 12448
#   ROR32(12448, 4) = 778
#   778 ^ 666 = 400
#   400 = ascii_sum  ->  digit_sum = 400 - 8*48 = 16
#
# Any 8-digit string whose digit characters sum to 16 works.
# "00700900": 0+0+7+0+0+9+0+0 = 16  ✓

DAY1_FIXED = "00700900"

def verify_day1(birthday: str) -> bool:
    if len(birthday) != 8 or not birthday.isdigit():
        return False
    ascii_sum = sum(ord(c) for c in birthday)
    x = ascii_sum ^ 0x29A
    x = rol32(x, 4)
    x = (x * 5) & 0xFFFFFFFFFFFFFFFF  # keep as integer
    return x == 62240

def keygen_day1() -> str:
    """Return a valid 8-digit birthday string."""
    # digit sum = 16, e.g. '00700900'
    return DAY1_FIXED

# ============================================================
# DAY 2: Manufacturer (Atbash cipher)
# ============================================================
# Encoded string stored in binary: "Dlyyov#Dsvvoh#Fmornrgvw"
# Non-alpha chars map to '-'.
# Atbash:
#   lowercase c -> chr(ord('z') - ord(c) + ord('a'))  i.e. z-a mirror
#   uppercase C -> chr(ord('Z') - ord(C) + ord('A'))
#   other       -> '-'

ENCODED_MANUFACTURER = "Dlyyov#Dsvvoh#Fmornrgvw"

def atbash_decode(s: str) -> str:
    result = []
    for c in s:
        if 'a' <= c <= 'z':
            result.append(chr(ord('z') - ord(c) + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr(ord('Z') - ord(c) + ord('A')))
        else:
            result.append('-')
    return ''.join(result)

DAY2_ANSWER = atbash_decode(ENCODED_MANUFACTURER)  # "Wobble-Wheels-Unlimited"

def verify_day2(manufacturer: str) -> bool:
    expected = atbash_decode(ENCODED_MANUFACTURER)
    return manufacturer == expected

def keygen_day2() -> str:
    return DAY2_ANSWER

# ============================================================
# DAY 3: Fibonacci number code
# ============================================================
# For each letter in name (lowercased, up to 8 chars):
#   pos = ord(c) - ord('a')  (a=0 .. z=25)
#   concatenate str(fib(pos))
# Name must be <= 8 characters.

def verify_day3(name: str, code: str) -> bool:
    name = name.lower()[:8]
    expected = ''.join(str(fib(ord(c) - ord('a'))) for c in name)
    return code == expected

def keygen_day3(name: str) -> str:
    name = name.lower()[:8]
    return ''.join(str(fib(ord(c) - ord('a'))) for c in name)

# ============================================================
# DAY 4a: Launch Code  (format NNN-NNNNN-NNN)
# ============================================================
# Format: exactly "XXX-XXXXX-XXX"
# Each of the three numeric segments must have ASCII sum divisible by 7.
# "003-00005-003":
#   "003"   48+48+51=147  147%7=0
#   "00005" 48*4+53=245   245%7=0
#   "003"   same

DAY4_LAUNCH = "003-00005-003"

def _ascii_sum_div7(segment: str) -> bool:
    return sum(ord(c) for c in segment) % 7 == 0

def verify_day4_launch(code: str) -> bool:
    parts = code.split('-')
    if len(parts) != 3:
        return False
    if len(parts[0]) != 3 or len(parts[1]) != 5 or len(parts[2]) != 3:
        return False
    return all(_ascii_sum_div7(p) for p in parts)

def keygen_day4_launch() -> str:
    return DAY4_LAUNCH

# ============================================================
# DAY 4b: Coordinates
# ============================================================
# The compute_target_coordinate function is pure obfuscation;
# all trig/log operations cancel to zero.
# The returned constants are:
#   latitude  = 40.8214
#   longitude = 14.4262
# Format enforced: XX.XXXX,XX.XXXX (dot at index 2, comma at index 7, dot at index 10)

DAY4_COORDS = "40.8214,14.4262"

def verify_day4_coords(coords: str) -> bool:
    # Format check
    if len(coords) != 15:
        return False
    if coords[2] != '.' or coords[7] != ',' or coords[10] != '.':
        return False
    try:
        lat = float(coords[:7])
        lon = float(coords[8:])
    except ValueError:
        return False
    return abs(lat - 40.8214) < 1e-6 and abs(lon - 14.4262) < 1e-6

def keygen_day4_coords() -> str:
    return DAY4_COORDS

# ============================================================
# DAY 4c: Verification number
# ============================================================
# Formula (from dynamic analysis / breakpoint at RVA 0x3638):
#   v7 = 0x8000000000000000  (intermediate always equals this constant;
#        it is the XOR of the IEEE-754 bit patterns of 40.8214 and 14.4262
#        after going through the hash/normalization pipeline)
#   v8 = (0x309 * len(name)) ^ 0x8000000000000000
#   Result is interpreted as a signed 64-bit integer and printed as decimal.
#
# ASSUMPTION: The intermediate v7 is always 0x8000000000000000 regardless of
# launch code or coordinates, as confirmed by debugger read for "Kanker".

def _to_signed64(n: int) -> int:
    n &= 0xFFFFFFFFFFFFFFFF
    if n >= (1 << 63):
        n -= (1 << 64)
    return n

def verify_day4_verification(name: str, verif: str) -> bool:
    try:
        user_val = int(verif)
    except ValueError:
        return False
    expected = _to_signed64((0x309 * len(name)) ^ 0x8000000000000000)
    return user_val == expected

def keygen_day4_verification(name: str) -> str:
    v8 = _to_signed64((0x309 * len(name)) ^ 0x8000000000000000)
    return str(v8)

# ============================================================
# Unified verify / keygen
# ============================================================
# The crackme has four separate puzzles; 'serial' is interpreted as a
# pipe-separated string:  birthday|manufacturer|code|launch|coords|verif
# For Day 3+4 the name is required.

def verify(name: str, serial: str) -> bool:
    """
    serial format (pipe-separated):
        birthday|manufacturer|fib_code|launch_code|coordinates|verification
    name must be <= 8 characters.
    """
    parts = serial.split('|')
    if len(parts) != 6:
        return False
    birthday, manufacturer, fib_code, launch_code, coords, verif = parts
    name = name[:8]
    return (
        verify_day1(birthday) and
        verify_day2(manufacturer) and
        verify_day3(name, fib_code) and
        verify_day4_launch(launch_code) and
        verify_day4_coords(coords) and
        verify_day4_verification(name, verif)
    )

def keygen(name: str) -> str:
    """
    Generate a full serial for the given name.
    Name must be 1-8 alphabetic characters.
    """
    name = name[:8]
    parts = [
        keygen_day1(),
        keygen_day2(),
        keygen_day3(name),
        keygen_day4_launch(),
        keygen_day4_coords(),
        keygen_day4_verification(name),
    ]
    return '|'.join(parts)

# ============================================================
# CLI
# ============================================================

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
