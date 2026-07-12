# Crackme 0.68 by bswap - Reverse Engineered Validation
# Based on Harlequin's writeup
#
# There are TWO stages:
#
# STAGE 1: A 12-character key that must satisfy a palindrome-like symmetry:
#   Position 0 == Position 11
#   Position 1 == Position 10  (actually described as "B" matching)
#   Position 2 == Position 9   (actually described as "B" matching)
#   Middle positions can be anything
#   The diagram shows: 102000000201 as an example structure
#   475777777574 is given as a valid example
#   Pattern: A?B??????B?A where A[0]==A[11], B[2]==B[9]
#   ASSUMPTION: the check is serial[0]==serial[11] and serial[2]==serial[9]
#   (and possibly serial[1]==serial[10] based on the diagram)
#
# STAGE 2: Registration with Name + Serial
#   Serial must have 'r' at index 3 (4th character)
#   Name must contain 'T' and 'l' at positions 12 and 13 (0-indexed)
#   ASSUMPTION: The name length should be at least 14 characters to reach positions 12-13
#   The serial only needs to be >= 4 characters with serial[3] == 'r'

import string
import random

def verify_stage1(serial: str) -> bool:
    """
    Stage 1 key check.
    The key must be 12 chars and satisfy:
      serial[0] == serial[11]
      serial[1] == serial[10]  # ASSUMPTION based on diagram
      serial[2] == serial[9]   # ASSUMPTION based on diagram
    Example valid: '475777777574'
    Pattern: A?B??????B?A
    """
    if len(serial) < 12:
        return False
    # ASSUMPTION: positions 0 and 11 must match
    if serial[0] != serial[11]:
        return False
    # ASSUMPTION: positions 2 and 9 must match (the 'B' in A?B??????B?A)
    if serial[2] != serial[9]:
        return False
    # ASSUMPTION: positions 1 and 10 must match
    if serial[1] != serial[10]:
        return False
    return True

def verify_stage2(name: str, serial: str) -> bool:
    """
    Stage 2 registration check.
    Serial must have 'r' at index 3.
    Name must have 'T' at index 12 and 'l' at index 13.
    ASSUMPTION: name length >= 14, serial length >= 4
    """
    if len(serial) < 4:
        return False
    # Serial[3] must be 'r'
    if serial[3] != 'r':
        return False
    if len(name) < 14:
        return False
    # Name positions 12 and 13 must be 'T' and 'l'
    if name[12] != 'T' or name[13] != 'l':
        return False
    return True

def verify(name: str, serial: str) -> bool:
    """
    Full verification combining both stages.
    For stage 1 we use the serial as a 12-char key.
    For stage 2 we use name + serial.
    ASSUMPTION: The crackme has two separate dialogs/checks;
    here we combine both into one verify function.
    A valid input must pass both.
    """
    return verify_stage1(serial) and verify_stage2(name, serial)

def keygen_stage1() -> str:
    """
    Generate a valid 12-char stage-1 serial.
    Pattern: A B C x x x x x x C B A (indices 0..11)
    """
    chars = string.digits + string.ascii_letters
    a = random.choice(chars)
    b = random.choice(chars)
    c = random.choice(chars)
    middle = ''.join(random.choice(chars) for _ in range(6))
    return a + b + c + middle + c + b + a

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Requirements:
      - 12 chars total
      - serial[0]==serial[11], serial[1]==serial[10], serial[2]==serial[9]
      - serial[3] == 'r'
    The name must also satisfy name[12]=='T', name[13]=='l'.
    We generate the serial here; name must be provided correctly by user.
    """
    # ASSUMPTION: serial must be exactly 12 chars to satisfy both checks
    chars = string.ascii_letters + string.digits
    a = random.choice(chars)
    b = random.choice(chars)
    c = random.choice(chars)
    # serial[3] = 'r', positions 4..8 are free (5 chars), then c, b, a
    middle = ''.join(random.choice(chars) for _ in range(5))
    serial = a + b + c + 'r' + middle + c + b + a
    return serial

def keygen_name_for_stage2() -> str:
    """
    Generate a name that satisfies stage 2 name check.
    Name[12]=='T', name[13]=='l'
    ASSUMPTION: first 12 chars and chars after 13 can be anything.
    """
    prefix = ''.join(random.choice(string.ascii_letters) for _ in range(12))
    suffix = ''.join(random.choice(string.ascii_letters) for _ in range(2))
    return prefix + 'Tl' + suffix


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
