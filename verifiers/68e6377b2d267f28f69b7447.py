import math
import random
from typing import Optional

# Constants from binary analysis
INIT   = 0x12345678
TARGET = 0x683B236D
SALT   = 0x55555555
MOD    = 1 << 32
A      = 0x83
AINV   = pow(A, -1, MOD)  # modular inverse of 0x83 mod 2^32

CHARSET = b"abcdefghijklmnopqrstuvwxyz0123456789-?><_"


def _roll_hash(s: bytes) -> int:
    """Rolling hash: H = ((H * 0x83) + b) ^ 0x55555555, starting at 0x12345678"""
    H = INIT
    for b in s:
        H = ((H * A) + b) & 0xFFFFFFFF
        H ^= SALT
    return H


def _check_length(s: str) -> bool:
    """Length must be: 6 <= len <= 49, odd, and len % 3 == 0"""
    n = len(s)
    if n < 6 or n > 49:
        return False
    if (n & 1) == 0:       # even -> reject
        return False
    if (n % 3) == 1:       # len%3 == 1 -> reject (only 0 or 2 allowed, but combined with odd...)
        return False
    return True


def verify(name: str, serial: str) -> bool:
    """
    Validate a serial key.
    The name parameter is not used in the check (key-only crackme).
    """
    s = serial
    if not s:
        return False
    # Length checks
    if not _check_length(s):
        return False
    # Prefix check
    if len(s) < 2 or s[0] != 'K' or s[1] != 'e':
        return False
    # Rolling hash check
    return _roll_hash(s.encode('latin-1')) == TARGET


def _step_fwd(H: int, b: int) -> int:
    H = ((H * A) + b) & 0xFFFFFFFF
    return H ^ SALT


def _step_bwd(H_after: int, b: int) -> int:
    X = H_after ^ SALT
    return (((X - b) & 0xFFFFFFFF) * AINV) & 0xFFFFFFFF


def _index_to_digits(idx: int, base: int, length: int):
    d = []
    for _ in range(length):
        d.append(idx % base)
        idx //= base
    return d


def _valid_length(n: int) -> bool:
    """Check if length n satisfies all constraints."""
    if n < 6 or n > 49:
        return False
    if (n & 1) == 0:
        return False
    if (n % 3) == 1:
        return False
    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial key using meet-in-the-middle on a length-9 key
    with prefix 'Ke'. Uses modular inverse for backward step.
    The name parameter is ignored (key-only crackme).
    """
    # length=9: odd, 9%3=0, 9>=6 -> valid
    PREFIX = b"Ke"
    LENGTH = 9
    SPLIT_K = 3  # forward chunk size after prefix
    # tail2_len = LENGTH - len(PREFIX) - SPLIT_K = 9 - 2 - 3 = 4
    TAIL2_LEN = LENGTH - len(PREFIX) - SPLIT_K

    base = len(CHARSET)
    H0 = _roll_hash(PREFIX)  # hash state after processing 'Ke'

    rng = random.Random()
    rng.seed()

    total_fwd = base ** SPLIT_K
    total_bwd = base ** TAIL2_LEN

    # Build forward table: H after PREFIX + 3 chars -> those 3 chars
    fwd = {}
    order_fwd = list(range(total_fwd))
    rng.shuffle(order_fwd)
    for idx in order_fwd:
        digits = _index_to_digits(idx, base, SPLIT_K)
        H = H0
        chunk = bytearray()
        for d in digits:
            b = CHARSET[d]
            chunk.append(b)
            H = _step_fwd(H, b)
        if H not in fwd:
            fwd[H] = bytes(chunk)

    # Search backward from TARGET through 4 chars
    order_bwd = list(range(total_bwd))
    rng.shuffle(order_bwd)
    for idx in order_bwd:
        digits = _index_to_digits(idx, base, TAIL2_LEN)
        H = TARGET
        tail2 = bytearray()
        valid = True
        for d in digits:
            b = CHARSET[d]
            tail2.append(b)
            H = _step_bwd(H, b)
        # tail2 was built in reverse order of application, so reverse it
        tail2 = bytes(reversed(tail2))
        # H is now the state we need after processing PREFIX + fwd_chunk
        if H in fwd:
            key = PREFIX + fwd[H] + tail2
            key_str = key.decode('latin-1')
            # Double-check
            if verify(name, key_str):
                return key_str

    # ASSUMPTION: fallback brute-force for length 9 if MITM failed (shouldn't happen)
    # Try a few known-good lengths with brute force
    for attempt in range(100000):
        chars = [rng.choice(CHARSET) for _ in range(7)]
        candidate = b"Ke" + bytes(chars)
        if _roll_hash(candidate) == TARGET:
            return candidate.decode('latin-1')

    raise RuntimeError("keygen failed to find a valid key")



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
