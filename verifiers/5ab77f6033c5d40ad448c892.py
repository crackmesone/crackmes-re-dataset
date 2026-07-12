# Reconstructed from solution writeup (IRCxB0T's keyGen.php)
# The crackme has 4 numeric input fields, each exactly 6 characters.
# Rules derived from the writeup:
#   input1: 6-digit number, digit at index 1 must be '9', digit at index 3 must be '7'
#   input2: 6-digit number in range [800000, 899999]
#   input4: 6-digit number <= 500200 (0x7A1E8), digit at index 3 must be '2', digit at index 5 must be '0'
#   input3 = input1 + input4  (must also be 6 digits)
#   Serial format: 'input1-input2-input3-input4'
#
# The 'name' field is not used in the algorithm (no name-based check described).

import random

def _make_input1():
    # 6-digit, index 1 == '9', index 3 == '7'
    # Range hinted: 190700 - 499799 with those digits forced
    while True:
        n = random.randint(100000, 499999)
        s = list(str(n).zfill(6))
        s[1] = '9'
        s[3] = '7'
        result = int(''.join(s))
        if 100000 <= result <= 999999:
            return result

def _make_input2():
    return random.randint(800000, 899999)

def _make_input4():
    # 6-digit, index 3 == '2', index 5 == '0', value <= 500200
    while True:
        n = random.randint(100000, 500200)
        s = list(str(n).zfill(6))
        s[3] = '2'
        s[5] = '0'
        result = int(''.join(s))
        if 100000 <= result <= 500200:
            return result

def keygen(name):
    """Generate a valid serial. name is ignored (no name-based check described)."""
    input1 = _make_input1()
    input2 = _make_input2()
    input4 = _make_input4()
    input3 = input1 + input4
    return f"{input1}-{input2}-{input3}-{input4}"

def verify(name, serial):
    """Verify a serial string against the known constraints."""
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    
    # All parts must be exactly 6 characters
    for p in parts:
        if len(p) != 6:
            return False
    
    try:
        input1 = int(parts[0])
        input2 = int(parts[1])
        input3 = int(parts[2])
        input4 = int(parts[3])
    except ValueError:
        return False
    
    s1 = parts[0]
    s2 = parts[1]
    s3 = parts[2]
    s4 = parts[3]
    
    # input1 checks: index 1 == '9', index 3 == '7'
    if s1[1] != '9':
        return False
    if s1[3] != '7':
        return False
    
    # input2 checks: 6 digits (already checked by length)
    # ASSUMPTION: input2 range 800000-899999 based on PHP keygen, but the
    # writeup does not explicitly confirm an upper-bound check for input2 in asm
    # We only enforce 6-digit numeric.
    
    # input4 checks: value <= 500200, index 3 == '2', index 5 == '0'
    if input4 > 500200:
        return False
    if s4[3] != '2':
        return False
    if s4[5] != '0':
        return False
    
    # input3 == input1 + input4
    if input3 != input1 + input4:
        return False
    
    # input3 must be 6 characters (already checked, but verify value fits)
    if not (100000 <= input3 <= 999999):
        return False
    
    return True


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
