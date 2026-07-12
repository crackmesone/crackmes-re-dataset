import math

# Based on the writeup for crackme_4 by norritt
# The serial validation algorithm (from the writeup):
#
# 1. Convert the serial (or name-derived number) to a float
# 2. Compute Ln(x) of that number
# 3. Compute Ln(x)^2
# 4. Multiply by Pi  -->  result = Pi * Ln(x)^2
# 5. Compare with 1111111111111 (the constant at [0040216C])
#    - If result < 1111111111111: result = result * 2 (or similar adjustment, writeup truncated)
#    - Otherwise: proceed
#
# The writeup was TRUNCATED before the full comparison/acceptance logic was shown.
# We can reconstruct the core formula but not the final acceptance condition fully.
#
# From what is shown:
#   value = Pi * (ln(x))^2
#   compared against 1111111111111
#   if value < 1111111111111: some adjustment (writeup cut off)
#
# ASSUMPTION: The serial is a numeric string. The 'name' field may not factor
#             into the algorithm based on the writeup (no name-based derivation shown).
# ASSUMPTION: The acceptance condition is that Pi * ln(x)^2 == 1111111111111
#             (i.e., the crackme checks for equality or near-equality after possible
#             normalization steps not shown in the truncated writeup).
# ASSUMPTION: The multiplication by 2 loop normalizes the value up to the constant,
#             suggesting the check may be after normalization equals the constant.

PI = math.pi
TARGET = 1111111111111.0  # constant from [0040216C] in the crackme


def _compute_value(x: float) -> float:
    """Compute Pi * ln(x)^2 as described in the writeup."""
    ln_x = math.log(x)
    ln_x_sq = ln_x * ln_x
    result = PI * ln_x_sq
    return result


def _normalize(value: float, target: float) -> float:
    """ASSUMPTION: If value < target, multiply by 2 repeatedly until >= target.
       This is based on the partial writeup hint 'number = number * 2 or ...'.
    """
    while value < target:
        value *= 2.0
    return value


def verify(name: str, serial: str) -> bool:
    """
    Attempt to verify the serial for the given name.
    NOTE: The writeup does not show name being used in the serial check;
    the check appears to operate purely on the numeric serial value.
    ASSUMPTION: serial must be a positive integer string > 1 (for ln to be positive).
    ASSUMPTION: After normalization, the value must equal TARGET exactly (or within
    floating-point tolerance). This is an assumption due to truncated writeup.
    """
    try:
        x = float(serial)
    except ValueError:
        return False

    if x <= 0:
        return False

    try:
        value = _compute_value(x)
    except ValueError:
        return False

    # ASSUMPTION: normalization step from writeup
    if value > 0:
        value = _normalize(value, TARGET)
    else:
        # ASSUMPTION: negative ln case not described, reject
        return False

    # ASSUMPTION: check is equality within floating-point tolerance
    return abs(value - TARGET) < 1e-3


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Solves: Pi * ln(x)^2 * 2^k == TARGET for some non-negative integer k,
    where k is the number of doublings needed.
    i.e., Pi * ln(x)^2 == TARGET / 2^k
    So ln(x)^2 == TARGET / (Pi * 2^k)
    ln(x) == sqrt(TARGET / (Pi * 2^k))
    x == exp(sqrt(TARGET / (Pi * 2^k)))
    We want x to be a positive integer, try k=0,1,2,...
    ASSUMPTION: name does not affect keygen.
    """
    for k in range(0, 200):
        divisor = TARGET / (2 ** k)
        ln_x_sq = divisor / PI
        if ln_x_sq < 0:
            continue
        ln_x = math.sqrt(ln_x_sq)
        x = math.exp(ln_x)
        # Try rounding to nearest integer
        x_int = round(x)
        if x_int > 1:
            # Verify
            if verify(name, str(x_int)):
                return str(x_int)
        # Also try the float directly (non-integer serial)
        candidate = str(int(x)) if x > 1 else None
        if candidate and verify(name, candidate):
            return candidate

    # ASSUMPTION: fallback - return the float value for k=0
    ln_x = math.sqrt(TARGET / PI)
    x = math.exp(ln_x)
    return str(x)



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
