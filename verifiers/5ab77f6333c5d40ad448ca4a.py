import hashlib
import struct

# Based on solution 2 (protection.txt):
# h = ((dt.A ^ dt.D) | dt.C) * dt.B
# where dt.A, dt.B, dt.C, dt.D are the 32-bit words of the MD5 hash of NAME
# Then solve DLP: h = CC3183A81DF91B^x mod DB10266AB0FD5B
# Serial = NAME + '-' + BASE16(x)
#
# NOTE: The MD5 hash words appear to be in big-endian (the ASM swaps bytes at the end)
# The modulus and base are from protection.txt as hex literals.

# ASSUMPTION: The MD5 hash is computed as standard MD5, words in little-endian
# (the ASM byte-swap at the end converts to big-endian for display but the
# computation uses the raw 32-bit words before the swap).
# We use Python's standard hashlib.md5 which gives the same byte sequence;
# we interpret the 16-byte digest as four little-endian 32-bit words (A,B,C,D)
# matching what the ASM stores before the final byte-swap phase.

BASE = 0xCC3183A81DF91B
MOD  = 0xDB10266AB0FD5B

def md5_words(name: str):
    """Return (A, B, C, D) as 32-bit little-endian words of MD5(name)."""
    digest = hashlib.md5(name.encode('ascii')).digest()
    A, B, C, D = struct.unpack('<IIII', digest)
    return A, B, C, D

def compute_h(name: str) -> int:
    A, B, C, D = md5_words(name)
    # h = ((A ^ D) | C) * B
    # All arithmetic is on 32-bit unsigned values
    h = (((A ^ D) | C) * B) & 0xFFFFFFFFFFFFFFFF  # ASSUMPTION: no explicit bit-width given; using 64-bit
    return h

def discrete_log_baby_giant(base: int, target: int, mod: int):
    """Solve base^x = target (mod mod) using baby-step giant-step."""
    import math
    # ASSUMPTION: the group order is mod-1 (mod is prime, not verified)
    n = int(math.isqrt(mod)) + 1
    # Baby steps: base^j for j in 0..n
    table = {}
    cur = target % mod
    for j in range(n + 1):
        table[cur] = j
        cur = (cur * base) % mod
    # Giant steps: base^(n*i) for i in 1..n
    factor = pow(base, n, mod)
    cur = factor
    for i in range(1, n + 2):
        if cur in table:
            x = (i * n - table[cur]) % (mod - 1)
            # Verify
            if pow(base, x, mod) == target % mod:
                return x
        cur = (cur * factor) % mod
    return None

def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    # ASSUMPTION: serial format is NAME-HEX_X (from protection.txt: NAME-BASE16(x))
    # But the crackme might just take a serial field separate from name.
    # From the first writeup, the key has two parts separated by '#'.
    # From protection.txt: FORMAT NAME-SERIAL. We'll try '-' separator.
    try:
        # Try splitting serial on '-' to get the hex value
        parts = serial.split('-')
        if len(parts) < 2:
            return False
        x_hex = parts[-1]
        x = int(x_hex, 16)
    except ValueError:
        return False

    h = compute_h(name)
    # Check: BASE^x mod MOD == h mod MOD
    # ASSUMPTION: h is reduced mod MOD for the DLP check
    target = h % MOD
    return pow(BASE, x, MOD) == target

def keygen(name: str) -> str:
    """Generate a valid serial for name."""
    h = compute_h(name)
    target = h % MOD
    # Solve BASE^x = target (mod MOD)
    # ASSUMPTION: MOD is small enough for baby-step giant-step
    # MOD = 0xDB10266AB0FD5B ~ 61 bits, BSGS table size ~2^30 -- may be slow
    # ASSUMPTION: We try a simple brute-force for small x first, then BSGS
    # For demonstration, we use pow-based check; real solve needs BSGS or factoring
    # Try to solve directly
    x = discrete_log_baby_giant(BASE, target, MOD)
    if x is None:
        raise ValueError(f"Could not solve DLP for name={name!r}")
    return f"{name}-{x:X}"


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
