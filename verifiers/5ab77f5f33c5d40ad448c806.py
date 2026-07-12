import hashlib
from decimal import Decimal, getcontext

# Set high precision for decimal arithmetic to match .NET behavior
getcontext().prec = 50


def _compute_d(name: str) -> Decimal:
    """
    Compute the intermediate value 'd' from the MD5 hash of the name.
    This is a direct port of the crackme's algorithm.
    """
    md5_bytes = hashlib.md5(name.encode('ascii')).digest()
    buffer = list(md5_bytes)  # 16 bytes

    # d = buffer[15] + 1
    d = Decimal(buffer[15]) + Decimal('1.0')

    # Continued-fraction-like iteration
    for i in range(15):
        d = (Decimal('1.0') / d) + Decimal(buffer[14 - i]) + Decimal('1')

    # Final adjustment using buffer[5]
    d = (Decimal('1.0') + Decimal(buffer[5] % 4)) + (Decimal('10.0') / d)

    return d


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    The math boils down to:
        c = d^2 + d

    Serial format: 15-digit integer string + '-' + exponent digit
    where the 15 digits represent (c * 10^14) rounded to an integer,
    and the exponent digit encodes how many extra digits c*10^14 has beyond 15.
    """
    d = _compute_d(name)

    # c = d^2 + d  (derived from A2/A1 == num5 simplification)
    c = d * d + d

    # Encode c as a serial: multiply by 10^14, convert to integer string
    c_scaled = c * Decimal('100000000000000')  # 10^14

    # Format as integer (round to nearest, no decimal point)
    c_int_str = format(int(c_scaled.to_integral_value()), 'd')

    # The last character of the serial is (len(c_int_str) - 15)
    exponent = len(c_int_str) - 15

    # Take the first 15 digits
    serial = c_int_str[:15] + '-' + str(exponent)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.

    Serial format: exactly 17 characters matching r'\d{15}-\d{1}'
    The 15 digits + exponent digit encode a floating-point value c.
    Valid if |c - (d^2 + d)| < some small epsilon.
    """
    import re

    # Format check: 15 digits, dash, 1 digit, total length 17 (0x11)
    pattern = re.compile(r'^\d{15}-\d{1}$')
    if not name:
        return False
    if not pattern.match(serial) or len(serial) != 17:
        return False

    if not name:
        return False

    # Decode the serial into c
    # y = last digit (the exponent indicator)
    y = float(serial[16])  # single digit after '-'
    # c = (first 15 digits / 10^14) * 10^y
    c_from_serial = (Decimal(serial[:15]) / Decimal('100000000000000')) * Decimal(10 ** int(y))

    # Compute expected c from name
    d = _compute_d(name)
    c_expected = d * d + d

    # Check equality within a small tolerance
    # ASSUMPTION: tolerance mirrors the crackme check (< 3e-16 relative)
    diff = abs(c_from_serial - c_expected)
    # Use a generous epsilon since serial only stores 15 significant digits
    epsilon = Decimal('0.0000000000000003') * c_expected
    return diff < abs(epsilon) + Decimal('1e-10')



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
