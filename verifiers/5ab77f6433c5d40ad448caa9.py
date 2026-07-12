# Reverse-engineered keygen for ultrass_2nd_cm by ultrasnord
# Based on solution writeup by yudi
#
# Algorithm (from writeup, name='yudi123', serial='123456789'):
#
# 1. name must be >= 7 characters (button only enabled at len >= 7)
# 2. Let n = len(name)
# 3. Loop: esi goes from 1 to (n-1), i.e. n-1 iterations
#    For each iteration i (esi = i, 1-indexed):
#      a. char_at_i   = name[i]        (second letter on first pass, 0-indexed: name[esi])
#      b. char_at_i_1 = name[i-1]      (first letter on first pass, 0-indexed: name[esi-1])
#      c. eax = ord(char_at_i) + n
#      d. edx = (n + n) * n - n   =>  (2*n)*n - n  = 2*n^2 - n  = n*(2*n - 1)
#         From writeup: LEA EDX,[EBX+EBX]  => edx = 2*n
#                       IMUL EDX,EBX       => edx = 2*n * n = 2*n^2
#                       SUB EDX,EBX        => edx = 2*n^2 - n
#      e. eax = eax XOR edx
#      f. PUSH eax   (save it as 'pushed_val')
#      g. edx = pushed_val  (after XCHG: eax becomes char_at_i_1, edx becomes pushed_val)
#         Actually from writeup:
#           MOVZX EAX, name[esi-1]   => eax = ord(char_at_i_1)
#           POP EDX                  => edx = pushed_val
#           XCHG EAX,EDX            => eax = pushed_val, edx = ord(char_at_i_1)
#           SUB EAX,EDX             => eax = pushed_val - ord(char_at_i_1)
#         (note: writeup says eax=27-79=FFFFFFAE which is 0x27 - 0x79 = -82d,
#          but after XCHG eax=pushed_val=0x27, edx=0x79, so eax = 0x27 - 0x79)
#      h. serial_part = eax (signed 32-bit)
#         then converted to string via IntToStr (Delphi call at 00407B68)
#         then concatenated to result string
#
# ASSUMPTION: The serial is the concatenation of all serial_part integers (as decimal strings)
# ASSUMPTION: The writeup is truncated; only the first iteration is fully shown.
# ASSUMPTION: The final serial is compared directly to user input.
# ASSUMPTION: Arithmetic is done as signed 32-bit integers.

import ctypes

def _to_signed32(n):
    return ctypes.c_int32(n).value

def compute_serial(name):
    n = len(name)
    if n < 7:
        return None  # button not even enabled
    
    serial_parts = []
    # Loop esi from 1 to n-1 (n-1 iterations)
    for esi in range(1, n):  # esi = 1, 2, ..., n-1
        # Step a: take name[esi] (second char on first pass)
        char_i   = ord(name[esi])      # name[esi]
        # Step b: take name[esi-1]
        char_i_1 = ord(name[esi - 1])  # name[esi-1]
        
        # Step c: eax = char_i + n
        eax = char_i + n
        
        # Step d: edx = 2*n*n - n
        edx = 2 * n * n - n
        
        # Step e: eax = eax XOR edx
        eax = eax ^ edx
        pushed_val = eax  # PUSH EAX
        
        # Step g: after MOVZX eax=char_i_1, POP edx=pushed_val, XCHG => eax=pushed_val, edx=char_i_1
        eax = pushed_val
        edx = char_i_1
        
        # SUB EAX, EDX
        eax = eax - edx
        
        # Convert to signed 32-bit
        eax = _to_signed32(eax)
        
        serial_parts.append(str(eax))
    
    return ''.join(serial_parts)

def verify(name, serial):
    expected = compute_serial(name)
    if expected is None:
        return False
    return serial == expected

def keygen(name):
    return compute_serial(name)


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
