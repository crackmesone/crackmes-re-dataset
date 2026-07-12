import ctypes

def ror32(value, shift):
    """Rotate right 32-bit value by shift bits."""
    value = value & 0xFFFFFFFF
    shift = shift & 31
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF

def compute_part(name, multiplier):
    """
    For each character in name (skipping spaces),
    compute: sum of ROR(ord(c) * multiplier, 0x13) for c in name
    Result is a 32-bit unsigned integer.
    """
    acc = 0
    for c in name:
        if c == ' ':
            continue
        buf = (ord(c) * multiplier) & 0xFFFFFFFF
        buf = ror32(buf, 0x13)
        acc = (acc + buf) & 0xFFFFFFFF
    return acc

def keygen(name):
    """
    Generate serial for given name.
    Name must be at least 4 characters.
    
    Algorithm (from solution 3 / keygen.cpp):
      Start with intSecondPart = 0x401284
      For i in range(3, -1, -1):
          intFirstPart = compute_part(name, intSecondPart)
          dwSerial[i] = intSecondPart = intFirstPart
      Serial = "%08X-%08X-%08X-%08X" % (dwSerial[0], dwSerial[1], dwSerial[2], dwSerial[3])
    
    Note: 0x401284 is the 'magic constant' used when NOT under debugger.
    Under debugger the constant is 0x4012BE (anti-debug trick).
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters.")
    
    INIT_VALUE = 0x401284  # ASSUMPTION: no debugger present; under debugger it would be 0x4012BE
    
    dwSerial = [0, 0, 0, 0]
    second_part = INIT_VALUE
    
    for i in range(3, -1, -1):
        first_part = compute_part(name, second_part)
        dwSerial[i] = first_part
        second_part = first_part
    
    serial = "%08X-%08X-%08X-%08X" % (dwSerial[0], dwSerial[1], dwSerial[2], dwSerial[3])
    return serial

def verify(name, serial):
    """
    Verify name/serial pair.
    
    Serial format: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    - Total length must be 35 (0x23)
    - Each character must be hex [0-9A-Fa-f] or '-' at positions 8,17,26 (1-indexed: 9,18,27)
    - Name must be >= 4 chars
    
    Validation logic:
      Parse serial into 4 hex parts: s1, s2, s3, s4
      Check 1: compute_part(name, s2) == s1  (i.e. ebx = s1, sum should equal s1)
      Check 2: compute_part(name, s3) == s2
      Check 3: compute_part(name, s4) == s3
      Check 4: compute_part(name, 0x401284) == s4
    
    From solution 2/3: the check is ebx -= eax for each char, then ebx must be zero.
    i.e. firstPart == sum_of_ror_terms, which means compute_part(name, storedValue) == firstPart.
    """
    if len(name) < 4:
        return False
    
    serial = serial.upper()
    
    # Check length
    if len(serial) != 35:
        return False
    
    # Check characters and '-' positions
    valid_hex = set('0123456789ABCDEF')
    for idx, ch in enumerate(serial):
        # 0-indexed positions 8, 17, 26 should be '-'
        if idx in (8, 17, 26):
            if ch != '-':
                return False
        else:
            if ch not in valid_hex:
                return False
    
    # Parse the 4 parts
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    if any(len(p) != 8 for p in parts):
        return False
    
    try:
        s = [int(p, 16) for p in parts]
    except ValueError:
        return False
    
    INIT_VALUE = 0x401284  # ASSUMPTION: no debugger present
    
    # Check 1: compute_part(name, s[1]) should equal s[0]
    if compute_part(name, s[1]) != s[0]:
        return False
    # Check 2: compute_part(name, s[2]) should equal s[1]
    if compute_part(name, s[2]) != s[1]:
        return False
    # Check 3: compute_part(name, s[3]) should equal s[2]
    if compute_part(name, s[3]) != s[2]:
        return False
    # Check 4: compute_part(name, INIT_VALUE) should equal s[3]
    if compute_part(name, INIT_VALUE) != s[3]:
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
