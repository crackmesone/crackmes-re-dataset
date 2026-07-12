# Reconstructed keygen for falcon1crackme2
# Based on the keygen.asm writeup
# The algorithm processes each character of the username and produces
# a numeric string (base-10 digits, possibly hex-style) per character,
# then concatenates them.

def char_to_keypart(c):
    """
    From keygen.asm __key block:
      ebx = ord(c) - 0x21
      ebx = ebx * 2          (add ebx, ebx)
      eax = ebx
      edx:eax = eax (signed) / 0x5A  -> quotient in eax, remainder in edx
      ebx = edx - 1           (mov ebx, edx; dec ebx)
      eax = ebx               (the value to convert to digits)
    Then convert eax to decimal digits stored backwards (high address first),
    each digit: dl = (eax % 10) + 0x30, if dl >= 0x3A then dl += 7
    (that makes it uppercase hex-like for digits > 9, but since max value
     is bounded, likely stays decimal)
    
    After digit generation, fuck_case is called which appears to be
    a string-to-int (atoi-style) routine - but in context it's called
    on the generated digits, and dl is stored as a prefix/separator byte.
    # ASSUMPTION: fuck_case call result (dl) is a separator or prefix char;
    # we skip it as its exact role is unclear from truncated writeup.
    """
    val = ord(c) - 0x21
    val = val * 2
    # signed division by 0x5A
    import ctypes
    # Python integer division matching x86 idiv (truncation toward zero)
    divisor = 0x5A
    # treat val as signed 32-bit
    val_s = ctypes.c_int32(val).value
    quotient = int(val_s / divisor)  # truncate toward zero
    remainder = val_s - quotient * divisor
    ebx = remainder - 1  # dec ebx after mov ebx, edx
    eax = ebx
    # Convert eax to digit string (base 10, stored high-to-low)
    # The loop: xor edx,edx; div ecx(=10); dec esi; add dl,30h; ...
    if eax == 0:
        # Special case: if eax==0, loop runs once producing '0'
        # ASSUMPTION: zero produces single '0'
        return '0'
    # Handle negative: idiv can give negative remainder
    # ASSUMPTION: we take absolute value for digit generation
    # since the asm uses unsigned div after this (xor edx,edx; div ecx)
    eax_u = eax & 0xFFFFFFFF  # treat as unsigned 32-bit for the digit loop
    digits = []
    tmp = eax_u
    if tmp == 0:
        digits.append('0')
    while tmp > 0:
        d = tmp % 10
        tmp = tmp // 10
        ch = d + 0x30
        if ch >= 0x3A:
            ch += 7  # makes A-F for hex digits
        digits.append(chr(ch))
    # digits are stored low-digit first but read high-first (esi decrements)
    # so reverse to get correct order
    digits.reverse()
    return ''.join(digits)

def keygen(name):
    """
    Generate serial for given name.
    Processes each character, concatenates keyparts.
    """
    serial_parts = []
    for c in name:
        part = char_to_keypart(c)
        serial_parts.append(part)
    return '-'.join(serial_parts)  # ASSUMPTION: separator is '-' or just concatenation

def keygen_concat(name):
    """Concatenated version without separator."""
    result = ''
    for c in name:
        result += char_to_keypart(c)
    return result

def verify(name, serial):
    """
    # ASSUMPTION: The verify function checks serial == keygen(name).
    # The exact check routine from the crackme binary is not fully described.
    # The bla.asm shows some rejection conditions (checking for 'N','AN','A','G','!','H','T')
    # at the start of the result string, but the full comparison logic is unclear.
    # We attempt both concatenated and dash-separated forms.
    """
    expected_concat = keygen_concat(name)
    expected_dash = keygen(name)
    return serial == expected_concat or serial == expected_dash


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
