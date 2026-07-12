import math
import random

def _k1k2(name: str):
    """Compute k1 and k2 from the first two characters of name."""
    if len(name) < 2:
        raise ValueError("Name must be at least 2 characters.")
    k1 = round(ord(name[0]) / 5)
    k2 = round(ord(name[1]) / 5)
    return k1, k2

def verify(name: str, serial: str) -> bool:
    """
    Verification logic recovered from the solution write-up.

    The crackme accepts a serial if:
      sum(ord(c) for c in serial) mod k1 == 0
      AND
      sum(ord(c) for c in serial) mod k2 == 0

    Which is equivalent to: the sum of ord values of the serial characters
    must be divisible by both k1 and k2, i.e. divisible by lcm(k1, k2).

    The solution writer notes the simplest target is sum == k1*k2,
    and the keygen (Unit1.pas) builds a string whose running ord-sum
    reaches k1*k2 in a specific way. Both conditions collapse to the
    same requirement: total_sum is a multiple of lcm(k1, k2).
    """
    if len(name) < 2:
        return False
    k1, k2 = _k1k2(name)
    if k1 == 0 or k2 == 0:
        # ASSUMPTION: if either key is 0, division by zero would occur; treat as invalid
        return False
    total = sum(ord(c) for c in serial)
    return (total % k1 == 0) and (total % k2 == 0)

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy: target = k1 * k2 (the simplest common multiple, as used in
    the original keygen source). Build a serial whose ord-sum equals target
    by choosing printable random characters until the remaining sum fits in
    one final character (matching the Delphi keygen logic closely).

    The Delphi keygen:
      suma = k1*k2
      repeat
        k = round(32 + random(95))   -- printable ASCII 32..126
        kod += chr(k)
        suma -= k
      until suma < 127
      kod += chr(suma)  -- append the last character
    """
    if len(name) < 2:
        raise ValueError("Name must be at least 2 characters.")
    k1, k2 = _k1k2(name)
    if k1 == 0 or k2 == 0:
        raise ValueError("k1 or k2 is zero; cannot generate serial.")

    target = k1 * k2

    # ASSUMPTION: if target < 32 we cannot form a valid single printable char;
    # in that case just return chr(target) if printable, else raise.
    if target < 1:
        raise ValueError("Target sum is non-positive.")

    # Mimic the Delphi repeat-until loop
    # Delphi random(95) returns 0..94, so k in [32, 126]
    serial_chars = []
    suma = target
    max_iterations = 10000  # safety guard
    iterations = 0
    while suma >= 127 and iterations < max_iterations:
        # pick a random printable char whose ord <= suma (so we don't overshoot into negative)
        low = 32
        high = min(126, suma - 1)  # keep suma > 0 after subtraction
        if low > high:
            # ASSUMPTION: if we can't pick a char without going negative,
            # restart accumulation
            serial_chars = []
            suma = target
            iterations += 1
            continue
        k = random.randint(low, high)
        serial_chars.append(chr(k))
        suma -= k
        iterations += 1

    if suma < 0 or suma > 127:
        # Fallback: just build a serial directly
        # ASSUMPTION: produce a deterministic serial if random approach fails
        serial_chars = []
        suma = target
        while suma >= 127:
            k = 64  # '@'
            serial_chars.append(chr(k))
            suma -= k
        serial_chars.append(chr(suma))
        return ''.join(serial_chars)

    serial_chars.append(chr(suma))
    return ''.join(serial_chars)



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
