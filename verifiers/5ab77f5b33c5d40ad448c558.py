import hashlib
import struct
import random
import string

# ---- Key 2 table (base64-like decode table, indexed by ASCII value) ----
# From key2_tbl.h: maps ASCII -> 6-bit value, 0xffffffff = invalid
key2_tbl = [0xffffffff] * 256
# '+' = 0x3e (ASCII 43)
key2_tbl[43] = 0x3e
# '/' = 0x3f (ASCII 47)
key2_tbl[47] = 0x3f
# '0'-'9' = 52-61
for i in range(10):
    key2_tbl[ord('0') + i] = 52 + i
# 'A'-'Z' = 0-25
for i in range(26):
    key2_tbl[ord('A') + i] = i
# 'a'-'z' = 26-51
for i in range(26):
    key2_tbl[ord('a') + i] = 26 + i

# ---- Key 2 seed / PRNG (Adler-32 variant) ----
def key2_seed(name):
    x = 1
    y = 0
    for ch in name:
        x = (ord(ch) + x) % 0xfff1
        y = (x + y) % 0xfff1
    seed = ((y << 16) + x) ^ 0x31373313
    return seed

def key2_ctx_init(name):
    """Initialize key2 context using C rand() seeded with key2seed.
    NOTE: C rand() is platform-specific. We approximate with Python random.
    """
    seed = key2_seed(name)
    # ASSUMPTION: C rand() behavior approximated; actual C rand may differ
    random.seed(seed & 0xffffffff)
    r0 = (random.randint(0, 0x7fff) | (random.randint(0, 0x7fff) << 15)) ^ 0x67452301
    r1 = (random.randint(0, 0x7fff) | (random.randint(0, 0x7fff) << 15)) ^ 0xefcdab89
    r2 = (random.randint(0, 0x7fff) | (random.randint(0, 0x7fff) << 15)) ^ 0x98badcfe
    r3 = (random.randint(0, 0x7fff) | (random.randint(0, 0x7fff) << 15)) ^ 0x103
    return {'seed': seed, 'r0': r0 & 0xffffffff, 'r1': r1 & 0xffffffff,
            'r2': r2 & 0xffffffff, 'r3': r3 & 0xffffffff}

# ---- Key 1: Name hash (SHA-256 based) ----
bigcool = b"bigcoolrobotyeaah"
frighten = b"frighteningoptic"
shake = b"shakezmonctrfdvyx"
ironcock = b"ironcock"

def make_name_hash_bytes(name):
    """Compute the name hash as described in the keygen.c make_name_hash."""
    name_bytes = name.encode() if isinstance(name, str) else name
    len0 = len(bigcool)
    len1 = len(frighten)
    # XOR name with bigcool, feed into SHA-256
    h = hashlib.sha256()
    for ix, ch in enumerate(name_bytes):
        t0 = ch ^ bigcool[ix % len0]
        h.update(bytes([t0]))
    sha_hash = h.digest()  # 32 bytes
    # XOR each byte with frighten, format as hex
    hash1 = ''
    for ix in range(32):
        t0 = frighten[ix % len1] ^ sha_hash[ix]
        hash1 += '%02X' % t0
    # Truncate to 63 hex chars (as in code: hash1[63] = 0)
    hash1 = hash1[:63]
    return hash1

def make_name_hash_int(name):
    hex_str = make_name_hash_bytes(name)
    return int(hex_str, 16)

# ---- Key 3 algorithm summary ----
# 1. Compute name hash (big integer from XOR+SHA256 as above)
# 2. Find next prime after several iterations based on (hash mod 31)
# 3. Compute modular inverse: xgcd(hash, next_prime)
# 4. Apply Lucas sequence + RSA-like powmod with private key
# Full key3 requires MIRACL big-number library and RSA private key
# RSA parameters from keygen.c:
pub_mod_hex = "E6B4F5A5C6BE26DFB96694BDE6BD31FA0CB3F87D2B477AA77B74A5B9541CE299"
pub_exp_hex = "10001"
prv_exp_hex = "2938E04394B55940D461CDE5F89A89992B4C7BE8529430114A3BC6895C59C8B9"
prv_p_hex = "E9526DEFF53B54FDC5EEDB5A68F00CBB"
prv_q_hex = "FD2175CF229F863725BCB0AE2B6C62BB"

def symm_mod_inverse(a, m):
    """Extended GCD to find modular inverse."""
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        return None
    return x % m

