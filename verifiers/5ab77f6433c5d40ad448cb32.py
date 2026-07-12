import math

# Hardcoded table from crackme
TABLE = [0x25, 0x28, 0x29, 0x2c, 0x31, 0x36]


def mul_inv(a, b):
    """Modular inverse of a mod b (extended Euclidean algorithm)."""
    b0 = b
    x0, x1 = 0, 1
    if b == 1:
        return 1
    while a > 1:
        q = a // b
        a, b = b, a % b
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += b0
    return x1


def number_of_digits(i):
    if i <= 0:
        return 1
    return int(math.log10(i)) + 1


def _compute_key(name: str) -> int:
    n = len(name)
    if n < 2 or n > 5:
        raise ValueError("Name length must be between 2 and 5 letters inclusive")

    # Step 1: find minimum ASCII code in name
    min_char = min(ord(c) for c in name)

    # Step 2: subtract minimal value from 2
    min_val = 2 - min_char  # This is a signed byte difference (may be negative)
    # Note: treated as plain integer arithmetic matching C char behaviour

    # Step 3: compute remainders array a[] and moduli array p[]
    a = [0] * n
    p = [0] * n
    N = 1
    for i in range(n):
        a[i] = ord(name[i]) + min_val + i
        p[i] = (i % 10) + TABLE[i]
        N *= p[i]

    # Build array of inverses (Garner algorithm)
    r = [[0] * n for _ in range(n)]
    for i in range(1, n):
        for j in range(i):
            r[i][j] = mul_inv(p[j], p[i])

    # Garner algorithm to find x[]
    x = list(a)  # start with x[i] = a[i]
    for i in range(n):
        x[i] = a[i]
        for j in range(i):
            x[i] = r[i][j] * (x[i] - x[j])
            x[i] = x[i] % p[i]
            if x[i] < 0:
                x[i] += p[i]

    # Reconstruct key = x[0] + x[1]*p[0] + x[2]*p[0]*p[1] + ...
    key = x[0]
    for i in range(1, n):
        temp = 1
        for j in range(i):
            temp *= p[j]
        key += x[i] * temp

    # Key length must be between 8 and 10 digits
    while number_of_digits(key) < 8:
        key += N * 10

    return key


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    key = _compute_key(name)
    return str(key)


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial is valid for name.
    The check is: for every letter at position i,
        int(serial) % ((i % 10) + TABLE[i]) == a[i]
    where a[i] = ord(name[i]) + (2 - min_ascii) + i
    """
    n = len(name)
    if n < 2 or n > 5:
        return False

    try:
        key = int(serial)
    except ValueError:
        return False

    if number_of_digits(key) < 8 or number_of_digits(key) > 10:
        return False

    min_char = min(ord(c) for c in name)
    min_val = 2 - min_char

    for i in range(n):
        expected_remainder = (ord(name[i]) + min_val + i) & 0xFF  # keep as C char arithmetic
        # ASSUMPTION: the remainder comparison uses the raw integer value (may be negative in C)
        # We replicate using the plain integer as in the C source
        expected_remainder = ord(name[i]) + min_val + i
        modulus = (i % 10) + TABLE[i]
        if key % modulus != expected_remainder % modulus:
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
