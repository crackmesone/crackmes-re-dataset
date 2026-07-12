#!/usr/bin/env python3
"""
Reverse-engineered keygen for SunnY KeYGenMe no.#2 by ManSun

Algorithm summary (from writeup):
1. Name must be 2-15 chars, uppercase letters only (A-Z)
2. Compute name_seed = sum of ASCII values of name chars
   If name_seed is odd, name_seed += 1  (make it even)
3. The 16 serial boxes form a 4x4 magic-like grid (row-major order):
   [ k0  k1  k2  k3 ]
   [ k4  k5  k6  k7 ]
   [ k8  k9  k10 k11]
   [ k12 k13 k14 k15]
4. All 16 values must be UNIQUE (no repeats)
5. Row sums, column sums, diagonal sums computed:
   - row1_sum != row2_sum  (rows must NOT be equal to each other)
   - row3_sum != row4_sum
   - col1_sum != col2_sum
   - col3_sum != col4_sum
   - diag1_sum == diag2_sum  (diagonals MUST be equal)
6. row1_sum == name_seed  (first row sum equals the name seed)

Note: The writeup says sums of rows/cols should NOT be equal to adjacent
ones, but the diagonals MUST be equal. Only row1 must equal name_seed.
The other rows/cols just need to be internally consistent (unique elements,
diagonals equal). The writeup author used a template-based approach.
"""

def compute_name_seed(name: str) -> int:
    name = name.upper()
    s = sum(ord(c) for c in name)
    if s % 2 != 0:
        s += 1
    return s


def verify(name: str, serial: list) -> bool:
    """
    name: string (2-15 chars, A-Z)
    serial: list of 16 integers (the 16 box values)
    Returns True if valid.
    """
    name = name.upper()
    # Check name length
    if len(name) < 2 or len(name) > 15:
        return False
    # Check name is all uppercase A-Z
    for c in name:
        if ord(c) < 0x41 or ord(c) > 0x5A:
            return False
    # Check serial has 16 elements
    if len(serial) != 16:
        return False

    # Check all unique
    if len(set(serial)) != 16:
        return False

    k = serial
    # Rows
    r1 = k[0]  + k[1]  + k[2]  + k[3]
    r2 = k[4]  + k[5]  + k[6]  + k[7]
    r3 = k[8]  + k[9]  + k[10] + k[11]
    r4 = k[12] + k[13] + k[14] + k[15]
    # Columns
    c1 = k[0] + k[4] + k[8]  + k[12]
    c2 = k[1] + k[5] + k[9]  + k[13]
    c3 = k[2] + k[6] + k[10] + k[14]
    c4 = k[3] + k[7] + k[11] + k[15]
    # Diagonals
    d1 = k[0]  + k[5]  + k[10] + k[15]  # top-left to bottom-right
    d2 = k[3]  + k[6]  + k[9]  + k[12]  # top-right to bottom-left

    name_seed = compute_name_seed(name)

    # Check row1 == name_seed
    if r1 != name_seed:
        return False
    # Check rows not equal to adjacent
    if r1 == r2:
        return False
    if r3 == r4:
        return False
    # Check columns not equal to adjacent
    if c1 == c2:
        return False
    if c3 == c4:
        return False
    # Diagonals must be equal
    if d1 != d2:
        return False

    return True


def keygen(name: str) -> list:
    """
    Generate a valid 16-element serial for the given name.
    Strategy (from writeup):
      - Compute name_seed; distribute across row1 (4 values near seed//4)
      - Fill remaining 12 cells with distinct values
      - Manipulate to make diagonals equal
    """
    name = name.upper()
    assert 2 <= len(name) <= 15, "Name length must be 2-15"
    for c in name:
        assert 0x41 <= ord(c) <= 0x5A, "Name must be A-Z only"

    seed = compute_name_seed(name)

    # Build row1: 4 distinct positive integers summing to seed
    # Use base = seed // 4, distribute remainder
    base = seed // 4
    rem = seed % 4
    # row1 values: base, base, base, base + adjust for remainder
    # Make them distinct by small offsets
    # e.g., base-1, base, base+1, base+rem-2  (sum = 4*base + rem = seed)
    # ASSUMPTION: exact distribution strategy from author not given; this is a heuristic
    row1 = [base - 1, base, base + 1, seed - (base - 1) - base - (base + 1)]
    # Ensure all row1 are distinct and positive
    if len(set(row1)) != 4 or any(v <= 0 for v in row1):
        # fallback
        row1 = [1, 2, 3, seed - 6]
        assert sum(row1) == seed

    # Build remaining 12 values, all distinct from each other and from row1
    used = set(row1)
    # Start filling from a value unlikely to collide
    start = max(used) + 1
    rest = []
    v = start
    while len(rest) < 12:
        if v not in used:
            rest.append(v)
            used.add(v)
        v += 1

    # Arrange into grid:
    # row1: k0..k3
    # row2: rest[0..3]  = k4..k7
    # row3: rest[4..7]  = k8..k11
    # row4: rest[8..11] = k12..k15
    k = row1 + rest

    # Now manipulate to make diagonals equal
    # d1 = k[0] + k[5] + k[10] + k[15]
    # d2 = k[3] + k[6] + k[9]  + k[12]
    # We want d1 == d2
    # ASSUMPTION: We swap k[15] and k[14] or adjust values to equalize diagonals
    # Try swapping elements in rows 2-4 to equalize diagonals
    # Simple approach: adjust k[15] by swapping with k[14] if possible, etc.
    # More robust: try all permutations of rest rows

    from itertools import permutations

    best = None
    # Try permutations of each sub-row to find diagonal equality
    # This is a brute-force fallback since template approach not fully specified
    r2_vals = rest[0:4]
    r3_vals = rest[4:8]
    r4_vals = rest[8:12]

    found = False
    for p2 in permutations(r2_vals):
        for p3 in permutations(r3_vals):
            for p4 in permutations(r4_vals):
                k = list(row1) + list(p2) + list(p3) + list(p4)
                d1 = k[0] + k[5] + k[10] + k[15]
                d2 = k[3] + k[6] + k[9]  + k[12]
                r1s = k[0]+k[1]+k[2]+k[3]
                r2s = k[4]+k[5]+k[6]+k[7]
                r3s = k[8]+k[9]+k[10]+k[11]
                r4s = k[12]+k[13]+k[14]+k[15]
                c1s = k[0]+k[4]+k[8]+k[12]
                c2s = k[1]+k[5]+k[9]+k[13]
                c3s = k[2]+k[6]+k[10]+k[14]
                c4s = k[3]+k[7]+k[11]+k[15]
                if (d1 == d2 and r1s != r2s and r3s != r4s
                        and c1s != c2s and c3s != c4s
                        and len(set(k)) == 16):
                    found = True
                    best = k
                    break
            if found:
                break
        if found:
            break

    if best is None:
        raise ValueError(f"Could not generate valid serial for name '{name}'. Try different name.")

    return best



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
