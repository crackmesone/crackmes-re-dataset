# Reconstructed algorithm from crackme writeup by [mdk] for VB6 crackme by mumbo_jumbo
# Serial 1: sum of ASCII values of all chars in name + 0x363
# Serial 2: ASCII value of first char squared (as integer)
# Serial 3: (sum of ASCII values of all chars) * 0x108D8 + 0x49923F52, taken as 32-bit signed integer

def _ascii_sum(name):
    return sum(ord(c) for c in name)

def compute_serial1(name):
    total = _ascii_sum(name)
    total += 0x363
    return total

def compute_serial2(name):
    if not name:
        return 0
    first_char_val = ord(name[0])
    # ASSUMPTION: 'first char is multiplied with itself' means first_char_val^2
    result = first_char_val * first_char_val
    return result

def compute_serial3(name):
    total = _ascii_sum(name)
    # ASSUMPTION: multiply sum by 0x108D8, add 0x49923F52, truncate to 32-bit signed
    result = total * 0x108D8 + 0x49923F52
    # Truncate to 32-bit
    result = result & 0xFFFFFFFF
    # Interpret as signed 32-bit
    if result >= 0x80000000:
        result -= 0x100000000
    return result

def verify(name, serial):
    """serial should be a string like 'S1-S2-S3' or a tuple/list of 3 serials.
    Based on the writeup, there are 3 separate serial input boxes.
    ASSUMPTION: serials are compared as decimal string representations of computed values.
    """
    if not name:
        return False
    if isinstance(serial, str):
        parts = serial.split('-')
    else:
        parts = list(serial)
    if len(parts) != 3:
        return False
    try:
        s1 = int(parts[0].strip())
        s2 = int(parts[1].strip())
        s3 = int(parts[2].strip())
    except (ValueError, IndexError):
        return False
    expected1 = compute_serial1(name)
    expected2 = compute_serial2(name)
    expected3 = compute_serial3(name)
    return s1 == expected1 and s2 == expected2 and s3 == expected3

def keygen(name):
    """Returns a serial string 'S1-S2-S3' for the given name."""
    if not name:
        return None
    s1 = compute_serial1(name)
    s2 = compute_serial2(name)
    s3 = compute_serial3(name)
    return f'{s1}-{s2}-{s3}'


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
