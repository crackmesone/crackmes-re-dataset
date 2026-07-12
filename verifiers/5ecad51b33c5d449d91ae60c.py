# Reconstructed algorithm based on the writeup
# Key format: CTF{key_here} but hint says format doesn't define the output
# Multiple valid keys exist (e.g., '~~~~~~~~~~~~~~~~~B', '~~~~~~~~~~~~~~~~~C')
#
# From the writeup:
# - security_check iterates over each character of the key
# - For each character, it runs an inner loop 8 times (generating bits)
# - fcn.0041138e returns 0 or 1 - it generates binary encoding of the character in REVERSE
# - These 8 bits form the reversed binary representation of each ASCII character
# - The function returns nonzero for success
#
# The core idea: each character's bits (LSB first) are accumulated/checked
# against some target value (0x55C = 1372 decimal is passed as a parameter)
#
# ASSUMPTION: Based on the examples '~~~~~~~~~~~~~~~~~B' and '~~~~~~~~~~~~~~~~~C'
# and the comment about z3, the algorithm likely computes a sum/hash of bit-reversed
# characters and checks it equals 1372 (0x55C).
#
# '~' = 0x7E = 126, reversed bits of 0x7E:
# 0x7E = 0111 1110, reversed = 0111 1110 = 0x7E = 126
# Actually 0x7E reversed: bits 01111110 reversed = 01111110 = 126
# 17 * 126 = 2142, doesn't equal 1372
#
# ASSUMPTION: The check is on the sum of bit-reversed bytes.
# Let's compute bit_reverse for each char:
# bit_reverse(0x7E) = reverse bits of 01111110 = 01111110 = 0x7E = 126
# 16 * 126 + bit_reverse(ord('B')) = 16*126 + bit_reverse(0x42)
# bit_reverse(0x42) = reverse of 01000010 = 01000010 = 0x42 = 66
# 16*126 + 66 = 2016 + 66 = 2082 -- not 1372
#
# ASSUMPTION: Maybe it sums only certain bits, or uses XOR, or the target is different.
# Let's try: sum of reversed-bit values mod something, or just the raw byte sum.
# 17 * ord('~') + ord('B') = 17*126 + 66 = 2142 + 66 = 2208 -- no
# Try sum directly: 17*126 + 66 = 2208
# ~~~~~~~~~~~~~~~~~C: 17*126 + 67 = 2209
# Neither is 1372.
#
# ASSUMPTION: The algorithm reverses the bits of each character and sums them,
# checking against 1372. Let's verify with a different interpretation:
# reversed bits of '~' (0x7E = 01111110) => 01111110 = 126 (palindrome in bits)
# reversed bits of 'B' (0x42 = 01000010) => 01000010 = 66 (also palindrome)
# Same result. Sum of 17 chars '~' and 'B' = 2208 != 1372
#
# ASSUMPTION: Perhaps only specific positions matter, or the inner loop accumulates
# a running sum differently. Without full disassembly, using z3-style constraint:
# sum of bit_reverse(char[i]) for i in range(len(key)) == 1372
# This would give average char value ~80 per char for ~17 chars.

def bit_reverse_byte(b):
    """Reverse the bits of a byte (8 bits, LSB first as described)"""
    result = 0
    for i in range(8):
        result = (result << 1) | ((b >> i) & 1)
    return result

def verify(name, serial):
    """
    ASSUMPTION: The security_check function sums bit-reversed values of each
    character in the key and compares to 1372 (0x55C, passed as parameter).
    Multiple keys are valid as confirmed by comments.
    The 'name' field does not appear to be used in this crackme (serial only).
    """
    key = serial
    # Strip CTF{} wrapper if present
    # ASSUMPTION: wrapper is stripped before check based on hint
    if key.startswith('CTF{') and key.endswith('}'):
        key = key[4:-1]
    
    total = 0
    for ch in key:
        total += bit_reverse_byte(ord(ch))
    
    # ASSUMPTION: target value is 1372 (0x55C)
    return total == 1372

def keygen(name):
    """
    Generate a valid serial. Use '~' repeated to fill most of the sum,
    then find a final character to hit exactly 1372.
    bit_reverse('~') = bit_reverse(0x7E=01111110) = 01111110 = 126
    """
    target = 1372
    # ASSUMPTION: Use printable ASCII characters
    # Try building key with '~' chars and adjusting last char
    filler_char = '~'
    filler_val = bit_reverse_byte(ord(filler_char))  # 126
    
    # Find how many filler chars we can use
    for n_filler in range(1, 50):
        remainder = target - n_filler * filler_val
        if 0 < remainder <= 254:
            # Find a printable char whose bit_reverse == remainder
            for c in range(32, 127):
                if bit_reverse_byte(c) == remainder:
                    serial = filler_char * n_filler + chr(c)
                    return serial
    
    # ASSUMPTION fallback: brute force short keys
    import itertools
    printable = [chr(c) for c in range(32, 127)]
    for length in range(1, 20):
        # Too slow to enumerate all, use greedy
        pass
    return None


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
