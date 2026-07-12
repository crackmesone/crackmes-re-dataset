# Reverse-engineered from the OllyDbg disassembly of therapy's 'easyone' crackme.
# The crackme reads name and serial, both must be > 4 chars (at least 5).
# For each position i in 0..len(name)-1 it computes an integer-square-root
# (isqrt) of ord(name[i]) via a binary-search loop, then computes a
# serial_char value via:  serial_val = (name_char - isqrt^2 + i^2) % 10
# and checks that chr(serial_val + ord('0')) == serial[i]  (digit character).
# The truncated writeup cuts off just before the final comparison but the
# pattern up to that point is clear.
#
# The inner loop is a binary-search for floor(sqrt(name_char)):
#   lo=0, hi=name_char
#   while True:
#     mid = (lo + hi) >> 1  (arithmetic right shift = floor division by 2)
#     mid2 = mid * mid
#     if mid2 > name_char: hi = mid
#     if mid2 < name_char: lo = mid
#     if lo + 1 == hi:  flag=2; break   (lo is the floor sqrt)
#     if mid2 == name_char: flag=1; break  (exact sqrt)
#   result = lo if flag==2 else mid
#
# Then for each char at position i:
#   name_char = ord(name[i])  (treated as signed via MOVSX)
#   sqrt_val  = isqrt_loop(name_char)
#   val = name_char - sqrt_val*sqrt_val + i*i
#   serial_digit = val % 10
#   expected_serial_char = chr(serial_digit + ord('0'))   # ASSUMPTION: maps to ASCII digit

def _isqrt_loop(c):
    """Mimics the binary-search floor-sqrt loop in the crackme."""
    # c is the signed byte value of the name character
    lo = 0
    hi = c  # initial hi = name_char (MOVSX of byte -> signed int)
    if hi <= 0:
        # Edge case: if char <= 0, the loop won't make sense; just return 0
        # ASSUMPTION: program probably only handles printable ASCII (>0)
        return 0
    while True:
        mid = (lo + hi) >> 1  # arithmetic shift right 1 = floor((lo+hi)/2)
        mid2 = mid * mid
        flag = 0
        if mid2 > c:
            hi = mid
        if mid2 < c:
            lo = mid
        # Check lo+1 == hi  (done as MOVZX lo, INC, CMP with hi)
        if (lo & 0xFF) + 1 == (hi & 0xFF):
            flag = 2
        if mid2 == c:
            flag = 1
        if flag != 0:
            if flag == 2:
                result = lo & 0xFF
            else:
                result = mid & 0xFF
            return result


def _compute_serial_char(name_char_signed, i):
    """Compute expected serial character for position i."""
    sqrt_val = _isqrt_loop(name_char_signed)
    # val = name_char - sqrt_val^2 + i^2
    val = name_char_signed - (sqrt_val * sqrt_val) + (i * i)
    # ASSUMPTION: modulo 10 to get a digit 0-9, then add ord('0')
    digit = val % 10
    return chr(digit + ord('0'))


def verify(name, serial):
    """Returns True if the serial is valid for the given name."""
    if len(name) < 5:
        return False
    if len(serial) < 5:
        return False
    # The loop runs for i in range(len(name)) but also requires serial[i] to exist
    # The crackme checks ESI (loop index) against EDI (serial length) at 0x401363
    # and jumps to 'good' (XOR EAX,EAX path) if equal -> so lengths must match
    # ASSUMPTION: serial length must equal name length (the loop exits 'good' when i==serial_len)
    if len(serial) != len(name):
        return False
    for i, ch in enumerate(name):
        c = ord(ch)
        # MOVSX treats it as signed byte
        if c > 127:
            c = c - 256
        expected = _compute_serial_char(c, i)
        if i >= len(serial):
            break
        if serial[i] != expected:
            return False
    return True


def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) < 5:
        raise ValueError('Name must be at least 5 characters long')
    serial = ''
    for i, ch in enumerate(name):
        c = ord(ch)
        if c > 127:
            c = c - 256
        serial += _compute_serial_char(c, i)
    return serial



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