def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

def is_prime(n, k=20):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def next_prime(n):
    """Find next prime >= n."""
    if n < 2: return 2
    candidate = n if n % 2 != 0 else n + 1
    while not is_prime(candidate):
        candidate += 2
    return candidate

def make_key3_plain(name):
    """Compute plain key3 = modular inverse of name_hash mod next_prime."""
    name_hash = make_name_hash_int(name)
    # Compute reminder = name_hash mod 31
    reminder = name_hash % 31
    nx_prime = name_hash
    # The loop: while reminder-- > -1: nx_prime = next_prime(nx_prime)
    # This runs (reminder + 1) times (from reminder down to 0 inclusive)
    for _ in range(reminder + 1):
        nx_prime = next_prime(nx_prime)
    # plain_key3 = xgcd(name_hash, nx_prime) = modular inverse
    inv = symm_mod_inverse(name_hash, nx_prime)
    return name_hash, nx_prime, inv

def lucas_sequence(k, P, n):
    """Compute Lucas V_k(P, 1) mod n using doubling formulas."""
    # ASSUMPTION: Using standard Lucas V sequence with Q=1
    # V_0=2, V_1=P, V_{k+1} = P*V_k - V_{k-1}
    if k == 0:
        return 2 % n
    if k == 1:
        return P % n
    # Using fast doubling
    def lucas_double(Vm, Vm1, m):
        # V_{2m} = V_m^2 - 2*Q^m, with Q=1: V_{2m} = V_m^2 - 2
        # V_{2m+1} = V_m * V_{m+1} - Q^m * P, with Q=1: V_{2m+1} = V_m*V_{m+1} - P
        v2m = (Vm * Vm - 2) % n
        v2m1 = (Vm * Vm1 - P) % n
        return v2m, v2m1
    # Binary method
    bits = bin(k)[2:]
    vm, vm1 = 2 % n, P % n
    for bit in bits[1:]:
        vm, vm1 = lucas_double(vm, vm1, k)
        if bit == '1':
            vm, vm1 = vm1, (vm1 * P - vm) % n
    return vm

def make_key3(name):
    """Compute key3 using RSA private key operations.
    ASSUMPTION: Lucas sequence and powmod match MIRACL library behavior.
    """
    pub_mod = int(pub_mod_hex, 16)
    pub_exp = int(pub_exp_hex, 16)
    prv_exp = int(prv_exp_hex, 16)
    prv_p = int(prv_p_hex, 16)
    prv_q = int(prv_q_hex, 16)

    name_hash, nx_prime, plain_key = make_key3_plain(name)
    if plain_key is None:
        return None

    # compute lucas_exp = modular inverse of pub_exp mod (p^2-1)*(q^2-1)
    p_sq = prv_p * prv_p
    q_sq = prv_q * prv_q
    lucas_mod_val = (p_sq - 1) * (q_sq - 1)
    lucas_exp = symm_mod_inverse(pub_exp, lucas_mod_val)
    if lucas_exp is None:
        return None

    # v = lucas(plain_key, lucas_exp, pub_mod)  -- V_{lucas_exp}(plain_key, 1) mod pub_mod
    v = lucas_sequence(lucas_exp, plain_key, pub_mod)
    # w = powmod(v, prv_exp, pub_mod)
    w = pow(v, prv_exp, pub_mod)
    return w

def int_to_base64_miracl(n):
    """Convert integer to MIRACL-style base64 string."""
    # Standard base64 alphabet
    b64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    if n == 0:
        return 'A'
    result = ''
    while n > 0:
        result = b64chars[n % 64] + result
        n //= 64
    return result

# ---- Verification ----
def verify(name, serial):
    """
    ASSUMPTION: The serial is a base64-encoded key3 value.
    Full verification would require matching the MIRACL big-number library output.
    We check that the serial decodes to the expected key3 integer.
    """
    try:
        expected = make_key3(name)
        if expected is None:
            return False
        # Try to parse serial as base64 integer
        serial_int = 0
        for ch in serial.strip():
            val = key2_tbl[ord(ch)] if ord(ch) < 256 else 0xffffffff
            if val == 0xffffffff:
                return False
            serial_int = serial_int * 64 + val
        return serial_int == expected
    except Exception:
        return False

def keygen(name):
    """Generate key3 for given name."""
    key3_int = make_key3(name)
    if key3_int is None:
        return None
    return int_to_base64_miracl(key3_int)


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
