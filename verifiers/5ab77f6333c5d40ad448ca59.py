def brute_couple(in_val):
    """
    Brute-force find (A, B) such that the check passes.
    A and B iterate over printable ASCII '!' (0x21) to '~' (0x7E).
    
    The check (from the assembly):
      ebx = in_val * in_val
      ebx += A
      eax = (B - 0x60) * 0x1A
      ebx += eax
      ebx -= 0x60
      result = ebx & 0xFF
      pass if result == 1
    
    Returns (A_byte, B_byte) or (0, 0) on failure.
    """
    in_byte = in_val & 0xFF
    # treat as signed byte
    if in_byte >= 0x80:
        in_byte -= 0x100
    
    a_val = 0x21  # '!'
    while a_val <= 0x7E:
        b_val = 0x21  # '!'
        while b_val <= 0x7E:
            # sign-extend each byte for imul
            iv = in_byte
            av = a_val if a_val < 0x80 else a_val - 0x100
            bv = b_val if b_val < 0x80 else b_val - 0x100
            
            ebx = iv * iv
            ebx += av
            tmp = (bv - 0x60) * 0x1A
            ebx += tmp
            ebx -= 0x60
            
            result = ebx & 0xFF
            if result == 1:
                return (a_val, b_val)
            
            b_val += 1
        a_val += 1
    
    return (0, 0)


def keygen(name):
    """
    Generate a serial for the given name.
    Requirements:
      - Name must be at least 6 characters
      - Name must not contain spaces (0x20)
    
    The serial is built from the first 6 characters of the name.
    For each character c in name[:6]:
      - Call brute_couple(ord(c)) -> (A, B)
      - Serial[i] = A  (low byte of return, stored via stosb)
      - Serial[i+6] = B (high byte of return, stored at [edi+6])
    Result: 12 printable ASCII characters.
    
    The command line format is: name serial
    """
    if len(name) < 6:
        raise ValueError("Name should be at least 6 letters!")
    if ' ' in name:
        raise ValueError("Name should not have spaces in it!")
    
    serial_a = []  # first 6 bytes
    serial_b = []  # next 6 bytes
    
    for i in range(6):
        c = ord(name[i])
        a, b = brute_couple(c)
        if a == 0 and b == 0:
            raise ValueError(f"No password matching character '{name[i]}' (index {i})")
        serial_a.append(a)
        serial_b.append(b)
    
    serial_bytes = serial_a + serial_b
    serial = ''.join(chr(x) for x in serial_bytes)
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    - Name must be >= 6 chars, no spaces
    - Serial must be 12 chars
    - For each of first 6 chars of name:
        A = serial[i], B = serial[i+6]
        The brute_couple condition must hold:
          (name[i]^2 + A + (B-0x60)*0x1A - 0x60) & 0xFF == 1
    """
    if len(name) < 6:
        return False
    if ' ' in name:
        return False
    if len(serial) != 12:
        return False
    
    for i in range(6):
        c = ord(name[i])
        # sign-extend
        if c >= 0x80:
            c -= 0x100
        
        a = ord(serial[i])
        b = ord(serial[i + 6])
        
        av = a if a < 0x80 else a - 0x100
        bv = b if b < 0x80 else b - 0x100
        
        ebx = c * c
        ebx += av
        ebx += (bv - 0x60) * 0x1A
        ebx -= 0x60
        
        if (ebx & 0xFF) != 1:
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
