import struct

def compute_checksum(name):
    """
    Compute the checksum 'c' from the name string.
    For each consecutive pair of characters, shift left by the ordinal of the second,
    take absolute value, and sum. Then XOR with the length of the name.
    """
    c = 0
    ns = name
    for i in range(len(ns) - 1):
        a = ord(ns[i])
        b = ord(ns[i + 1])
        # Delphi integer: 32-bit signed, simulate with Python
        a = (a << b) & 0xFFFFFFFF
        # Treat as signed 32-bit
        if a >= 0x80000000:
            a = a - 0x100000000
        if a < 0:
            a = -a
        c = c + a
    # c XOR length
    c = c ^ len(ns)
    # Keep as 32-bit signed
    c = c & 0xFFFFFFFF
    if c >= 0x80000000:
        c = c - 0x100000000
    return c


def byte2hex(a):
    """Convert byte value to 2-char hex string (uppercase)."""
    return '%02X' % (a & 0xFF)


def compute_sst(a_val):
    """
    Simulate the Delphi hex conversion loop:
    repeat
      Byte2Hex(a, @hx[1]);
      sst := hx[2] + sst;  -- hx[2] is the low nibble hex char
      a := a shr 4;
    until a = 0;
    """
    # ASSUMPTION: Byte2Hex writes two hex chars; hx[1] is high nibble char, hx[2] is low nibble char
    # The loop uses unsigned right shift (shr)
    a = a_val & 0xFFFFFFFF  # treat as unsigned for shr
    sst = ''
    while True:
        byte_val = a & 0xFF
        hx = '%02X' % byte_val
        # hx[1] in Delphi 1-indexed = hx[0] in Python (high nibble)
        # hx[2] in Delphi 1-indexed = hx[1] in Python (low nibble)
        sst = hx[1] + sst  # prepend low nibble char
        a = a >> 4
        if a == 0:
            break
    return sst


def generate_serial(name):
    """
    Generate the serial for a given name.
    Returns None if the name length is invalid or if algo produces weak result.
    """
    ns = name
    if len(ns) < 5 or len(ns) > 20:
        return None  # length must be > 5 and < 21 (5 <= len <= 20 based on > 4 and < 21)
    
    c = compute_checksum(ns)
    
    ss = ''
    for i in range(len(ns)):
        a = ord(ns[i])
        # a := (a * c) shl 3 xor $19
        # All arithmetic in 32-bit signed Delphi integers
        a32 = (a * c) & 0xFFFFFFFF
        a32 = (a32 << 3) & 0xFFFFFFFF
        a32 = a32 ^ 0x19
        # Treat as signed
        if a32 >= 0x80000000:
            a32 = a32 - 0x100000000
        
        # a := ((a*a) shl 4 xor $14) shl 5
        a32b = (a32 * a32) & 0xFFFFFFFF
        a32b = (a32b << 4) & 0xFFFFFFFF
        a32b = a32b ^ 0x14
        a32b = (a32b << 5) & 0xFFFFFFFF
        if a32b >= 0x80000000:
            a32b = a32b - 0x100000000
        
        # a := (a shl c) * $7C3
        # ASSUMPTION: c is used as shift amount; in Delphi shl uses only low 5 bits for 32-bit
        shift_amount = c & 0x1F  # low 5 bits
        a32c = (a32b << shift_amount) & 0xFFFFFFFF
        a32c = (a32c * 0x7C3) & 0xFFFFFFFF
        if a32c >= 0x80000000:
            a32c = a32c - 0x100000000
        if a32c < 0:
            a32c = -a32c
        # Make unsigned
        a32c = a32c & 0xFFFFFFFF
        
        sst = compute_sst(a32c)
        
        if len(sst) < 4:
            return None  # weak algo
        
        # ss := ss + 'F' + sst[1] + sst[2] + sst[4]  (Delphi 1-indexed)
        ss = ss + 'F' + sst[0] + sst[1] + sst[3]
    
    return ss


def verify(name, serial):
    """
    Verify that serial matches the expected serial for the given name.
    Also checks the keyfile content requirement (name + serial reversed),
    but here we only check the serial string match.
    """
    if len(name) < 5 or len(name) > 20:
        return False
    expected = generate_serial(name)
    if expected is None:
        return False
    return serial == expected


def keygen(name):
    """
    Generate a valid serial for the given name.
    Returns None if generation fails.
    """
    if len(name) < 5 or len(name) > 20:
        return None
    return generate_serial(name)



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
