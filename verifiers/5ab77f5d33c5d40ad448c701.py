import struct
import math

# The matrix M (6x6 floats) as described in the writeup
# Each row corresponds to coefficients for s[0]..s[5]
M = [
    [-0.2, -0.4,  0.6,  0.4,  0.2, -0.4],
    [-0.4,  0.2,  0.2,  0.8, -0.6,  0.2],
    [ 0.8,  0.6, -0.4, -0.6,  0.2, -0.4],
    [-0.2, -0.4,  0.6,  0.4, -0.8,  0.6],
    [-0.4,  0.2,  0.2, -0.2,  0.4,  0.2],
    [ 0.6,  0.2, -0.8, -0.2,  0.4,  0.2],
]

# Inverse matrix M^-1 as given in the writeup
M_inv = [
    [1, 0, 1, 1, 0, 1],
    [0, 1, 1, 0, 1, 0],
    [1, 0, 1, 1, 1, 0],
    [1, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1],
]

# ASSUMPTION: The float constants stored on the stack correspond exactly to
# the matrix M values listed in the writeup (as IEEE 754 single precision).
# The constants in the disasm (BE4CCCCD, BECCCCCD, 3F19999A, 3ECCCCCD, etc.)
# match -0.2, -0.4, 0.6, 0.4, 0.2, -0.4 etc. in single precision.

# ASSUMPTION: The x[i] values are computed from the name using some algorithm
# described as "6 numbers calculated from name and masked with 0FFFFFh".
# The exact name->x[] algorithm is NOT fully described in the writeup.
# The keygen assembly source was truncated. We reconstruct it based on the
# description and common patterns for such crackmes.

def compute_x_from_name(name):
    """
    ASSUMPTION: The x[i] values are computed from the name characters
    and masked with 0xFFFFF. The exact algorithm is not given in full.
    Based on common patterns for such crackmes, we attempt a plausible
    reconstruction. This is a PARTIAL recovery - the real algo is in the
    (truncated) assembly keygen source.
    
    A common approach: iterate over name bytes, accumulate into 6 buckets
    using position mod 6 or character-based arithmetic.
    
    Since the writeup says 'this algo is ripped in keygen. See there.' and
    the keygen source is truncated, we mark this as an assumption.
    """
    # ASSUMPTION: Simple sum-based approach - accumulate char values
    # into x[i] using shifts/multiplies typical of such keygens.
    # Without the full assembly, we use a placeholder that produces
    # consistent values.
    x = [0] * 6
    for i, c in enumerate(name):
        v = ord(c)
        for j in range(6):
            # ASSUMPTION: rotate/xor style mixing
            x[j] = (x[j] * 0x1F + v + j) & 0xFFFFF
    return x


def int_to_base36(n):
    """Convert integer to base-36 uppercase string."""
    if n == 0:
        return '0'
    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    while n > 0:
        result = digits[n % 36] + result
        n //= 36
    return result


def base36_to_int(s):
    """Convert base-36 uppercase string to integer."""
    return int(s, 36)


def mat_vec_mul_float(mat, vec):
    """Multiply 6x6 float matrix by 6-vector."""
    result = []
    for row in mat:
        val = sum(row[j] * vec[j] for j in range(6))
        result.append(val)
    return result


def mat_vec_mul_int(mat, vec):
    """Multiply 6x6 integer matrix by 6-vector (for M_inv)."""
    result = []
    for row in mat:
        val = sum(row[j] * vec[j] for j in range(6))
        result.append(val)
    return result


def keygen(name):
    """
    Generate serial for given name.
    Algorithm:
      1. Compute x[0..5] from name (masked with 0xFFFFF)
      2. s = M_inv * x  (integer matrix multiply)
      3. Encode each s[i] as base-36 string
      4. Serial = s[0]-s[1]-s[2]-s[3]-s[4]-s[5]
    """
    x = compute_x_from_name(name)
    s = mat_vec_mul_int(M_inv, x)
    parts = [int_to_base36(int(round(v))) for v in s]
    return '-'.join(parts)


def verify(name, serial):
    """
    Verify name/serial pair.
    Algorithm:
      1. Compute x[0..5] from name (masked with 0xFFFFF)
      2. Parse serial: 6 base-36 numbers s[0..5]
      3. Compute y = M * s  (float matrix multiply)
      4. Check round(y[i]) == x[i] for all i
    """
    if not name:
        return False
    
    # Parse serial format: 6 alphanumeric groups separated by '-'
    import re
    parts = serial.upper().split('-')
    if len(parts) != 6:
        return False
    pattern = re.compile(r'^[0-9A-Z]+$')
    if not all(pattern.match(p) for p in parts):
        return False
    
    try:
        s = [base36_to_int(p) for p in parts]
    except ValueError:
        return False
    
    x = compute_x_from_name(name)
    y_float = mat_vec_mul_float(M, s)
    y_rounded = [int(round(v)) for v in y_float]
    
    return y_rounded == x



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
