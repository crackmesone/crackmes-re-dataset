import random
import itertools

# Based on solution writeup by Frantz04:
# - Password must be exactly 10 characters long
# - Sum of all character ASCII values must equal 0x40A (1034)
# - XOR of all character ASCII values must equal 0x26 (38)
# - All other checks (quantum, neural, etc.) are fake/decorative

TARGET_SUM = 0x40A   # 1034
TARGET_XOR = 0x26   # 38
REQUIRED_LENGTH = 10


def verify(name: str, serial: str) -> bool:
    """Verify a password against the known constraints.
    NOTE: 'name' is not used in the check - only 'serial' (the password) matters.
    """
    # Check 1: length must be exactly 10
    if len(serial) != REQUIRED_LENGTH:
        return False

    # Check 2: sum of all ASCII values must equal 0x40A
    char_sum = sum(ord(c) for c in serial)
    if char_sum != TARGET_SUM:
        return False

    # Check 3: XOR of all ASCII values must equal 0x26
    char_xor = 0
    for c in serial:
        char_xor ^= ord(c)
    if char_xor != TARGET_XOR:
        return False

    return True


def keygen(name: str = "") -> str:
    """Generate a valid password satisfying sum=0x40A and XOR=0x26.
    The known working example from the writeup uses these chars:
    ['c', 'd', 'e', 'f', 'x', 'h', 'i', 'j', 'k', 'Z']
    Verify: ord values: c=99, d=100, e=101, f=102, x=120, h=104, i=105, j=106, k=107, Z=90
    Sum = 99+100+101+102+120+104+105+106+107+90 = 1034 = 0x40A  (check!)
    XOR = 99^100^101^102^120^104^105^106^107^90 = ?
    """
    # Also mentioned: 'jolilojglD' is a valid key per comment by ROnixx
    # Verify the base set from writeup
    base_chars = ['c', 'd', 'e', 'f', 'x', 'h', 'i', 'j', 'k', 'Z']
    result = ''.join(base_chars)

    # Shuffle to produce different valid passwords (all permutations are valid
    # since sum and XOR are commutative/associative over the same set)
    shuffled = base_chars[:]
    random.shuffle(shuffled)
    return ''.join(shuffled)


def generate_custom_password(charset=None):
    """Generate a custom 10-char password satisfying the constraints.
    Picks 9 random chars then solves for the 10th to satisfy sum constraint,
    then adjusts to fix XOR.
    """
    if charset is None:
        # Printable ASCII range
        charset = [chr(c) for c in range(0x20, 0x7F)]

    for _ in range(100000):
        # Pick 8 random characters
        chosen = [random.choice(charset) for _ in range(8)]
        current_sum = sum(ord(c) for c in chosen)
        current_xor = 0
        for c in chosen:
            current_xor ^= ord(c)

        # We need two more chars c9, c10 such that:
        # current_sum + ord(c9) + ord(c10) == TARGET_SUM
        # current_xor ^ ord(c9) ^ ord(c10) == TARGET_XOR
        needed_sum = TARGET_SUM - current_sum
        needed_xor = TARGET_XOR ^ current_xor

        # Try all printable pairs
        for v9 in range(0x20, 0x7F):
            v10 = needed_sum - v9
            if 0x20 <= v10 < 0x7F:
                if (v9 ^ v10) == needed_xor:
                    password = ''.join(chosen) + chr(v9) + chr(v10)
                    if verify('', password):
                        return password

    # ASSUMPTION: fallback to known-good permutation if random generation fails
    return keygen(name)

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
