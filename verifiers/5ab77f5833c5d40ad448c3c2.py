import random
import math

# Tables used to build the RegKey (each is 16 chars of digits)
rnd1 = '1234432132142134'
rnd2 = '1234564543212341'
rnd3 = '2221113337213424'

# ASSUMPTION: The crackme validates name length >= 5, then:
#   1) sums ASCII values of name chars -> name_sum
#   2) counts '1' bits in name_sum -> bin_count  (the 'SUM TO BINARY NUM' step)
#   3) generates a random RegKey of form 'XXX-XXX-XXX-B' (12 hex-ish chars + dashes + 'B')
#   4) computes rkrez from RegKey digits using weighted formula (RkeyVal)
#   5) computes: tmp1 = rkrez ^ bin_count  (via FPU: repeated multiply)
#   6) finds a prime serial via BruteSerial: remainder of 64-bit left-shift division
#   Both RegKey and serial are tied together; verifier checks serial matches key+name.

def sum_name(name):
    """Sum ASCII values of all name characters."""
    return sum(ord(c) for c in name)

def count_ones_in_binary(n):
    """Count number of 1-bits in n (the 'SUM TO BINARY NUM' step in the asm).
    The asm code starts bin=0, then for each remainder==1 during repeated idiv by 2, increments bin.
    This is equivalent to bin(n).count('1')."""
    return bin(n).count('1')

def rkey_val(rkey_segment, tosub, subval):
    """RkeyVal procedure:
    For each of 3 chars in segment:
      digit = char - ord('0')
      weight = tosub - subval
      rkrez += digit * weight
      subval += 1
    """
    rkrez = 0
    ebx = subval
    for i in range(3):
        al = ord(rkey_segment[i]) - 0x30
        edx = tosub - ebx
        rkrez += al * edx
        ebx += 1
    return rkrez

def generate_rkey():
    """Generate a random RegKey string of form 'XXX-XXX-XXX-B' (13 chars).
    Each group of 3 chars is picked from rnd1/rnd2/rnd3 tables using a random seed.
    ASSUMPTION: We use random to simulate GetTickCount, picking 3 chars per group."""
    tables = [rnd1, rnd2, rnd3]
    rkey = ''
    for t in range(3):
        tick = random.randint(0, 0xFFFFFFFF)
        val = (tick * 2) & 0xFFFFFFFF
        for _ in range(3):
            idx = val & 0x0F
            val >>= 4
            rkey += tables[t][idx]
        rkey += '-'
    rkey += 'B'
    return rkey

def compute_rkrez(rkey):
    """Compute rkrez from RegKey using RkeyVal x3.
    RkeyVal(Rkey, 11, 1)  -> chars [0..2]
    RkeyVal(Rkey+4, 12, 5) -> chars [4..6]
    RkeyVal(Rkey+8, 13, 9) -> chars [8..10]
    """
    rkrez = 0
    rkrez += rkey_val(rkey[0:3], 11, 1)
    rkrez += rkey_val(rkey[4:7], 12, 5)
    rkrez += rkey_val(rkey[8:11], 13, 9)
    return rkrez

def compute_tmp1(rkrez, bin_count):
    """Compute tmp1 = rkrez ^ bin_count via repeated FPU multiply.
    The asm uses a 80-bit extended float accumulator starting at 0,
    then for bin_count iterations: tmp1 = tmp1 * rkrez.
    But initial tmp1 is 0 which would always give 0.
    ASSUMPTION: The FPU tbyte initialized to 1.0 conceptually (identity for multiply),
    so tmp1 = rkrez ** bin_count, stored as 64-bit integer.
    Actually re-reading: tmp2=0x80000000, tmp3=0x3FFF -> this is an 80-bit extended 1.0.
    So tmp1 starts as 1.0, and each loop: tmp1 *= rkrez.
    Result: tmp1 = rkrez ** bin_count (as integer after fistp)."""
    # ASSUMPTION: initial value is 1.0 (80-bit extended float)
    result = float(1)
    for _ in range(bin_count):
        result *= rkrez
    return int(result) & 0xFFFFFFFFFFFFFFFF  # 64-bit

def brute_serial(tmp1_64):
    """BruteSerial: finds a value ebx such that (tmp1_64 mod ebx) is prime.
    The 64-bit division is done via 64-bit left-shift algorithm.
    Returns (remainder, ebx) where remainder is prime."""
    # ASSUMPTION: ebx starts at 0x3016+1=0x3017 and increments
    ebx = 0x3017
    while True:
        # 64-bit division: tmp1_64 / ebx -> quotient, remainder
        remainder = tmp1_64 % ebx
        # Check if remainder is prime (esi in asm)
        if remainder > 2 and is_prime(remainder):
            return remainder, ebx
        ebx += 1
        if ebx > 0xFFFFFFFF:
            break
    return None, None

def is_prime(n):
    """Simple primality test matching the asm ptest loop."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limit = (n - 1) // 2  # asm: ecx = esi/2 - 2 + 1 approx
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def keygen(name):
    """Generate a (regkey, serial) pair for the given name."""
    if len(name) < 5:
        raise ValueError('Name must be at least 5 characters')
    ns = sum_name(name)
    bc = count_ones_in_binary(ns)
    rkey = generate_rkey()
    rkrez = compute_rkrez(rkey)
    tmp1 = compute_tmp1(rkrez, bc)
    serial, _ = brute_serial(tmp1)
    return rkey, str(serial)

def verify(name, serial_str, rkey=None):
    """Verify a name/regkey/serial combination.
    ASSUMPTION: The verifier recomputes the same rkrez from the provided regkey,
    then checks that serial is the prime remainder found by BruteSerial.
    Since we don't have the original verifier binary disassembly fully,
    this is a reconstruction."""
    if len(name) < 5:
        return False
    try:
        serial = int(serial_str)
    except ValueError:
        return False
    if rkey is None:
        return False
    ns = sum_name(name)
    bc = count_ones_in_binary(ns)
    rkrez = compute_rkrez(rkey)
    tmp1 = compute_tmp1(rkrez, bc)
    found_serial, _ = brute_serial(tmp1)
    return found_serial == serial


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
