# Reconstructed algorithm for advancrkme by d3ux
# Based on solution writeup analysis
#
# Key findings from writeup:
# 1. Serial has two halves: serial[1] (first half) and serial[2] (second half)
# 2. serial[1] must be a PRIME number (verified via Miller-Rabin test)
# 3. serial[1] must equal the ComputerID (a random prime tied to the machine)
# 4. Miller-Rabin test uses bases 2, 7, 0x3D (61)
# 5. The second half (serial[2]) is involved in an int64 power-mod computation
#    with constants 0xFB8D visible in the code
# 6. Serial values are processed as WORDs (16-bit), first half unchanged,
#    last word transformed via ROR/ROL
# 7. The check [400128] == 0x71EC0 verifies the binary is unpacked
#
# ASSUMPTION: The full serial format is a string of digits or hex representing
#             two 16-bit (WORD) values concatenated.
# ASSUMPTION: serial[1] = first WORD, serial[2] = second WORD (after ROR/ROL transform)
# ASSUMPTION: The int64 powmod uses modulus 0xFB8D (64397) based on const visible in code
# ASSUMPTION: The success condition for serial[2] is serial2_transformed^e mod 0xFB8D == some_target
#             but the exact exponent/target is not fully revealed in the truncated writeup.
# ASSUMPTION: ComputerID is machine-specific; we cannot reproduce it without running the binary.

import sympy

# Miller-Rabin with specific witnesses as used in the crackme
def miller_rabin_witnesses(n, witnesses=(2, 7, 61)):
    """Miller-Rabin primality test with specific witnesses."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # Write n-1 as 2^k * o
    o = n - 1
    k = 0
    while o % 2 == 0:
        o //= 2
        k += 1
    for p in witnesses:
        if p >= n:
            continue
        # Compute p^o mod n
        ebx = pow(p, o, n)
        if ebx == 1 or ebx == n - 1:
            continue
        passed = False
        for i in range(1, k):
            ebx = pow(ebx, 2, n)
            if ebx == n - 1:
                passed = True
                break
        if not passed:
            return False
    return True

def is_prime_crackme(n):
    """Check primality as the crackme does (Miller-Rabin with bases 2, 7, 61)."""
    return miller_rabin_witnesses(n, witnesses=(2, 7, 61))

# ASSUMPTION: The serial is formatted as two decimal numbers separated by '-'
# or as a combined string. We assume format "SERIAL1-SERIAL2"
# ASSUMPTION: serial1 is the raw WORD value (16-bit prime)
# ASSUMPTION: serial2 undergoes ROR/ROL transformation before use
# ASSUMPTION: The modulus for serial2 check is 0xFB8D = 64397
# ASSUMPTION: We cannot verify serial[1] == ComputerID without the actual machine ID

MOD2 = 0xFB8D  # constant seen in int64powmod routine

def rol16(val, count, bits=16):
    count = count % bits
    return ((val << count) | (val >> (bits - count))) & 0xFFFF

def ror16(val, count, bits=16):
    count = count % bits
    return ((val >> count) | (val << (bits - count))) & 0xFFFF

def transform_serial2(s2_raw):
    """Apply the ROR/ROL transformation described in the writeup.
    ASSUMPTION: exact rotation amount unknown, using 1 as placeholder."""
    # ASSUMPTION: rotation amount is 1 based on typical crackme patterns
    return ror16(s2_raw, 1)

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: 'name' is not directly used in validation (writeup focuses on ComputerID).
    ASSUMPTION: serial format is 'PART1-PART2' where each part is a decimal integer.
    """
    try:
        parts = serial.split('-')
        if len(parts) != 2:
            return False
        s1 = int(parts[0])
        s2 = int(parts[1])
    except ValueError:
        return False

    # Serial values must fit in 16-bit WORD
    if not (0 < s1 <= 0xFFFF) or not (0 < s2 <= 0xFFFF):
        return False

    # Check 1: serial[1] must be prime (Miller-Rabin with witnesses 2, 7, 61)
    if not is_prime_crackme(s1):
        return False

    # Check 2: serial[1] should equal ComputerID
    # ASSUMPTION: We cannot check this without the actual machine; skip or always pass
    # In a real scenario: if s1 != get_computer_id(): return False

    # Check 3: serial[2] transformation check
    # ASSUMPTION: After ROR transformation, s2_transformed^? mod MOD2 must equal some value
    # The writeup is truncated before revealing the exact condition
    # We mark this as a partial check
    s2_transformed = transform_serial2(s2)
    # ASSUMPTION: the condition may be s2_transformed^s1 mod MOD2 == 1 (like a group order check)
    # This is speculative
    result = pow(s2_transformed, s1, MOD2)
    # ASSUMPTION: expected result is 1 (i.e., s2 is a primitive root or similar)
    check3 = (result == 1)

    # Overall: checks 1 and 3 must pass (check 2 skipped - machine dependent)
    return check3

def get_computer_id():
    """ASSUMPTION: ComputerID is machine-specific; cannot be computed here.
    Return a placeholder prime for demonstration."""
    # ASSUMPTION: returning a small prime as placeholder
    return 65521  # largest 16-bit prime

def keygen(name):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: name is not used; serial[1] must be the ComputerID (a prime).
    ASSUMPTION: serial[2] must satisfy the int64powmod condition mod 0xFB8D.
    """
    # Step 1: serial[1] = ComputerID (must be prime)
    # ASSUMPTION: We use a placeholder prime since ComputerID is machine-specific
    s1 = get_computer_id()
    assert is_prime_crackme(s1), "ComputerID must be prime"

    # Step 2: Find s2 such that transform_serial2(s2)^s1 mod MOD2 == 1
    # We need to find s2_raw such that ror16(s2_raw, 1)^s1 mod MOD2 == 1
    # ASSUMPTION: this is the actual condition
    for s2_raw in range(2, 0x10000):
        s2_t = transform_serial2(s2_raw)
        if s2_t == 0:
            continue
        if pow(s2_t, s1, MOD2) == 1:
            return f"{s1}-{s2_raw}"

    # Fallback: ASSUMPTION failed, try simple approach
    # s2_transformed = 1 -> pow(1, anything, MOD2) = 1
    # rol16(1, 1) would give us s2_raw
    s2_raw = rol16(1, 1)  # reverse of ror16(s2_raw, 1) == 1
    return f"{s1}-{s2_raw}"


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
