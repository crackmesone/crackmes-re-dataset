# Reverse-engineered keygen for excrek's crackme #1
# Based on tut.txt writeup

def encrypt_name(name):
    """
    Encrypt name using ADD 8 + index / SUB 8 - index depending on char value.
    If char > 0x5F: new_char = char - 8 - index (1-based)
    If char <= 0x5F: new_char = char + 8 + index (1-based)
    index is 1-based (EDI starts at 1, increments)
    """
    result = []
    for i, ch in enumerate(name):
        idx = i + 1  # 1-based index
        b = ord(ch)
        if b > 0x5F:
            new_b = (b - 8 - idx) & 0xFF
        else:
            new_b = (b + 8 + idx) & 0xFF
        result.append(new_b)
    return bytes(result)

def sum_chars(data):
    """
    Sum all byte values of a string/bytes.
    """
    return sum(data)

def compute_code1(name):
    """
    Code1 is the encrypted name as a string (raw bytes interpreted as chars).
    """
    enc = encrypt_name(name)
    return ''.join(chr(b) for b in enc)

def compute_code2(name):
    """
    Code2:
    1. Decrypt the hardcoded encrypted string 'JejbWYRbSS[' -> 'Soundgarden'
       (this is a fixed internal reference string, not user-dependent for code2)
    2. Sum all chars of 'Soundgarden'
    3. Multiply sum by (name[4] - 0x3A)
    4. Print as integer -> Code2
    
    Wait: re-reading the writeup more carefully:
    The sum is of the decrypted reference string 'Soundgarden',
    then multiplied by (name[4] - 0x3A).
    But the example: name=eXcreK, Code2=49278
    Let's verify: sum('Soundgarden') = S+o+u+n+d+g+a+r+d+e+n
    = 83+111+117+110+100+103+97+114+100+101+110 = 1146
    name[4] = 'e' = 0x65, 0x65 - 0x3A = 43
    1146 * 43 = 49278  -- matches!
    """
    # ASSUMPTION: The reference string is always 'Soundgarden' (hardcoded in binary)
    reference = 'Soundgarden'
    s = sum(ord(c) for c in reference)
    # name[4] is 5th character (0-indexed)
    multiplier = ord(name[4]) - 0x3A
    return s * multiplier

def compute_code3(name):
    """
    Code3 = 'GrnG-' + str(code2_sum + encrypted_name_sum_product)
    
    From the writeup:
    - sum of encrypted name chars -> 'buffer'
    - old sum (same as code2 numerator = sum of reference * multiplier) -> code2
    # ASSUMPTION: The assembly reuses the same sum*multiplier pattern for the encrypted name too
    # Reading again: 
    #   'last code is generated from the above sum + a new sum of the encrypted text'
    #   The snippet sums the encrypted name chars (buffer), then:
    #   EDX = name[4] - 0x3A
    #   IMUL EDX  (old sum here - this is the sum of encrypted name * multiplier)
    #   POP EDX   (buffer = sum of reference string chars * multiplier = code2)
    #   ADD EDX, EAX  -> code3_val = code2 + (enc_sum * multiplier)
    # Verify: enc = encrypt_name('eXcreK')
    # code2 = 49278
    # enc_sum = sum of encrypted bytes
    # enc_sum * multiplier + code2 = 49835
    # enc_sum * multiplier = 49835 - 49278 = 557
    # multiplier = 43, enc_sum = 557/43 = 12.95... not integer
    # ASSUMPTION: maybe 'old sum' in pop EDX is the sum of reference string (not multiplied)
    # 1146 + enc_sum * 43 = 49835 -> enc_sum*43 = 48689 -> enc_sum = 1132.3... no
    # ASSUMPTION: maybe it's enc_sum + code2 directly (no extra multiply for code3)
    # enc_sum + code2 = 49835 -> enc_sum = 49835 - 49278 = 557
    # Let's check: encrypt 'eXcreK'
    # e=0x65<=5F? no, 0x65>0x5F: 0x65-8-1=0x5C=92
    # X=0x58<=5F: 0x58+8+2=0x62=98
    # c=0x63>5F: 0x63-8-3=0x58=88
    # r=0x72>5F: 0x72-8-4=0x66=102
    # e=0x65>5F: 0x65-8-5=0x58=88
    # K=0x4B<=5F: 0x4B+8+6=0x59=89
    # enc = [92,98,88,102,88,89] sum=557  matches!
    # So Code3_val = code2 + enc_name_char_sum
    """
    enc = encrypt_name(name)
    enc_sum = sum(enc)
    code2 = compute_code2(name)
    code3_val = code2 + enc_sum
    return 'GrnG-' + str(code3_val)

def verify(name, serial):
    """
    Verify name and serial (serial should be a tuple/list of (code1, code2, code3)
    or a single string. We'll accept a dict or tuple.
    """
    if len(name) <= 5 or len(name) >= 12:
        return False
    expected_code1 = compute_code1(name)
    expected_code2 = compute_code2(name)
    expected_code3 = compute_code3(name)
    # serial can be a tuple (code1, code2, code3)
    if isinstance(serial, (list, tuple)) and len(serial) == 3:
        return (serial[0] == expected_code1 and
                str(serial[1]) == str(expected_code2) and
                serial[2] == expected_code3)
    return False

def keygen(name):
    """
    Generate the three codes for a given name.
    Returns (code1, code2, code3)
    """
    if len(name) <= 5 or len(name) >= 12:
        raise ValueError('Name must be >5 and <12 characters')
    code1 = compute_code1(name)
    code2 = compute_code2(name)
    code3 = compute_code3(name)
    return (code1, str(code2), code3)


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
