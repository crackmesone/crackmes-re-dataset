import datetime
import math

def _solve_quadratic():
    # Solve 54x^2 - 702x + 2160 = 0
    # Simplifies to x^2 - 13x + 40 = 0
    # x = (13 +/- sqrt(169 - 160)) / 2 = (13 +/- 3) / 2
    # Solutions: x = 5 and x = 8
    a, b, c = 54, -702, 2160
    discriminant = b * b - 4 * a * c  # 9
    sqrt_disc = int(math.isqrt(discriminant))
    x1 = (-b + sqrt_disc) // (2 * a)  # 8
    x2 = (-b - sqrt_disc) // (2 * a)  # 5
    return x1, x2

def _check_formula(x):
    return math.pow(float(x), 2.0) * 54.0 - float(702 * x) + 2160.0

def verify(name, serial):
    # name is not used in the validation algorithm
    text = serial
    # Check length: (len + 1) / 10 == 2  => len must be 19
    if (len(text) + 1) // 10 != 2:
        return False
    # Positions 4, 9, 14 (0-indexed) must all be '-'
    if text[4] != '-' or text[9] != '-' or text[14] != '-':
        return False
    # Split by '-'
    parts = text.split('-')
    if len(parts) != 4:
        return False
    # Each part must be 4 characters
    if any(len(p) != 4 for p in parts):
        return False
    # parts[0] must be 'TC2N'
    if parts[0] != 'TC2N':
        return False
    # parts[3] must be 'RTCR'
    if parts[3] != 'RTCR':
        return False
    now = datetime.datetime.now()
    year_2digit = str(now.year)[2:4]   # last 2 digits of year
    day_2digit = now.strftime('%d')    # day zero-padded
    # parts[1][0:2] must equal last 2 digits of current year
    if parts[1][0:2] != year_2digit:
        return False
    # parts[2][0:2] must equal current day (zero-padded)
    if parts[2][0:2] != day_2digit:
        return False
    # Parse the remaining 2 chars of parts[1] and parts[2]
    try:
        result1 = int(parts[1][2:4])
    except ValueError:
        result1 = 0
    try:
        result2 = int(parts[2][2:4])
    except ValueError:
        result2 = 0
    num1 = math.pow(float(result1), 2.0) * 54.0 - float(702 * result1) + 2160.0
    num2 = math.pow(float(result2), 2.0) * 54.0 - float(702 * result2) + 2160.0
    # result1 != result2 AND both equations equal 0
    if result1 != result2 and num1 == 0.0 and num2 == 0.0:
        return True
    return False

def keygen(name):
    # name is not used
    # Solutions of 54x^2 - 702x + 2160 = 0 are x=5 and x=8
    x1, x2 = _solve_quadratic()  # x1=8, x2=5
    now = datetime.datetime.now()
    year_2digit = str(now.year)[2:4]
    day_2digit = now.strftime('%d')
    serial1 = 'TC2N-{}{:02d}-{}{:02d}-RTCR'.format(year_2digit, x1, day_2digit, x2)
    serial2 = 'TC2N-{}{:02d}-{}{:02d}-RTCR'.format(year_2digit, x2, day_2digit, x1)
    return serial1  # returns one valid serial; serial2 is also valid


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
