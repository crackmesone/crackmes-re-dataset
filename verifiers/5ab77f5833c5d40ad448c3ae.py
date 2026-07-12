#!/usr/bin/env python3
"""
KeygenMe #2 by Lesco - reverse engineered algorithm
Based on the solution writeup by Johannes.

Algorithm summary:
1. Check name length: 3 <= len(name) <= 20
2. Hash the name to a 32-bit value
3. Split hash into two vectors x[3] and y[3] (5 bits each, sign+4bit magnitude)
4. For each x[i], call evaluate(x[i]) -> (a, b, c) triple
5. The serial encodes three values that must match y[0], y[1], y[2]
   when passed through evaluate()

The 'evaluate' subroutine is described as transforming a value into three values.
The writeup was truncated before fully describing evaluate() and the serial format.
See ASSUMPTION comments.
"""

def hash_name(name):
    """Compute 32-bit hash of name."""
    h = 0x0DEADCA7
    for ch in name:
        n = ord(ch) & 0xFF
        # h = (~((n >> 2) + (h ^ 0xf28437*n)) - 0xd23664*n) & 0xFFFFFFFF
        inner = (h ^ (0xF28437 * n)) + (n >> 2)
        h = (~inner - 0xD23664 * n) & 0xFFFFFFFF
    return h

def chop_hash(h):
    """
    Split 32-bit hash into two vectors x[3] and y[3].
    Each element uses 5 bits: bits[3:0] = abs_value-1, bit[4] = sign.
    x gets elements at even iterations (i=0,2,4 -> x[0],x[1],x[2])
    y gets elements at odd iterations  (i=1,3,5 -> y[0],y[1],y[2])
    After each pair, ensure x values are all distinct.
    """
    x = []
    y = []
    val_h = h
    for i in range(6):
        abs_val = (val_h & 0xF) + 1
        sign_bit = (val_h >> 4) & 1
        val = -abs_val if sign_bit else abs_val
        val_h >>= 5

        if i % 2 == 0:
            # x element
            x.append(val)
        else:
            # y element
            y.append(val)
            # After adding x[i//2], check all previous x values for uniqueness
            xi = i // 2
            for j in range(xi):
                if x[j] == x[xi]:
                    x[j] += 1
    return x, y

# ASSUMPTION: The 'evaluate' subroutine computes something like:
# given an integer t, find integers a, b such that some quadratic/polynomial
# relationship holds. The writeup says evaluate() transforms a value into
# three output values (result triple). The exact formula was not shown because
# the writeup was truncated. Based on the description ("little math problem",
# "solve a math problem"), a plausible guess is that evaluate computes
# the roots or coefficients of a polynomial, or solves a Diophantine equation.
# We cannot implement it faithfully without the full writeup.

def evaluate(t):
    """
    ASSUMPTION: evaluate(t) -> (a, b, c) or similar triple.
    The exact algorithm is UNKNOWN - writeup was truncated.
    Placeholder returns (t, t, t) so the structure compiles.
    """
    # ASSUMPTION: Unknown - writeup truncated before revealing this function
    raise NotImplementedError("evaluate() algorithm not recovered from truncated writeup")

def check_length(name):
    return 3 <= len(name) <= 20

def verify(name, serial):
    """
    Verify name/serial pair.
    Steps:
    1. Check name length
    2. Hash name
    3. Chop hash into x[3], y[3]
    4. For each x[i], evaluate(x[i]) should yield something matching y[i]
    5. Serial encodes values that when passed through evaluate() match y[0..2]
    """
    if not check_length(name):
        return False

    h = hash_name(name)
    x, y = chop_hash(h)

    # ASSUMPTION: The serial is parsed into three integers s[0], s[1], s[2]
    # and evaluate(s[i]) must equal evaluate(x[i]) or match y[i] somehow.
    # Since evaluate() is unknown, we cannot complete this.
    # ASSUMPTION: serial format is dash-separated decimal integers
    try:
        parts = serial.replace('-', ' ').split()
        s = [int(p) for p in parts]
    except Exception:
        return False

    # ASSUMPTION: The check is that for each i in range(3),
    # evaluate(s[i]) matches y[i] in some way.
    # Without the full evaluate() we mark this as partial.
    try:
        for i in range(3):
            result_s = evaluate(s[i])
            result_x = evaluate(x[i])
            # ASSUMPTION: result must equal y[i] or result_s == result_x
            if result_s != result_x:
                return False
    except NotImplementedError:
        # Cannot verify without evaluate()
        return False

    return True

def keygen(name):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: Since evaluate() is unknown, this is incomplete.
    """
    if not check_length(name):
        raise ValueError(f"Name must be 3-20 characters, got {len(name)}")

    h = hash_name(name)
    x, y = chop_hash(h)

    print(f"Name hash: 0x{h:08X}")
    print(f"x vector: {x}")
    print(f"y vector: {y}")

    # ASSUMPTION: The serial is derived by finding s[i] such that
    # evaluate(s[i]) == y[i] for each i in range(3).
    # Without evaluate(), we cannot produce a valid serial.
    raise NotImplementedError(
        "keygen incomplete: evaluate() algorithm not recovered from truncated writeup.\n"
        f"Name: {name!r}, hash: 0x{h:08X}, x={x}, y={y}"
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
