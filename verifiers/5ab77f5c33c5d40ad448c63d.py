# Reconstructed from writeup for beboss_keygenme_1
# Algorithm:
# Serial format: PART1-MID-PART2
# PART1 is 21 chars (digits only)
# MID is 17 chars (digits only)
# PART2 is 21 chars (digits only)
# Only digits [0-9] allowed
#
# Checks:
# 1. PART1 == PART2 (the two 21-char parts must be equal)
# 2. Position 14 (1-indexed) of the full concatenated serial (PART1+MID+PART2) must be '7'
#    i.e. PART1[13] == '7'
# 3. Position 44 of the full concatenated serial must be '7'
#    Full serial = PART1(21) + '-'? + MID(17) + '-'? + PART2(21)
#    ASSUMPTION: positions are counted in the combined string PART1+MID+PART2 (no dashes)
#    pos 44 (0-indexed: 43) in PART1+MID+PART2 (59 chars total)
#    PART1 is indices 0-20, MID is indices 21-37, PART2 is indices 38-58
#    index 43 = PART2[5] => PART2[5] == '7', but since PART1==PART2, PART1[5] must also == '7'
#    ASSUMPTION: pos 44 (1-indexed) means index 43 in concatenated 59-char string
# 4. Mid string (MID, 17 chars): position 29 (1-indexed) in full string = MID[7] == '2'
#    ASSUMPTION: offset 0x3A/2 = 29 (1-indexed), i.e. index 28 in full string = MID[7]
#    Actually writeup says 'mid string is 2' so MID contains '2' at some central position
#    0x3A = 58 bytes offset in wide-char string => char index 29 (0-indexed)
#    ASSUMPTION: MID[7] == '2' (the center of 17-char MID string)
#
# Sum checks (CALL 004124B8 converts substring/number, pairs summed):
# The serial is split into segments. From the example:
#   strSerial = %c44%c%c%c%c%c%c%c66%c%c7%c%c%c%c%c5507%c%c%c%c%c  (21 chars)
# Positions in PART1 (0-indexed):
#   [1][2] = '4','4'  -> pair sum = 8
#   [9][10] = '6','6' -> pair sum = 12
#   [16][17] = '5','5'? -> ASSUMPTION based on example 'sum=10'
#   [0] and some other -> ASSUMPTION: sum=7
#
# From example serial: 144111111166117111115...
# PART1 = '144111111166117111115' (21 chars)
# Positions (0-indexed):
#   0: '1'
#   1: '4', 2: '4'  -> 4+4=8 check
#   9: '6', 10: '6' -> 6+6=12 check  
#   13: '7'          -> fixed '7' check
#   15: '1', 16: '1'? or 16:'1',17:'5' -> sum=10? ASSUMPTION
#   Actually from '5507' at positions 16-19: 5+5=10 at pos 16,17? or different
# ASSUMPTION: the exact pair positions are not fully clear from writeup
# Using the example string as template: PART1 positions:
#   pairs for sum=8:  positions (1,2)
#   pairs for sum=12: positions (9,10)
#   pairs for sum=10: positions (16,17) -- '55' from '5507'
#   pairs for sum=7:  positions (0, some_other) -- ASSUMPTION
# Fixed positions: PART1[13]='7', PART1[5]='7' (from pos44 check, ASSUMPTION)
# MID[7]='2'

import random

def build_part1(a=4, b=4, c=6, d=6, e=5, f=5, pos0=1):
    """
    Build PART1 (21 digits) satisfying:
    - [1]+[2] == 8  (use a, b)
    - [9]+[10] == 12 (use c, d)
    - [16]+[17] == 10 (use e, f)  # ASSUMPTION
    - [13] == '7' (fixed)
    - [5] == '7'  # ASSUMPTION from pos44 check
    - [0]+[?] == 7  # ASSUMPTION: pair at positions (0, 20) sum=7
    """
    # ASSUMPTION: sum=7 check uses positions 0 and 20
    g = 7 - pos0
    if g < 0 or g > 9:
        pos0 = 3
        g = 4
    part = ['1'] * 21
    part[0] = str(pos0)
    part[1] = str(a)
    part[2] = str(b)
    # part[3],[4] free
    part[5] = '7'  # ASSUMPTION for pos44 check
    # part[6..8] free
    part[9]  = str(c)
    part[10] = str(d)
    # part[11],[12] free
    part[13] = '7'  # pos14 check
    # part[14],[15] free
    part[16] = str(e)
    part[17] = str(f)
    # part[18],[19] free
    part[20] = str(g)
    return ''.join(part)

def build_mid():
    """
    MID is 17 digits, with MID[7]=='2' (center char)
    ASSUMPTION: rest can be arbitrary digits
    """
    mid = list('11111112111111111')  # 17 chars, index 7 = '2'
    return ''.join(mid)

def keygen(name=None):
    # name is not used in the algorithm (serial-only keygen)
    # ASSUMPTION: no name dependency was described
    a, b = random.choice([(1,7),(2,6),(3,5),(4,4),(0,8)])
    # ensure digits 0-9
    c, d = random.choice([(3,9),(4,8),(5,7),(6,6),(7,5),(9,3)])
    e, f = random.choice([(1,9),(2,8),(3,7),(4,6),(5,5),(6,4)])
    pos0 = random.randint(0, 7)
    g = 7 - pos0
    part1 = build_part1(a=a, b=b, c=c, d=d, e=e, f=f, pos0=pos0)
    mid = build_mid()
    part2 = part1  # PART1 == PART2
    serial = part1 + '-' + mid + '-' + part2
    return serial

def verify(name, serial):
    """
    Verify a serial according to the reconstructed algorithm.
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    part1, mid, part2 = parts
    # Length checks
    if len(part1) != 21 or len(mid) != 17 or len(part2) != 21:
        return False
    # Only digits
    if not (part1.isdigit() and mid.isdigit() and part2.isdigit()):
        return False
    # Check 1: PART1 == PART2
    if part1 != part2:
        return False
    # Check 2: 14th position (1-indexed) in PART1 == '7'
    if part1[13] != '7':
        return False
    # Check 3: 44th position (1-indexed) in full string PART1+MID+PART2 == '7'
    full = part1 + mid + part2
    if full[43] != '7':  # ASSUMPTION: 0-indexed pos 43
        return False
    # Check 4: MID[7] == '2' (center of 17-char mid string)
    if mid[7] != '2':  # ASSUMPTION
        return False
    # Sum checks on PART1 (ASSUMPTION: pair positions as derived from example)
    # Pair 1: positions 1,2 must sum to 8
    if int(part1[1]) + int(part1[2]) != 8:
        return False
    # Pair 2: positions 9,10 must sum to 12
    if int(part1[9]) + int(part1[10]) != 12:
        return False
    # Pair 3: positions 16,17 must sum to 10  # ASSUMPTION
    if int(part1[16]) + int(part1[17]) != 10:
        return False
    # Pair 4: positions 0,20 must sum to 7  # ASSUMPTION
    if int(part1[0]) + int(part1[20]) != 7:
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
