# Reverse-engineered validation for crackme_2 by boba_fett
#
# Based on comments and ToMKoL's solution writeup.
#
# Stage 1 (serial1):
#   serial1 = sum of Unicode code points of all characters in name
#   (stored as a decimal integer string, e.g. 'T'=84,'o'=111,'M'=77,'K'=75,'o'=111,'L'=76 => 534)
#
# Stage 2 (serial2):
#   From the comment formula:
#     15 * decval(left(serial1,3)) - 18 == serial2 * decval(left(serial1,3))
#   Solving for serial2:
#     serial2 = (15 * S - 18) / S   where S = int(serial1[:3])
#     serial2 = 15 - 18/S
#
#   Additionally, the truncated ASM shows:
#     - val(name) is attempted as a numeric conversion (VarR8FromStr), defaulting to 0.0 if name is not numeric
#     - Then: (val(name) * 100 + 15 * S - 18) / S  ... but the truncation prevents full recovery.
#
# ASSUMPTION: Based on the example pair (Name='ToMKoL', Serial1='534', Serial2='14.9662922')
#   S = 534
#   serial2 = 15 - 18/534 = 15 - 0.033707... = 14.9662921... ≈ 14.9662922  (matches!)
#   val('ToMKoL') = 0 (non-numeric name), so val(name)*100 contributes 0.
#   Formula confirmed: serial2 = (15*S - 18) / S  when name is non-numeric.
#
# ASSUMPTION: When name IS numeric, val(name) is used:
#   serial2 = (val(name)*100 + 15*S - 18) / S
#   but this part is not fully confirmed from the truncated writeup.

def _sum_unicode(name: str) -> int:
    """Sum of Unicode code points of all characters in name."""
    return sum(ord(c) for c in name)

def _val_name(name: str) -> float:
    """VB-style Val(): parse leading numeric portion, 0.0 if not numeric."""
    # ASSUMPTION: mirrors VarR8FromStr behaviour - returns 0.0 for non-numeric strings
    import re
    m = re.match(r'^\s*[+-]?\d*\.?\d+', name)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return 0.0
    return 0.0

def keygen(name: str):
    """Generate (serial1, serial2) for a given name."""
    if not name:
        raise ValueError("Name must not be empty")
    S = _sum_unicode(name)
    serial1 = str(S)
    # Use first 3 digits of serial1 as the divisor
    s3_str = serial1[:3]
    try:
        s3 = int(s3_str)
    except ValueError:
        raise ValueError(f"serial1 '{serial1}' has fewer than 1 digit")
    if s3 == 0:
        raise ValueError("Cannot generate serial2: divisor S is 0")
    val_n = _val_name(name)  # ASSUMPTION: 0.0 for non-numeric names
    serial2 = (val_n * 100.0 + 15.0 * s3 - 18.0) / s3
    return serial1, serial2

def verify(name: str, serial: str) -> bool:
    """
    serial should be a string like '534,14.9662922' (serial1,serial2 comma-separated)
    or a tuple/list (serial1, serial2).
    """
    if not name:
        return False
    # Accept both comma-separated string and tuple
    if isinstance(serial, str):
        parts = serial.split(',')
        if len(parts) != 2:
            return False
        serial1_in = parts[0].strip()
        try:
            serial2_in = float(parts[1].strip())
        except ValueError:
            return False
    else:
        serial1_in, serial2_in = serial
        serial2_in = float(serial2_in)

    # Check serial1
    S = _sum_unicode(name)
    expected_serial1 = str(S)
    if serial1_in != expected_serial1:
        return False

    # Check serial2
    s3_str = expected_serial1[:3]
    try:
        s3 = int(s3_str)
    except ValueError:
        return False
    if s3 == 0:
        return False
    val_n = _val_name(name)
    expected_serial2 = (val_n * 100.0 + 15.0 * s3 - 18.0) / s3
    # Allow small floating-point tolerance
    return abs(serial2_in - expected_serial2) < 1e-4


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
