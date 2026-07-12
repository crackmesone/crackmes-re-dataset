import hashlib
import random

# Hardcoded constants from the crackme
N = 0xE97E36F9426708D10516A001FC358367B8ECBB7210388B971C886AA4A44845F1
P = 0xEB8D197C10BA775BA2A785085C44A0C3
Q = 0xFDC35FF9D4A7BBCAD7577E99D8C8533B
# C as given in mod-n form
C = 0xFC1E242B3E7FC09993FE14EC88B799ACFD68BC83115F2F85C3E94E7D0FEC3F3

def compute_u(name: str) -> int:
    """Compute U = bignum(first_ten_bytes(sha1(name + '&PEdiy'))) mod N"""
    # ASSUMPTION: the salt appended to the username is '&PEdiy' based on solution description
    data = (name + '&PEdiy').encode('latin-1')
    digest = hashlib.sha1(data).digest()
    # Take first 10 bytes as big-endian integer
    u = int.from_bytes(digest[:10], 'big')
    return u % N

def legendre(a, p):
    """Legendre symbol (a/p) via Euler's criterion"""
    ls = pow(a, (p - 1) // 2, p)
    if ls == p - 1:
        return -1
    return ls

def sqrt_mod_prime(a, p):
    """Find x such that x^2 = a (mod p) using Tonelli-Shanks.
    Returns None if no solution."""
    a = a % p
    if a == 0:
        return 0
    if legendre(a, p) != 1:
        return None
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)
    # Tonelli-Shanks
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while legendre(z, p) != -1:
        z += 1
    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)
    while True:
        if t == 1:
            return r
        i, temp = 1, pow(t, 2, p)
        while temp != 1:
            temp = pow(temp, 2, p)
            i += 1
        b = pow(c, pow(2, m - i - 1), p)
        m = i
        c = pow(b, 2, p)
        t = (t * c) % p
        r = (r * b) % p

def sqrt_mod_n(a, p, q):
    """Find square roots of a mod n=p*q using CRT. Returns list of solutions."""
    sp = sqrt_mod_prime(a, p)
    sq = sqrt_mod_prime(a, q)
    if sp is None or sq is None:
        return []
    n = p * q
    results = []
    for rp in [sp, p - sp]:
        for rq in [sq, q - sq]:
            # CRT: x = rp (mod p), x = rq (mod q)
            # x = rp + p * ((rq - rp) * inverse(p, q) % q)
            diff = (rq - rp) % q
            inv_p_q = pow(p, -1, q)
            x = (rp + p * (diff * inv_p_q % q)) % n
            results.append(x)
    return results

def verify(name: str, serial: str) -> bool:
    """Verify a serial of the form 'HEXA-HEXB' for a given name."""
    try:
        parts = serial.strip().split('-')
        if len(parts) != 2:
            return False
        part_a = int(parts[0], 16)
        part_b = int(parts[1], 16)
    except ValueError:
        return False

    u = compute_u(name)
    # Check: C * partB^2 + partA^2 = U (mod N)
    lhs = (C * pow(part_b, 2, N) + pow(part_a, 2, N)) % N
    return lhs == u

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    u = compute_u(name)
    # Strategy: choose random A (as bignum), solve B = (U - A^2) * inverse(C) mod N
    # then check if A and B are quadratic residues mod N.
    # If yes, compute square roots to get partA and partB.
    max_attempts = 10000
    for _ in range(max_attempts):
        # Choose random X, set A = X^2 mod N (guarantees A is a QR)
        x_rand = random.randint(2, N - 2)
        A = pow(x_rand, 2, N)
        # Solve B = (U - A) * C_inv mod N
        C_inv = pow(C, -1, N)
        B = ((u - A) * C_inv) % N
        # Check if B is a quadratic residue mod both P and Q
        if legendre(B % P, P) == 1 and legendre(B % Q, Q) == 1:
            # A is already a perfect square: sqrt is x_rand
            part_a = x_rand
            # Find sqrt of B mod N
            b_roots = sqrt_mod_n(B, P, Q)
            if b_roots:
                part_b = b_roots[0]
                serial = f"{part_a:X}-{part_b:X}"
                if verify(name, serial):
                    return serial
    raise ValueError("Could not generate a valid serial after many attempts")


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
