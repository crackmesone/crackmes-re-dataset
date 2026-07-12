# pick_my_lock by badsector - reverse engineered serial checker
#
# From the writeup analysis:
# 1. Serial must be exactly 20 uppercase letters (A-Z)
# 2. Each char: subtract 0x41, run through an XLAT table (unknown), add 0x41
# 3. The result is XOR/filtered against 'BENDERISGREEAT' (bender string)
# 4. Subtract 0x41 again -> must be in 0-9 range (each byte 0-9)
# 5. The 20 digits represent 10 (row, col) pairs for placing 'x' on a 10x10 board
# 6. The board is checked: 10-queens problem on a 10x10 board (no two queens attack)
#    (horizontal, vertical, diagonal checks)
#
# The XLAT table content is NOT given in the writeup, so we cannot fully reverse
# the serial->coordinates mapping. However, the 16 valid coordinate sets ARE given
# in the Pascal solution, and the serial encoding IS given (checkmatit procedure).
#
# From PMLcheckmator.pas, the encoding (checkmatit) is:
#   Build charis[0..19] from pa[0..9] (queens positions) as:
#     charis[i*4]   = i        for i in 0..4
#     charis[i*4+2] = pa[i]    for i in 0..4
#     charis[(i-5)*4+1] = i    for i in 5..9
#     charis[(i-5)*4+3] = pa[i] for i in 5..9
#   Then for each byte:
#     charis[i] = charis[i] + bender[i] - 0x41
#     if charis[i] < 0x12: charis[i] += 0x41 + 0x08
#     else:                 charis[i] += 0x41 - 0x12
#   Serial = chr of each charis[i]
#
# ASSUMPTION: The XLAT table and its inverse are handled implicitly by the
# checkmatit encoding - the 16 valid serials are fully determined by the 16
# pa[] arrays given in the Pascal code.

bender = [0x42,0x45,0x4E,0x44,0x45,0x52,0x49,0x53,0x47,0x52,
           0x45,0x41,0x54,0x42,0x45,0x4E,0x44,0x45,0x52,0x49]

# 16 valid queen placements from PMLcheckmator.pas
valid_placements = [
    [0,9,6,4,7,1,8,2,5,3],  # pts1ra
    [9,0,5,3,1,7,2,8,6,4],  # pts1rb
    [0,9,4,6,8,2,7,1,3,5],  # pts1la
    [9,0,3,5,2,8,1,7,4,6],  # pts1lb
    [8,5,3,6,0,7,1,4,2,9],  # pts2ra
    [9,4,2,0,6,1,7,5,3,8],  # pts2rb
    [8,3,5,7,1,6,0,2,4,9],  # pts2la
    [9,2,4,1,7,0,6,3,5,8],  # pts2lb
    [5,3,1,7,2,8,6,4,9,0],  # pts3ra
    [6,4,7,1,8,2,5,3,0,9],  # pts3rb
    [3,5,2,8,1,7,4,6,9,0],  # pts3la
    [4,6,8,2,7,1,3,5,0,9],  # pts3lb
    [1,6,4,2,8,3,9,7,5,0],  # pts4ra
    [0,7,5,8,2,9,3,6,4,1],  # pts4rb
    [1,4,6,3,9,2,8,5,7,0],  # pts4la
    [0,5,7,9,3,8,2,4,6,1],  # pts4lb
]

def checkmatit(pa):
    """Encode a queen placement pa[0..9] into a 20-char serial string."""
    charis = [0] * 21
    for i in range(5):
        charis[i*4]   = i
        charis[i*4+2] = pa[i]
    for i in range(5, 10):
        charis[(i-5)*4+1] = i
        charis[(i-5)*4+3] = pa[i]
    result = []
    for i in range(20):
        v = charis[i] + bender[i] - 0x41
        if v < 0x12:
            v += 0x41 + 0x08
        else:
            v += 0x41 - 0x12
        result.append(chr(v))
    return ''.join(result)

# Pre-compute all valid serials
VALID_SERIALS = set()
for pa in valid_placements:
    s = checkmatit(pa)
    VALID_SERIALS.add(s)


def decode_serial(serial):
    """Reverse checkmatit to get charis bytes (0..9 range coords)."""
    if len(serial) != 20:
        return None
    charis = []
    for i in range(20):
        v = ord(serial[i])
        # reverse the add
        if v >= 0x41 + 0x08:  # came from v < 0x12 branch: v = orig + 0x41 + 0x08
            orig = v - 0x41 - 0x08
        else:  # came from v >= 0x12 branch: v = orig + 0x41 - 0x12
            orig = v - 0x41 + 0x12
        # orig = charis[i] + bender[i] - 0x41 => charis[i] = orig - bender[i] + 0x41
        c = orig - bender[i] + 0x41
        if c < 0 or c > 9:
            return None
        charis.append(c)
    # reconstruct pa[0..9]
    # charis[i*4]=i, charis[i*4+2]=pa[i] for i in 0..4
    # charis[(i-5)*4+1]=i, charis[(i-5)*4+3]=pa[i] for i in 5..9
    pa = [0]*10
    for i in range(5):
        if charis[i*4] != i:
            return None
        pa[i] = charis[i*4+2]
    for i in range(5, 10):
        if charis[(i-5)*4+1] != i:
            return None
        pa[i] = charis[(i-5)*4+3]
    return pa


def is_valid_10queens(pa):
    """Check if pa[0..9] is a valid 10-queens placement (no attacks)."""
    n = len(pa)
    # Check each value in 0-9
    for v in pa:
        if v < 0 or v > 9:
            return False
    # Check no two queens in same column
    if len(set(pa)) != n:
        return False
    # Check diagonals
    for i in range(n):
        for j in range(i+1, n):
            if abs(pa[i] - pa[j]) == abs(i - j):
                return False
    return True


def verify(name, serial):
    """
    Verify a serial for pick_my_lock.
    NOTE: name is NOT used in the check (this crackme is name-independent).
    Serial must be exactly 20 uppercase letters encoding a valid 10-queens solution.
    """
    if len(serial) != 20:
        return False
    for c in serial:
        if not c.isupper():
            return False
    # Check against known valid serials
    if serial in VALID_SERIALS:
        return True
    # Also try to decode and verify independently
    pa = decode_serial(serial)
    if pa is None:
        return False
    return is_valid_10queens(pa)


def keygen(name):
    """Generate all 16 valid serials (name-independent)."""
    for pa in valid_placements:
        yield checkmatit(pa)



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
