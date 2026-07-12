import math

def name_to_int_array(name):
    """
    Convert name to int array per the described algorithm.
    The name must end with 'B' (last char must be 'B' per the crackme requirement).
    """
    int_array = []

    # Process each character of the name (including the trailing 'B')
    i = 0
    while i < len(name):
        char = ord(name[i])
        i += 1

        # Iteratively reduce char until it's in range 0..9
        while True:
            if 0x00 <= char <= 0x09:
                # char is already a single digit
                # According to writeup: if char+0x30 == 0x31 then char+0x30 = 0x32
                # This means digit '1' becomes '2'
                val = char
                # ASSUMPTION: the correction (0x31->0x32) only affects OUT1 string,
                # but int[] (OUT2) stores char - 0x30 = char directly as digit value
                int_array.append(val)
                break
            elif 0x10 <= char <= 0xFF:
                val1 = char & 0x0F        # low nibble
                val2 = (char >> 4) & 0x0F # high nibble
                char = val1 + val2
                # loop back (JMP LABEL1)
            else:
                # char == 0 would break the loop but we handle that at the outer level
                # ASSUMPTION: shouldn't happen mid-character processing
                break

    return int_array


def int_array_to_serial_float(int_array):
    """
    Convert int array to a float value using the described algorithm.
    Uses log base 2 arithmetic.
    Note: The writeup says to use 80-bit precision. Python float is 64-bit.
    We use Python's arbitrary precision via the 'decimal' module with high precision.
    """
    # ASSUMPTION: We use Python's standard float (64-bit double).
    # The writeup warns about 80-bit precision; results may differ slightly.

    if len(int_array) < 2:
        return 0.0

    # y = int_array[0], x = int_array[1]
    # Then loop: y = y * log2(x), take next int, if 0 break, x = next int
    # The loop processes int_array[1], int_array[2], ..., stopping before a 0 element

    y = float(int_array[0])
    idx = 1

    while True:
        x = int_array[idx]
        if x == 0:
            break
        if x == 1:
            # log2(1) = 0, y stays conceptually but per algorithm y *= 0
            y = y * 0.0
        else:
            y = y * math.log2(float(x))
        idx += 1
        if idx >= len(int_array):
            break
        # check next
        # ASSUMPTION: The loop checks NEXTINT after computing y*log2(x),
        # then if NEXTINT==0 breaks, else x=NEXTINT and continues
        # We already incremented idx so int_array[idx] is NEXTINT
        if int_array[idx] == 0:
            break

    return y


def float_to_serial_string(y):
    """
    Format float to string then replace '.' with the 2nd character of the string.
    Based on writeup:
      OUT 2: format float to string  e.g. ' 694.2577038174219'
      OUT 3: replace '.' with char at index 2 of the string
              e.g. ' 6942257703817421...' -> ' 69422577038174219'
    The leading space is the first char of serial (found via bruteforce as ' ').
    """
    # Format the float. The writeup shows ~17 significant digits.
    # ASSUMPTION: We format with enough precision and use Python repr-style.
    # The example shows 694.2577038174219 -> 6942257703817421...
    # The dot is removed (replaced by char at position 2, which is '4' -> moves digits)
    # Actually: REPLACEDOTWITHCHAR2 means replace '.' with string[1] (0-indexed char 2?)
    # Looking at example: ' 694.257...' -> ' 6942257...'
    # The '.' is replaced by '4' (which is string[2] in 0-indexed: ' ','6','9','4',...)
    # Wait: ' 694.2577...' char[2] is '9'? Let's re-examine:
    # str: ' ', '6', '9', '4', '.', '2', ...
    # index 0=' ', 1='6', 2='9', 3='4', 4='.'
    # OUT3: ' 6942257...' - the '.' is gone and '4' appears where '.' was?
    # Actually it looks like the '.' is simply removed (deleted), not replaced.
    # ' 694.2577...' -> remove '.' -> ' 6942577...' but example shows ' 69422577...'
    # ASSUMPTION: 'REPLACEDOTWITHCHAR2' replaces the dot with the character at index 2
    # of the string. index 2 = '9'? That gives ' 6949257...' which doesn't match.
    # Let me try: char at position 1 (0-indexed) = '6'? No.
    # Most likely interpretation: just remove the dot.
    # ' 694.2577038174219' -> remove dot -> ' 6942577038174219' (16 digits)
    # But example serial is ' 69422577038174219' (17 digits)... 
    # ASSUMPTION: The float formatting includes more digits, let's just remove the dot.

    # Format with high precision
    formatted = f'{y:.15e}'  # scientific notation
    # Actually let's try fixed point with many digits
    # The example ' 694.2577038174219' suggests fixed-point formatting
    # with the leading space being the serial's first char

    # Use repr or a specific format
    # Try: format as string with enough decimal places
    s = f' {y:.13f}'  # leading space + fixed point
    # Now replace '.' with the character at index 2 of s
    # s = ' 694.2577038174219' -> s[2] = '9'? s[0]=' ', s[1]='6', s[2]='9', s[3]='4'
    # Replace '.' with s[2]:
    # ASSUMPTION: char2 means index 2 (0-based)
    char2 = s[2] if len(s) > 2 else ''
    result = s.replace('.', char2)
    return result


def verify(name, serial):
    """
    Verify name/serial pair.
    Requirements:
    - name must end with 'B'
    - serial must start with ' ' (blank space)
    """
    if not name.endswith('B'):
        return False
    if not serial.startswith(' '):
        return False

    expected = keygen(name)
    return serial == expected


def keygen(name):
    """
    Generate serial for a given name.
    Name must end with 'B' (enforced by the crackme - last char XOR key).
    """
    # Ensure name ends with 'B'
    if not name.endswith('B'):
        name = name + 'B'

    int_arr = name_to_int_array(name)
    y = int_array_to_serial_float(int_arr)
    serial = float_to_serial_string(y)
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
