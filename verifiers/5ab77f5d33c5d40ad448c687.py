# Haystack 0.3 keygen/verifier
# Based on the tutorial by PsYch1c (crackmes.de)
#
# What we know from the writeup:
# - Name must be at least 6 characters
# - There are TWO serial fields (IDSERIAL1, IDSERIAL2)
# - The core protection involves THREE runtime-decrypted functions
# - A mathematical property called "amicable numbers" is used
# - The tutorial was truncated before the actual algorithm details were shown
#
# ASSUMPTION: The algorithm involves computing some value(s) from the name,
# then checking/generating amicable numbers or using them as part of serial generation.
# The exact computation is NOT shown in the truncated writeup.

def sum_of_proper_divisors(n):
    """Sum of proper divisors of n (used for amicable number checks)."""
    if n <= 1:
        return 0
    total = 1
    i = 2
    while i * i <= n:
        if n % i == 0:
            total += i
            if i != n // i:
                total += n // i
        i += 1
    return total

def are_amicable(a, b):
    """Check if a and b are amicable numbers."""
    return a != b and sum_of_proper_divisors(a) == b and sum_of_proper_divisors(b) == a

def name_hash(name):
    # ASSUMPTION: Simple sum/product of character ordinals used to derive a base number
    # from which the serial is computed. Exact algorithm unknown.
    total = 0
    for i, c in enumerate(name):
        total += ord(c) * (i + 1)
    return total

def verify(name, serial):
    """
    Attempt to verify name/serial for Haystack 0.3.
    NOTE: Algorithm is PARTIALLY recovered. The writeup was truncated before
    the actual serial computation was revealed. This is a best-guess skeleton.
    """
    if len(name) < 6:
        return False
    # ASSUMPTION: serial is expected as "SERIAL1-SERIAL2" or two parts
    # The crackme has two serial edit boxes
    if '-' in serial:
        parts = serial.split('-', 1)
    else:
        return False
    try:
        s1 = int(parts[0])
        s2 = int(parts[1])
    except ValueError:
        return False
    # ASSUMPTION: The two serials might be an amicable number pair
    # derived from the name hash
    # ASSUMPTION: s1 == some_function(name) and s2 == amicable_partner(s1)
    if are_amicable(s1, s2):
        # ASSUMPTION: name hash must equal s1 or relate to it
        # Without the actual algorithm we cannot verify the name binding
        return True  # ASSUMPTION: simplified check
    return False

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: Since the exact algorithm is unknown, we cannot generate
    a correct serial. This returns a placeholder using amicable numbers.
    """
    if len(name) < 6:
        raise ValueError('Name must be at least 6 characters')
    # ASSUMPTION: Return the smallest amicable pair as placeholder
    # Real keygen would derive serial1 from name and serial2 as amicable partner
    # Known amicable pairs: (220, 284), (1184, 1210), (2620, 2924), etc.
    # ASSUMPTION: name_hash selects which pair or generates the number
    h = name_hash(name)
    # Try to find an amicable partner for h or a nearby number
    # ASSUMPTION: look for amicable pair near hash
    candidate = h
    for _ in range(10000):
        partner = sum_of_proper_divisors(candidate)
        if partner > 1 and sum_of_proper_divisors(partner) == candidate and candidate != partner:
            return f'{candidate}-{partner}'
        candidate += 1
    # fallback
    return '220-284'  # ASSUMPTION: fallback to known amicable pair


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
