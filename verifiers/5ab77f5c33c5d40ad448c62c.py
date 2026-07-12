# Paillier cryptosystem-based keygen for crackme2_by_sx0r
# The write-up is a Delphi keygen using the Paillier cryptosystem.
# The specific parameters (p, q, g, n) used by the crackme are NOT provided in the truncated writeup.
# We can implement the Paillier encryption structure, but without the actual public key (n, g)
# we cannot produce valid serials.

import math
from sympy import mod_inverse

# ASSUMPTION: These are placeholder values. The actual p, q, g from the crackme are unknown
# because the writeup was truncated before revealing them.
# ASSUMPTION: The crackme uses a small Paillier instance.
P_STR = 'UNKNOWN'  # actual prime p from crackme
Q_STR = 'UNKNOWN'  # actual prime q from crackme
G_STR = 'UNKNOWN'  # actual g from crackme

# ASSUMPTION: min/max name length constraints from the source
MIN_NAME_LEN = 5
MAX_NAME_LEN = 35


def lcm(a, b):
    return a * b // math.gcd(a, b)


def L_func(u, n):
    """L(u) = (u - 1) // n"""
    return (u - 1) // n


def paillier_keygen(p, q, g):
    """Compute Paillier public and private keys."""
    n = p * q
    n2 = n * n
    lam = lcm(p - 1, q - 1)
    # mu = (L(g^lambda mod n^2))^-1 mod n
    g_lam = pow(g, lam, n2)
    L_val = L_func(g_lam, n)
    mu = mod_inverse(L_val, n)
    pub = (n, g)
    priv = (lam, mu)
    return pub, priv


def paillier_encrypt(m, n, g, r=None):
    """Encrypt message m with public key (n, g) using randomness r."""
    n2 = n * n
    if r is None:
        import random
        r = random.randint(1, n - 1)
        while math.gcd(r, n) != 1:
            r = random.randint(1, n - 1)
    # c = g^m * r^n mod n^2
    c = (pow(g, m, n2) * pow(r, n, n2)) % n2
    return c


def paillier_decrypt(c, lam, mu, n):
    """Decrypt ciphertext c with private key (lam, mu)."""
    n2 = n * n
    u = pow(c, lam, n2)
    l_val = L_func(u, n)
    m = (l_val * mu) % n
    return m


def name_to_number(name):
    """Convert name to a number for encryption.
    ASSUMPTION: The crackme lowercases the name and converts it to some integer.
    The exact encoding (e.g., sum of chars, concatenation of hex values, etc.) is unknown.
    We assume it converts the lowercased ASCII bytes to a big-endian integer.
    """
    name_lower = name.lower()
    val = int(name_lower.encode('ascii').hex(), 16)
    return val


def serial_to_string(ciphertext):
    """Convert ciphertext integer to serial string.
    ASSUMPTION: The keygen formats the ciphertext as a hex or decimal string.
    The exact format (grouping, separators, length) is unknown.
    """
    # ASSUMPTION: serial is the hex representation of the ciphertext
    return hex(ciphertext)[2:].upper()


def verify(name, serial):
    """Verify name/serial pair.
    ASSUMPTION: Without the actual public key parameters, this cannot be implemented.
    The crackme decrypts the serial using Paillier and checks it matches a function of the name.
    """
    if len(name) < MIN_NAME_LEN or len(name) > MAX_NAME_LEN:
        return False

    # ASSUMPTION: actual n and g must be known
    if P_STR == 'UNKNOWN':
        raise NotImplementedError(
            'Actual Paillier parameters (p, q, g) from crackme are not available in the writeup. '
            'Cannot verify without them.'
        )

    p = int(P_STR)
    q = int(Q_STR)
    g = int(G_STR)
    pub, priv = paillier_keygen(p, q, g)
    n, g_pub = pub
    lam, mu = priv

    # ASSUMPTION: serial is a hex-encoded ciphertext
    try:
        c = int(serial, 16)
    except ValueError:
        return False

    # Decrypt
    m = paillier_decrypt(c, lam, mu, n)

    # ASSUMPTION: compare decrypted value to the name-derived number
    expected = name_to_number(name)
    return m == expected


def keygen(name):
    """Generate serial for name.
    ASSUMPTION: actual p, q, g must be known.
    """
    if len(name) < MIN_NAME_LEN or len(name) > MAX_NAME_LEN:
        raise ValueError(f'Name must be between {MIN_NAME_LEN} and {MAX_NAME_LEN} characters.')

    if P_STR == 'UNKNOWN':
        raise NotImplementedError(
            'Actual Paillier parameters (p, q, g) from crackme are not available in the truncated writeup. '
            'Cannot generate serial without them.'
        )

    p = int(P_STR)
    q = int(Q_STR)
    g = int(G_STR)
    pub, priv = paillier_keygen(p, q, g)
    n, g_pub = pub

    m = name_to_number(name)
    c = paillier_encrypt(m, n, g_pub)
    return serial_to_string(c)



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
