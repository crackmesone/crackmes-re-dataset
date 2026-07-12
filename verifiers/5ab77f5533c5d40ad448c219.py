# Reconstruction of oliver039s_first_crackme key validation algorithm
# Based on the writeup by 'nh' which describes the keygen algorithm most completely.
#
# Summary of algorithm (from nh's writeup):
# Name must be >= 6 chars.
#
# Step 1: For each character in the name (reversed, excluding first two chars?),
#   write its ordinal value as decimal, but each digit doubled:
#   e.g. char 'g' = ord 103 -> '110033' (each digit written twice)
#   This forms s0.
#
# Step 2: Convert each character (forward) to decimal normally:
#   e.g. 'g'=103 -> '103', 'f'=102 -> '102'
#   This forms s1 (concatenated decimal values of each char).
#
# Step 3 (5th cycle): Take every 3rd character from s1 (starting at index 0,3,6,...):
#   forms s2.
#
# Step 4 (last cycle): For each position i in s2,
#   result_digit = abs(int(s2[i]) - int(s1[len(name)-2 + i])) -- ASSUMPTION: subtract char at (len-2) offset of s1
#   Actually from example: name='abcdefg' (len=7)
#   s1 starts with ordinals of chars in order: a=97,b=98,c=99,d=100,e=101,f=102,g=103
#   s1 = '979899100101102103'
#   s2 = every 3rd char of s1: s1[0],s1[3],s1[6],... = '9','1','0','1','1','2'
#   From example output for 'Pincopall' -> '431114434654410'
#   and 'piopiopio' -> '555544434343554'
#
# The writeup is not fully precise about the subtraction step.
# ASSUMPTION: Based on nh's description:
#   - s1 = concatenation of decimal(ord(c)) for c in name (forward)
#   - s2 = s1[0::3] (every 3rd char of s1)
#   - The key is formed by: for each position i in s2,
#       key[i] = str(abs(int(s2[i]) - int(s1[len(name)-2+i]))) last digit + '0'
#   But the example outputs don't match this cleanly.
#
# Let's try to reverse-engineer from the known pairs:
# 'Pincopall' -> '431114434654410'
# 'piopiopio' -> '555544434343554'
#
# For 'Pincopall' (len=9):
#   ord values: P=80,i=105,n=110,c=99,o=111,p=112,a=97,l=108,l=108
#   s1 = '80105110991111129710810880105110991111129710810'
#   Wait, s1 = ''.join(str(ord(c)) for c in 'Pincopall')
#      = '80' + '105' + '110' + '99' + '111' + '112' + '97' + '108' + '108'
#      = '801051109911111297108108'
#   s2 = s1[0::3] = '8','0','5','1','9','1','1','2','7'
#   = '805191127' (9 chars, matches len(name)=9)
#
# ASSUMPTION: The last cycle subtracts s2[i] from s1[len(name)-2+i] with absolute value + '0' offset
# Let's check: len=9, so s1[7], s1[8], s1[9], ...
#   s1[7]='0', s1[8]='5', s1[9]='1', s1[10]='1', s1[11]='0', s1[12]='9', s1[13]='9', s1[14]='1'
#   result = abs(int(s2[i]) - int(s1[len-2+i])) ... this doesn't yield '431114434654410'
#
# ASSUMPTION: The algorithm description is incomplete. Implementing best-guess from nh's ASM keygen.
# The ASM keygen does:
# 1. Reverse chars of name (skipping first two? actually from nm+3 offset with ecx=len-1)
#    Each char byte -> doubled-digit decimal (hex2dec1): e.g. 103 -> '110033'
#    stored in buffer at nm+2+100h
# 2. Forward chars -> normal decimal (hex2dec): e.g. 103 -> '103'
#    stored appended in nm+2+200h area
# 3. Fifth cycle: from the forward-decimal string, take every 3rd char -> nm+2+100h area (overwriting?)
# 4. Last cycle: subtract and produce final key
#
# Given complexity and gaps, implementing a best-effort version:

def keygen(name):
    if len(name) < 6:
        raise ValueError("Name must be at least 6 characters")
    
    # Step 1: reversed chars (len-1 of them, skipping first?), each digit doubled
    # From ASM: ecx = len(name), si=nm+3 (char index 1 onward), bp=nm+2+len (last char)
    # Actually nm+1 = length byte, nm+2 = first char in Pascal string
    # si starts at nm+3 = 3rd char (index 1 in 0-based), bp starts at nm+2+len-1 = last char
    # Loop len-1 times: reads reversed char (from end), doubled-decimal, and forward char
    # ASSUMPTION: we process len(name)-1 characters
    
    n = len(name)
    
    # Build doubled-decimal of reversed chars (name[n-1], name[n-2], ..., name[1])
    doubled_buf = []
    for i in range(n-1, 0, -1):
        c = ord(name[i])
        s = str(c)
        doubled = ''.join(d+d for d in s)  # each digit doubled
        doubled_buf.append(doubled)
    s0 = ''.join(doubled_buf)
    
    # Build normal decimal of forward chars (name[1], name[2], ..., name[n-1])
    forward_buf = []
    for i in range(1, n):
        c = ord(name[i])
        forward_buf.append(str(c))
    s1 = ''.join(forward_buf)
    
    # ASSUMPTION: 5th cycle takes every 3rd char of s1 (indices 2,5,8,...) based on 'add ebx,3' starting at 3
    # ebx starts at 3 and indexes s1 with [edx+ebx-1] = s1[ebx-1]
    # so indices 2, 5, 8, ... (0-based)
    s2 = s1[2::3]
    
    # Last cycle: len(name) iterations
    # s1 offset: nm+2+300h -> relative to name, this is the doubled buffer area
    # esi starts at nm+2+300h + len - 2
    # ASSUMPTION: uses s0 reversed, starting at offset n-2
    # For each position i: result = abs(int(s2[i]) - int(s0_char)) % 10 + ord('0')
    # From ASM: sub eax,ebx; cdq; xor al,dl; sub al,dl -> abs value; add al,'0'
    
    # ASSUMPTION: s0 index starts at (n-2) from end of s0
    result = []
    for i in range(n):
        if i >= len(s2) or (n - 2 + i) >= len(s0):
            break
        a = int(s2[i])
        b = int(s0[n - 2 + i])
        diff = a - b
        # abs via cdq/xor/sub pattern
        r = diff if diff >= 0 else -diff
        result.append(str(r % 10))
    
    serial = ''.join(result)
    return serial


def verify(name, serial):
    """Verify name/serial pair."""
    if len(name) < 6:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
    return serial == expected


# Quick sanity check with known values from writeup
# 'Pincopall' -> '431114434654410'
# 'piopiopio' -> '555544434343554'

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
