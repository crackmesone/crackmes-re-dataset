import math

def name_hash(name: str) -> int:
    """Hash function extracted from the crackme."""
    h = 0x29A
    for ch in name:
        c = ord(ch)
        s = c ^ 0xDADA
        s += h
        a = c ^ 0xBABE
        c ^= 0xF001
        a = ~a
        a = a + s * 4
        a >>= 3
        a += c
        h = a
    return h


def xgcd(a: int, b: int):
    """Extended Euclidean algorithm. Returns (gcd, s, t) such that a*s + b*t == gcd."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def mul_inv(a: int, m: int):
    """Multiplicative inverse of a mod m. Returns None if gcd(a,m) != 1."""
    g, s, _ = xgcd(a, m)
    if g != 1:
        return None
    return s % m


def verify(name: str, serial: str) -> bool:
    """
    Validate a name/serial pair.
    - serial must consist only of hex characters (0-9, A-F, a-f)
    - serial is interpreted as a hex integer
    - nhash = (hash(name) + 0x28F) % 0x1234
    - (nhash * serial_int) % 0x10001 == 1
    """
    # Check serial is a valid hex string
    serial_upper = serial.upper()
    if not serial_upper:
        return False
    for ch in serial_upper:
        if ch not in '0123456789ABCDEF':
            return False

    try:
        key = int(serial_upper, 16)
    except ValueError:
        return False

    nhash = (name_hash(name) + 0x28F) % 0x1234
    if nhash == 0:
        return False

    return (nhash * key) % 0x10001 == 1


def keygen(name: str) -> str:
    """
    Generate a valid serial (hex string, uppercase) for the given name.
    Returns None if nhash == 0 (no valid serial exists for that name).
    """
    nhash = (name_hash(name) + 0x28F) % 0x1234
    if nhash == 0:
        # ASSUMPTION: The crackme has a bug for names that hash to 0; no serial exists.
        return None

    # 0x10001 is prime, so multiplicative inverse always exists for nhash != 0
    key = mul_inv(nhash, 0x10001)
    if key is None:
        return None

    return hex(key)[2:].upper()



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
