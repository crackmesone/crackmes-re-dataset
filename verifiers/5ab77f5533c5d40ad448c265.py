import math

def char_sum(name: str) -> int:
    return sum(ord(c) for c in name)

def rndint(x: float) -> int:
    """FPU frndint equivalent: round half to even (banker's rounding)"""
    import decimal
    d = decimal.Decimal(str(x)).to_integral_value(rounding=decimal.ROUND_HALF_EVEN)
    return int(d)

# The fixed password string (second text box)
# Either '125()42()6' or '125()00()6' are valid; keygen uses '125()42()6'
FIXED_PASSWORD = "125()42()6"

def keygen(name: str):
    """
    Returns (password, serial1, serial2) tuple.
    - password is fixed: '125()42()6'
    - serial1 = floor(atan(charsum) * 1000)  [using FPU rndint]
    - serial2 = (charsum + 0x2007) XOR 4
    """
    cs = char_sum(name)
    serial1 = rndint(math.atan(cs) * 1000)
    serial2 = (cs + 0x2007) ^ 4
    return (FIXED_PASSWORD, str(serial1), str(serial2))

def verify(name: str, serial_tuple) -> bool:
    """
    serial_tuple = (password, serial1_str, serial2_str)
    
    password (2nd box): must be '125()42()6' or '125()00()6'
      - exactly 10 chars
      - char[3] == '(' (ASCII 40), char[4] + char[3] == 0x51 => char[4] == ')'
      - char[7] == '(' (ASCII 40), char[8] + char[7] == 0x51 => char[8] == ')'
      - first 3 digits form number 125 (log5(125) = 3, passes the FPU check)
      - digits at positions 5,6 satisfy A^B == B^A and A^2 == B^4
        => (4,2) or (0,0) -- i.e. '42' or '00'
      - char[9] == '6' (passes sqrt(1+cos(pi/6))+sqrt(1-cos(pi/6)) == sqrt(3))
    serial1 (3rd box): int(floor(atan(charsum)*1000))
    serial2 (4th box): (charsum + 0x2007) XOR 4
    """
    if isinstance(serial_tuple, str):
        # If only one string provided, can't verify all boxes
        return False
    password, serial1_str, serial2_str = serial_tuple

    # --- Verify password (2nd box) ---
    pwd = password
    if len(pwd) != 10:
        return False
    # char[9] must not be '0'
    if pwd[9] == '0':
        return False
    # Collect digits from password (chars between '0' and '@' exclusive, i.e. '0'..'9')
    digits = []
    for ch in pwd:
        if '0' <= ch < '@':
            digits.append(ord(ch) - ord('0'))

    # char[3] must satisfy 2*x^2 - 8*x - 0xB40 == 0 => x == 40 => '('
    x3 = ord(pwd[3])
    if 2 * x3 * x3 - 8 * x3 - 0xB40 != 0:
        return False
    # char[3] + char[4] == 0x51
    if ord(pwd[3]) + ord(pwd[4]) != 0x51:
        return False
    # Same for char[7]
    x7 = ord(pwd[7])
    if 2 * x7 * x7 - 8 * x7 - 0xB40 != 0:
        return False
    if ord(pwd[7]) + ord(pwd[8]) != 0x51:
        return False

    # First 3 digits form number X; check log5(X) == 3 => X == 125
    if len(digits) < 3:
        return False
    X = digits[0] * 100 + digits[1] * 10 + digits[2]
    if X != 125:
        return False

    # Digits 3 and 4 (A and B): A^B == B^A and A^2 == B^4
    # Valid: (4,2) or (0,0)
    if len(digits) < 5:
        return False
    A, B = digits[3], digits[4]
    def safe_pow(base, exp):
        if base == 0 and exp == 0:
            return 1  # ASSUMPTION: 0^0 = 1 for this check
        if exp == 0:
            return 1
        result = 1
        for _ in range(exp):
            result *= base
        return result
    if safe_pow(A, B) != safe_pow(B, A):
        return False
    if A * A != B * B * B * B:
        return False

    # Digit 5 (W): sqrt(1+cos(pi/W)) + sqrt(1-cos(pi/W)) == sqrt(3)
    # => W == 6
    if len(digits) < 6:
        return False
    W = digits[5]
    if W == 0:
        return False
    val = math.sqrt(1 + math.cos(math.pi / W)) + math.sqrt(1 - math.cos(math.pi / W))
    if abs(val - math.sqrt(3)) > 0.001:
        return False

    # --- Verify serial1 and serial2 (3rd and 4th boxes) ---
    try:
        s1 = int(serial1_str)
        s2 = int(serial2_str)
    except (ValueError, TypeError):
        return False

    cs = char_sum(name)
    expected_s1 = rndint(math.atan(cs) * 1000)
    expected_s2 = (cs + 0x2007) ^ 4

    if s1 != expected_s1:
        return False
    if s2 != expected_s2:
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
