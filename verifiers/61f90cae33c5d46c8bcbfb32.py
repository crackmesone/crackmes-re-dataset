import random
import string


def verify(name: str, serial: str) -> bool:
    """
    Validate a serial key according to the VladMetz Keygenme #1 algorithm.

    Constraints derived from the write-up / Marshad's brute-force:
      - Key length must be <= 11 characters (write-up says exactly 11 are used)
      - Let the 11-character key be indexed 0..10
      - Algorithm:
          r8d  = key[9]  - key[10]
          edx  = key[5]  - key[3]
          ecx  = key[6]  - key[0]
          edx  = edx * ecx
          r8d  = r8d * r8d
          eax  = edx * 0x88          # 0x88 == 136
          r8d  = r8d + eax
          check: r8d == 0x660        # 0x660 == 1632

    Indices in Marshad's brute-force (0-based chars a,b,c,d,e,f -> positions 0,3,5,6,9,10):
      (e - f)^2  + 136*(c - b)*(d - a) == 1632
      i.e.  (key[9]-key[10])^2 + 136*(key[5]-key[3])*(key[6]-key[0]) == 1632
    """
    # Length check: must be <= 11, but we need at least 11 characters for the algorithm
    if len(serial) < 11 or len(serial) > 11:
        return False

    r8d = ord(serial[9]) - ord(serial[10])
    edx = ord(serial[5]) - ord(serial[3])
    ecx = ord(serial[6]) - ord(serial[0])
    edx = edx * ecx
    r8d = r8d * r8d
    eax = edx * 0x88  # 136
    r8d = r8d + eax

    return r8d == 0x660  # 1632


def keygen(name: str = "") -> str:
    """
    Generate a valid 11-character key.
    Strategy:
      - Pick random values for positions 0,3,5,6 such that
        (key[5]-key[3])*(key[6]-key[0]) divides evenly into
        (1632 - r8d^2) / 136 for some integer r8d.
      - Positions 1,2,4,7,8 are unconstrained (random printable ascii).

    The equation is:
      (key[9]-key[10])^2 + 136*(key[5]-key[3])*(key[6]-key[0]) == 1632

    Let P = (key[5]-key[3])*(key[6]-key[0])
    Then (key[9]-key[10])^2 == 1632 - 136*P
    We need 1632 - 136*P >= 0  and  sqrt(1632 - 136*P) is an integer.

    1632 = 136 * 12, so valid values of P where 136*P <= 1632 are P in {0,1,...,12}.
    And 1632 - 136*P must be a perfect square.

    Valid (P, r8d_abs) pairs:
      P=0  -> 1632 - 0 = 1632  (not perfect square)
      P=1  -> 1496  (not perfect square)
      P=2  -> 1360  (not perfect square)
      P=3  -> 1224  (not perfect square)
      P=4  -> 1088  (not perfect square)
      P=5  -> 952   (not perfect square)
      P=6  -> 816   (not perfect square)
      P=7  -> 680   (not perfect square)
      P=8  -> 544   (not perfect square)
      P=9  -> 408   (not perfect square)
      P=10 -> 272   (not perfect square)
      P=11 -> 136   (not perfect square)
      P=12 -> 0     -> r8d = 0  (perfect square!) => key[9] == key[10]

    # ASSUMPTION: Only P=12 gives integer r8d among P in 0..12.
    # So the solution requires (key[5]-key[3])*(key[6]-key[0]) == 12
    # and key[9] == key[10].
    # (Verified by Marshad's equation and Sir_Zed's example 'xxxppp' style keys)
    """
    import math

    printable = [chr(c) for c in range(33, 126)]
    letters = string.ascii_letters

    while True:
        # Find characters satisfying the constraint
        # Try all factor pairs of target_P from printable chars
        # We'll randomly pick and check

        # Random free positions
        k = [random.choice(letters) for _ in range(11)]

        # We need (k[5]-k[3])*(k[6]-k[0]) == P  and  (k[9]-k[10])^2 == 1632 - 136*P
        # Iterate over possible P values
        # ASSUMPTION: Printable char range 33-125 allows differences in range [-92, 92]
        for P in range(-92*92, 92*92 + 1):
            remainder = 1632 - 136 * P
            if remainder < 0:
                continue
            sqrt_r = int(math.isqrt(remainder))
            if sqrt_r * sqrt_r != remainder:
                continue
            # Valid P found; now pick chars realizing this
            # Try a random factor split of P
            for _ in range(200):
                # Pick key[3] and key[5] randomly, derive (key[5]-key[3])
                c3 = random.choice(printable)
                # Need factor1 * factor2 == P
                # Let factor1 = key[5] - key[3]
                if P == 0:
                    factor1 = 0
                    factor2 = 0
                else:
                    # Find divisors of P
                    factors = []
                    for d in range(-92, 93):
                        if d != 0 and P % d == 0:
                            factors.append(d)
                    if not factors:
                        break
                    factor1 = random.choice(factors)
                    factor2 = P // factor1

                # key[5] = key[3] + factor1
                v3 = ord(c3)
                v5 = v3 + factor1
                if not (33 <= v5 <= 125):
                    continue

                # key[6] = key[0] + factor2
                c0 = random.choice(printable)
                v0 = ord(c0)
                v6 = v0 + factor2
                if not (33 <= v6 <= 125):
                    continue

                # key[9] - key[10] = +/- sqrt_r
                diff = random.choice([sqrt_r, -sqrt_r])
                c10 = random.choice(printable)
                v10 = ord(c10)
                v9 = v10 + diff
                if not (33 <= v9 <= 125):
                    continue

                # Build the key
                k[0] = c0
                k[3] = c3
                k[5] = chr(v5)
                k[6] = chr(v6)
                k[9] = chr(v9)
                k[10] = c10

                candidate = ''.join(k)
                if verify(name, candidate):
                    return candidate
            break  # Only check small P values efficiently; break after first valid P tried



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
            print(_sv)
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
