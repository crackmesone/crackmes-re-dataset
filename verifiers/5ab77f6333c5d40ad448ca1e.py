# Reverse-engineered from crackmes.de 'backtracking_1' by bublic
# Based on the writeup/tutorial.txt
#
# The serial is 16 hex characters (each parsed via "%1X" so values 0-15)
# Three 32-bit accumulators dw1, dw2, dw3 are built:
#
#   For each index i (0..15) and serial digit d = serial[i] (0..15):
#     dw1 |= (1 << d)
#     dw2 |= (1 << (d + i))   # ECX = EDX+EAX = d+i, then EBX<<CL
#     dw3 |= (1 << (i - d + 15))  # ECX = EAX-EDX+0F = i-d+15, then EBX<<CL
#
# The counter increments once per set bit examined across dw1, dw2, dw3
# (each is shifted right 32 times and each set bit adds 1 to counter).
# Counter must equal 48 (= 16 bits each in dw1, dw2, dw3 => all 16 bits set in each).
#
# Since dw1, dw2, dw3 must each have exactly 16 bits set in their lower 32 bits,
# and each is built via OR of single bits, each must have exactly 16 distinct bits set.
# Since we have 16 characters, each must contribute a UNIQUE bit to each dw.
#
# For dw1: all 16 digits d[i] must be distinct (0..15, each used exactly once)
#           => the digits form a permutation of 0..15
# For dw2: all values (d[i] + i) mod 32 must be distinct across i=0..15
#           (but shift wraps mod 32 implicitly in a 32-bit register)
# For dw3: all values (i - d[i] + 15) mod 32 must be distinct across i=0..15
#
# ASSUMPTION: shift amounts are taken mod 32 (x86 SHL behaviour)
# ASSUMPTION: 'EBX' starts at 1 and is the value shifted (1 << amount),
#             based on 'XOR EBX,EBX; INC EBX' => EBX=1 throughout the loop.

def _build_dws(digits):
    """digits: list of 16 integers in range 0..15"""
    dw1 = 0
    dw2 = 0
    dw3 = 0
    for i, d in enumerate(digits):
        dw1 |= (1 << (d & 31))
        dw2 |= (1 << ((d + i) & 31))
        dw3 |= (1 << ((i - d + 15) & 31))
    return dw1, dw2, dw3


def _count_bits_32(dw):
    """Count set bits in lower 32 bits (simulate 32-step SHR loop)"""
    return bin(dw & 0xFFFFFFFF).count('1')


def verify(name, serial):
    """
    name is ignored (no name-based check described in writeup).
    serial must be exactly 16 hex characters (0-9, A-F, case-insensitive).
    """
    serial = serial.upper().strip()
    if len(serial) != 16:
        return False
    digits = []
    for ch in serial:
        if ch not in '0123456789ABCDEF':
            return False
        digits.append(int(ch, 16))
    dw1, dw2, dw3 = _build_dws(digits)
    counter = _count_bits_32(dw1) + _count_bits_32(dw2) + _count_bits_32(dw3)
    return counter == 48


def keygen(name):
    """
    Generate valid serials using backtracking.
    A valid serial is a permutation of hex digits 0-F (each used exactly once)
    such that the dw2 and dw3 constraints are also satisfied.
    Since digits must form a permutation of 0..15 (for dw1 to have 16 distinct bits),
    we search permutations of 0..15 checking dw2 and dw3 incrementally.
    """
    # Backtracking search
    def backtrack(pos, chosen, used, bits2, bits3):
        if pos == 16:
            yield chosen[:]
            return
        for d in range(16):
            if used[d]:
                continue
            b2 = (d + pos) & 31
            b3 = (pos - d + 15) & 31
            if (bits2 >> b2) & 1:
                continue  # collision in dw2
            if (bits3 >> b3) & 1:
                continue  # collision in dw3
            used[d] = True
            chosen.append(d)
            yield from backtrack(pos + 1, chosen, used,
                                  bits2 | (1 << b2),
                                  bits3 | (1 << b3))
            chosen.pop()
            used[d] = False

    used = [False] * 16
    for digits in backtrack(0, [], used, 0, 0):
        serial = ''.join(format(d, 'X') for d in digits)
        # Double-check
        if verify(name, serial):
            yield serial



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
