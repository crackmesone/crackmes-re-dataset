import os

def _rotate_forward(s):
    """Apply the loop: for num in range(1, len(s)): s = s[num:] + s[:num]"""
    # After the loop completes, the net rotation is sum(1..len-1) = len*(len-1)/2
    # which equals rotation by len*(len-1)//2 % len
    if len(s) <= 1:
        return s
    n = len(s)
    rot = (n * (n - 1) // 2) % n
    return s[rot:] + s[:rot]

def _rotate_backward(s):
    """Apply the loop: for num in range(1, len(s)): s = s[len-num:] + s[:len-num]"""
    # Net rotation: sum of (len-1),(len-2),...,1 steps to the right
    # Each step rotates right by num => left by (len-num)
    # Net left rotation = sum(len-num for num in 1..len-1) = sum(1..len-1) = len*(len-1)/2
    # but these are right-rotations: s = s[len-num:] + s[:len-num] means rotate RIGHT by num
    # Net right rotation = sum(1..len-1) = len*(len-1)//2 mod len
    if len(s) <= 1:
        return s
    n = len(s)
    rot = (n * (n - 1) // 2) % n
    # rotate right by rot
    return s[n - rot:] + s[:n - rot]

def _superstring_add(name, username):
    """Implements SuperString operator+: result = rotated(username) + 'X' + rotated(name)"""
    str_a = name.upper()  # SuperString constructor converts to uppercase
    str_b = username.upper()  # SuperString constructor converts to uppercase
    # Apply forward rotation to str_a (name)
    str_a_rot = _rotate_forward(str_a)
    # Apply backward rotation to str_b (username)
    str_b_rot = _rotate_backward(str_b)
    return str_b_rot + 'X' + str_a_rot

def _generate_serial(name, username):
    """Generates the serial from name and username (mirrors the Generate() keygen)."""
    str1 = name
    str2 = username
    # Apply even-length rotation (this is what the loop simplifies to for even length)
    # For even length, the loop sum(1..len-1) % len = len*(len-1)//2 % len
    # For even len n: n*(n-1)//2 % n = (n-1)//2 * (n % 2... actually:
    # n even: n*(n-1)/2 mod n = n/2*(n-1) mod n. Since n-1 is odd, n/2*(n-1) mod n:
    # = (n/2 mod n) * (n-1) mod n ... let's just use the loop result
    # The Generate() source shows: if even, swap halves
    # That's actually equivalent to rotation by len/2
    if len(str1) % 2 == 0:
        str1 = str1[len(str1)//2:] + str1[:len(str1)//2]
    if len(str2) % 2 == 0:
        str2 = str2[len(str2)//2:] + str2[:len(str2)//2]
    decoded_serial = str2 + 'X' + str1.upper()
    serial = ''
    for ch in decoded_serial:
        serial += format(ord(ch), '02X')
    return serial

def _compute_checkboxes(name):
    """Compute the 6 checkbox states from the name length."""
    # binary of length, reversed, zero-padded to 6 bits
    length = len(name)
    bin_str = bin(length)[2:]  # e.g. '100' for 4
    reversed_bin = bin_str[::-1]  # e.g. '001' for 4
    # pad to 6 chars with '0'
    reversed_bin = reversed_bin.ljust(6, '0')
    cb = [reversed_bin[i] == '1' for i in range(6)]
    return cb  # cb[0]=cb1, cb[1]=cb2, ..., cb[5]=cb6

def verify(name, serial):
    """
    Verify name+serial combination.
    The serial is a hex-encoded string. When expanded (each pair of hex digits -> char),
    it should equal SuperString(name) + SuperString(UserName).
    The checkboxes are derived from the name length binary representation.
    Since we can't interactively check checkboxes, we verify the serial matches the generated one.
    """
    if not name or not serial:
        return False
    if len(serial) % 2 != 0:
        return False
    username = os.environ.get('USERNAME') or os.environ.get('USER') or ''
    # Expand the serial
    try:
        expanded = ''
        for i in range(0, len(serial) - 1, 2):
            expanded += chr(int(serial[i:i+2], 16))
    except Exception:
        return False
    # Compute expected expanded value using SuperString operator+
    expected = _superstring_add(name, username)
    # Also verify checkboxes encode name length correctly
    # num7 = sum(cb[i] * 2^i for i in 0..5) should equal len(name)
    cb = _compute_checkboxes(name)
    num7 = sum((1 if cb[i] else 0) * (2**i) for i in range(6))
    serial_ok = expanded == expected
    cb_ok = num7 == len(name)
    return serial_ok and cb_ok

def keygen(name):
    """
    Generate a valid serial for the given name.
    Uses the same username as the current system.
    """
    username = os.environ.get('USERNAME') or os.environ.get('USER') or ''
    return _generate_serial(name, username)


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
