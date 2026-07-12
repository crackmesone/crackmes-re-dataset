# Keygen for auz_cavora by artfulwave
# Fully recovered from the C keygen source by ToMKoL

MD5FILE = "8f087e85e809af6c3902b12408fc065d"
MINUS = "--"
DEADCODE = "-DEADC0DE()"


def replace(string):
    """Replace certain characters per the substitution table."""
    result = []
    for ch in string:
        lch = ch.lower()
        if lch == 'a':
            result.append('m')          # A/a -> m
        elif lch == 'b':
            result.append('Z')          # B/b -> Z
        elif lch == 'c':
            result.append('T')          # C/c -> T
        elif lch == 'd':
            result.append('!')          # D/d -> !
        elif lch == 'e':
            result.append('*')          # E/e -> *
        elif lch == 'f':
            result.append('//')         # F/f -> //
        else:
            result.append(ch)           # default: copy
    return ''.join(result)


def generate(name):
    """
    Reproduces the C generate() function.
    name must be at least 9 characters (the crackme requires >= 9).
    Characters are treated as their Unicode code-point values (wchar_t).
    The bitwise NOT (~) operates on the 16-bit wchar_t value, masked to 0xFFFF.
    """
    length = len(name)
    if length < 9:
        raise ValueError("Name must be at least 9 characters")

    # Build the first part of the serial:
    # serial[0] = user[0]  (first char unchanged)
    # serial[i] = ~user[i] for i in 1..len-1  (bitwise NOT, 16-bit)
    serial_chars = []
    serial_chars.append(name[0])
    for i in range(1, length):
        flipped = (~ord(name[i])) & 0xFFFF
        serial_chars.append(chr(flipped))
    serial_part1 = ''.join(serial_chars)

    # Build temp string:
    # temp = "--" + user[1:] + user[0] + "-DEADC0DE()" + MD5FILE
    temp = MINUS + name[1:] + name[0] + DEADCODE + MD5FILE

    # Apply replace() substitution and append to serial_part1
    serial_part2 = replace(temp)

    # Compute the signed 32-bit integer s:
    # s = (((len * 0x66 + 0x34EFC1A4) * 2 + len) * 2 + (len * 0xA)) * 0xCD
    # The C code uses signed int arithmetic with 32-bit wrapping.
    def to_int32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    n = length
    step1 = to_int32(n * 0x66 + 0x34EFC1A4)
    step2 = to_int32(step1 * 2 + n)
    step3 = to_int32(step2 * 2 + n * 0xA)
    s = to_int32(step3 * 0xCD)

    # Append decimal representation of s and then MD5FILE
    serial = serial_part1 + serial_part2 + str(s) + MD5FILE
    return serial


def verify(name, serial):
    """Verify name/serial pair by regenerating and comparing."""
    if len(name) < 9:
        return False
    try:
        expected = generate(name)
    except ValueError:
        return False
    return serial == expected


def keygen(name):
    """Return the valid serial for the given name (>= 9 chars)."""
    return generate(name)



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
