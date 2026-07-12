import struct

# CRC-32 IEEE 802.3 table (poly 0xEDB88320)
def _make_crc_table():
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        table.append(crc)
    return table

_CRC_TABLE = _make_crc_table()

def crc32_custom(data: bytes) -> int:
    """CRC-32 as used by the crackme (same as standard CRC-32)."""
    crc = 0xFFFFFFFF
    for b in data:
        idx = (crc ^ b) & 0xFF
        crc = (crc >> 8) ^ _CRC_TABLE[idx]
    return (~crc) & 0xFFFFFFFF

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def next_prime(n: int) -> int:
    """Return the next prime strictly after n, stepping by 2."""
    # The C code does: do number+=2; while(!isprime(number));
    # It starts from an odd number (factor1 starts at 3)
    n += 2
    while not is_prime(n):
        n += 2
    return n

def get_primes(top: int):
    """
    Find two primes factor1, factor2 such that factor1 + factor2 == top.
    factor1 starts at 3 and increments through odd primes.
    Returns (factor1, factor2) or None if not found.
    """
    factor1 = 3
    while factor1 <= top // 2:
        candidate = top - factor1
        if candidate > 1 and is_prime(candidate):
            return (factor1, candidate)
        factor1 = next_prime(factor1)
    return None

def _compute_hash(substring: bytes) -> int:
    """Compute CRC32 of substring, subtract 0x13373, ensure even."""
    h = (crc32_custom(substring) - 0x13373) & 0xFFFFFFFF
    if h % 2 != 0:
        h = (h + 1) & 0xFFFFFFFF
    return h

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    Name must be at least 5 characters.
    Returns the serial string or raises ValueError.
    """
    if len(name) < 5:
        raise ValueError("Name length must be > 4")

    name_bytes = name.encode('latin-1')

    hash1 = _compute_hash(name_bytes[0:])
    hash2 = _compute_hash(name_bytes[1:])
    hash3 = _compute_hash(name_bytes[2:])
    hash4 = _compute_hash(name_bytes[3:])

    res1 = get_primes(hash1)
    res2 = get_primes(hash2)
    res3 = get_primes(hash3)
    res4 = get_primes(hash4)

    if res1 is None or res2 is None or res3 is None or res4 is None:
        raise ValueError("There are no possible serials for this name")

    r1, r5 = res1
    r2, r6 = res2
    r3, r7 = res3
    r4, r8 = res4

    return "{:X}-{:X}-{:X}-{:X}-{:X}-{:X}-{:X}-{:X}".format(r1, r2, r3, r4, r5, r6, r7, r8)

def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    The serial must be 8 hex values separated by '-'.
    """
    if len(name) < 5:
        return False

    parts = serial.strip().split('-')
    if len(parts) != 8:
        return False

    try:
        vals = [int(p, 16) for p in parts]
    except ValueError:
        return False

    r1, r2, r3, r4, r5, r6, r7, r8 = vals

    name_bytes = name.encode('latin-1')

    hash1 = _compute_hash(name_bytes[0:])
    hash2 = _compute_hash(name_bytes[1:])
    hash3 = _compute_hash(name_bytes[2:])
    hash4 = _compute_hash(name_bytes[3:])

    # Check: each pair (r_i, r_{i+4}) must be primes summing to hash_i
    def check_pair(top, fa, fb):
        if not is_prime(fa) or not is_prime(fb):
            return False
        if fa + fb != top:
            return False
        # fa must be <= top//2
        if fa > top // 2:
            return False
        return True

    return (
        check_pair(hash1, r1, r5) and
        check_pair(hash2, r2, r6) and
        check_pair(hash3, r3, r7) and
        check_pair(hash4, r4, r8)
    )


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
