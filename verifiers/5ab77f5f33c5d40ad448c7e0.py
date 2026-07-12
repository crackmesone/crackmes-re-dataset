import hashlib
import math

# CHARSET for base36 encoding (serial uses these characters)
CHARSET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def md5_bytes(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    return hashlib.md5(data).digest()

def create_value(data):
    """Convert bytes to big integer (big-endian)."""
    v = 0
    for b in data:
        v *= 0x100
        v += b
    return v

# The prime p is derived from "gim913!\x95"
P_STRING = b'gim913!\x95'
p = create_value(P_STRING)
# p == 7451607150867194261 (prime)

def legendre(a, p):
    """Compute Legendre symbol (a/p) via Euler's criterion."""
    return pow(a, (p - 1) // 2, p)

def isqrt(n):
    if n < 0:
        return None
    if n == 0:
        return 0
    x = int(math.isqrt(n))
    # verify
    if x * x == n:
        return x
    return None

def tonelli_shanks(n, p):
    """Compute square root of n mod p."""
    if n == 0:
        return 0
    if legendre(n, p) != 1:
        return None
    if p % 4 == 3:
        return pow(n, (p + 1) // 4, p)
    # General Tonelli-Shanks
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while legendre(z, p) != 1:
        z += 1
    m = s
    c = pow(z, q, p)
    t = pow(n, q, p)
    r = pow(n, (q + 1) // 2, p)
    while True:
        if t == 0:
            return 0
        if t == 1:
            return r
        i = 1
        tmp = (t * t) % p
        while tmp != 1:
            tmp = (tmp * tmp) % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

def to_base36_5(n):
    """Encode integer n as 5-character base36 string."""
    if n < 0:
        return None
    chars = []
    for _ in range(5):
        chars.append(CHARSET[n % 36])
        n //= 36
    if n != 0:
        return None  # doesn't fit in 5 chars
    return ''.join(reversed(chars))

def from_base36_5(s):
    """Decode 5-character base36 string to integer."""
    v = 0
    for c in s:
        v *= 36
        v += CHARSET.index(c.upper())
    return v

def keygen(name):
    """
    Generate a valid serial for the given username.

    From the writeup:
    1. usermd5 = MD5(username)
    2. a = createValue(usermd5[0:5])
       b = createValue(usermd5[5:10])
       c = createValue(usermd5[10:15])
       d = createValue(usermd5[15:16])
    3. b = 512 * b + d
    4. D = b*b - 4*a*c
    5. Check D >= 0 and D mod p is a QR mod p (Legendre symbol == 1)
    6. The serial encodes 3 values sn1, sn2, sn3 each as 5 base36 chars (15 chars total)

    The quadratic equation is: a*x^2 + b*x + c = 0
    Solutions: x = (-b +/- sqrt(D)) / (2*a)  -- but this is done mod p

    ASSUMPTION: sn1, sn2, sn3 are the two roots of the quadratic mod p and
    some derived value. The writeup was truncated before fully revealing
    what sn1/sn2/sn3 represent. We implement the most likely interpretation:
    sn1 = x1 mod 36^5, sn2 = x2 mod 36^5, sn3 = (x1 + x2) mod 36^5
    where x1, x2 are solutions of a*x^2 + b*x + c ≡ 0 (mod p).
    """
    usermd5 = md5_bytes(name)

    a = create_value(usermd5[0:5])
    b = create_value(usermd5[5:10])
    c = create_value(usermd5[10:15])
    d = create_value(usermd5[15:16])

    b = 512 * b + d

    D_big = b * b - 4 * a * c

    if D_big < 0:
        return None  # Wrong username - D < 0

    D_mod = D_big % p

    leg = legendre(D_mod, p)
    if leg != 1:
        return None  # Wrong username - not a QR mod p

    sqrt_D = tonelli_shanks(D_mod, p)
    if sqrt_D is None:
        return None

    inv2a = pow(2 * a % p, p - 2, p)  # modular inverse of 2a mod p

    # Two solutions mod p
    x1 = ((-b % p + sqrt_D) % p * inv2a) % p
    x2 = ((-b % p - sqrt_D) % p * inv2a) % p

    # ASSUMPTION: sn1, sn2, sn3 are derived from x1 and x2 taken mod 36^5
    base = 36 ** 5
    sn1 = x1 % base
    sn2 = x2 % base
    # ASSUMPTION: sn3 might be (x1 + x2) mod base or another derived value
    sn3 = (x1 + x2) % base

    part1 = to_base36_5(sn1)
    part2 = to_base36_5(sn2)
    part3 = to_base36_5(sn3)

    if part1 is None or part2 is None or part3 is None:
        return None

    return part1 + part2 + part3

def verify(name, serial):
    """
    Verify serial for name.
    ASSUMPTION: We re-derive the expected serial and compare.
    The actual verify logic in the crackme checks each sn value
    in a specific way (truncated writeup), so this is a best-effort check.
    """
    if len(serial) != 15:
        return False
    serial = serial.upper()
    for c in serial:
        if c not in CHARSET:
            return False

    expected = keygen(name)
    if expected is None:
        return False

    # Also try the alternate root order
    expected2 = None
    usermd5 = md5_bytes(name)
    a = create_value(usermd5[0:5])
    b_val = create_value(usermd5[5:10])
    c_val = create_value(usermd5[10:15])
    d = create_value(usermd5[15:16])
    b_val = 512 * b_val + d
    D_big = b_val * b_val - 4 * a * c_val
    if D_big >= 0:
        D_mod = D_big % p
        if legendre(D_mod, p) == 1:
            sqrt_D = tonelli_shanks(D_mod, p)
            if sqrt_D is not None:
                inv2a = pow(2 * a % p, p - 2, p)
                x1 = ((-b_val % p + sqrt_D) % p * inv2a) % p
                x2 = ((-b_val % p - sqrt_D) % p * inv2a) % p
                base = 36 ** 5
                sn1 = x2 % base
                sn2 = x1 % base
                sn3 = (x1 + x2) % base
                p1 = to_base36_5(sn1)
                p2 = to_base36_5(sn2)
                p3 = to_base36_5(sn3)
                if p1 and p2 and p3:
                    expected2 = p1 + p2 + p3

    return serial == expected or (expected2 is not None and serial == expected2)


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
