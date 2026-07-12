# Reconstruction of Sunny KeygenMe #1 by ManSun
# Based on solution writeups by Amenesia and crackmes.de
#
# The algorithm has two parts:
# 1. A 'Check' key (dummy - no real registration path found)
# 2. An 'Exit' key (real check - described in writeup)
#
# From the writeup (Solution 2), the real key algorithm when Exit is clicked:
#
# Step 1: Compute a value from the name using a lookup table
#   table = '@!FUCKOFFHbvnc90' (at DS:[4046F6])
#   result starts at 0
#   constant = 0x0010F9A8
#   modulus = 0xEE6B2800
#
#   for i in range(len(name)):
#       table_char = table[i % len(table)]
#       name_char  = name[i]
#       result = (result + table_char * name_char + constant) % modulus  # ASSUMPTION: ADD EDI is cumulative result
#
# Actually re-reading more carefully:
#   edi starts at 0 (constant 0x0010F9A8 is added each iteration)
#   eax = table[esi % len(table)]
#   edx = name[ebx + esi]   (ebx = offset to name buffer)
#   eax = eax * edx
#   eax = eax + edi          (edi is running accumulator)
#   (edx:eax) = eax / 0xEE6B2800  -> edi = remainder
#   esi += 1
#   loop while esi < name_length
#
# ASSUMPTION: The constant 0x0010F9A8 is added to eax before division
# (writeup says 'Constant: 0010F9A8h' next to ADD EAX,EDI line - but EDI is the running total)
# Let me re-read: ADD EAX,EDI  where EDI starts as some constant?
# Actually from code: MOV EDI,EE6B2800 then DIV EDI, then MOV EDI,EDX (remainder)
# So EDI is reused - initially it must be 0x0010F9A8 (the constant comment)
# ASSUMPTION: edi initial value = 0x0010F9A8

LOOKUP_TABLE = b'@!FUCKOFFHbvnc90'
INITIAL_EDI = 0x0010F9A8
MODULUS = 0xEE6B2800

def compute_step1(name):
    """Compute the intermediate value from the name."""
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    edi = INITIAL_EDI
    tlen = len(LOOKUP_TABLE)
    for i in range(len(name_bytes)):
        table_byte = LOOKUP_TABLE[i % tlen]
        name_byte = name_bytes[i]
        eax = table_byte * name_byte
        eax = (eax + edi) & 0xFFFFFFFF
        edi = eax % MODULUS
    return edi

def compute_serial(name):
    """Convert the computed value to the serial string following the writeup."""
    # Step 1: get the raw numeric result
    raw = compute_step1(name)
    # Convert to decimal string
    decimal_str = str(raw)
    
    # Step 2: The serial must have length >= 5
    if len(decimal_str) < 5:
        # ASSUMPTION: if too short, not a valid name
        return None
    
    # Step 3: sum all digits
    digit_sum = sum(int(c) for c in decimal_str)
    
    # Step 4: remainder = digit_sum % 0x7B (123)
    remainder = digit_sum % 0x7B
    
    # ASSUMPTION: The serial is constructed from the decimal_str with further
    # transformations not fully described in the truncated writeup.
    # The example shows name='Harley' -> intermediate result 0x119913 = 1153299
    # digit_sum = 1+1+5+3+2+9+9 = 30, 30 % 123 = 30
    # The writeup is truncated so we cannot determine the full serial construction.
    # We return the decimal string as a best-guess serial.
    # ASSUMPTION: serial = decimal_str (the sprintf'd decimal value)
    return decimal_str

def verify(name, serial):
    """Verify name/serial pair."""
    expected = compute_serial(name)
    if expected is None:
        return False
    # ASSUMPTION: direct string comparison
    return serial.strip() == expected

def keygen(name):
    """Generate serial for a given name."""
    serial = compute_serial(name)
    return serial if serial is not None else ''


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
