# Reconstruction of the 'justfun' crackme by raven_ (crackmes.de)
# Based on the keygen.cpp solution writeup

# The table (16 entries, indexed mod 15)
TABLE = [
    0x55, 0x36, 0x87, 0xA5,
    0x5D, 0x01, 0x0F, 0xFD,
    0xE4, 0xD5, 0x66, 0x3D,
    0xBA, 0xCC, 0x21, 0x5D
]

# NOTE: The serial must be at least 16 bytes for the third loop to work safely,
# but the check only depends on serial[0] and serial[1] in a meaningful way
# (the third loop is effectively a NOP as noted in the writeup).
# The serial is treated as a fixed-size 16-byte buffer (padded with zeros or
# the actual characters beyond index 1 don't matter for the outcome).

def f(x):
    """table[x mod 15], using Python's true modulo (always non-negative for positive x).
    For negative x, Python's % gives non-negative results, matching C signed remainder
    behavior via the doubled table trick in the original C code.
    The C code uses a doubled table and index+0x10 to handle negative remainders:
        table[((x) % 15) + 0x10]
    In Python, x % 15 is always in [0,14], so we can use it directly.
    """
    # ASSUMPTION: Python's % operator always returns non-negative, so no need for
    # the +0x10 offset trick used in the C solution for negative remainders.
    return TABLE[x % 15]


def check(serial_bytes):
    """
    serial_bytes: a bytes-like object of at least 2 bytes (16 bytes used internally).
    Returns True if the serial passes the check.
    """
    # Pad to 16 bytes
    s = bytearray(16)
    for i, b in enumerate(serial_bytes[:16]):
        s[i] = b if isinstance(b, int) else ord(b)

    # Init
    a = f(s[0])
    b = f(s[1])

    # Convert to signed bytes for arithmetic (matching C char behavior)
    def to_signed(v):
        v = v & 0xFF
        return v if v < 128 else v - 256

    a = to_signed(a)
    b = to_signed(b)

    # Calculation 1: a ^= f(i * b) for i in 0..15
    for i in range(16):
        a ^= to_signed(f(i * b))
        a = to_signed(a)

    # Calculation 2: b ^= f(i * a) for i in 0..15
    for i in range(16):
        b ^= to_signed(f(i * a))
        b = to_signed(b)

    # Calculation 3: effectively a NOP (as noted in writeup)
    # g(i) = f(s[i])
    def g(i):
        return to_signed(f(to_signed(s[i])))

    for i in range(4):
        a ^= g(4*i) ^ g(4*i+1) ^ g(4*i+2) ^ g(4*i+3)
        b ^= g(12-4*i) ^ g(13-4*i) ^ g(14-4*i) ^ g(15-4*i)
        a = to_signed(a)
        b = to_signed(b)

    return (a & 0xFF) == (b & 0xFF)


def verify(name, serial):
    """
    The crackme only checks the serial, name is not used.
    serial is a string (at least 2 chars; padded to 16 internally).
    """
    # ASSUMPTION: name is not used in the check (the writeup/keygen shows no name usage)
    serial_bytes = serial.encode('latin-1') if isinstance(serial, str) else serial
    return check(serial_bytes)


def keygen(name):
    """
    Generate a valid serial. As shown in the keygen.cpp, any serial whose
    first two bytes form a valid pair will work. The rest of the bytes are
    arbitrary (the third loop is a NOP).
    Returns a valid serial string.
    """
    # Search for valid first two characters in printable ASCII range
    for i in range(32, 127):
        for j in range(32, 127):
            candidate = chr(i) + chr(j) + 'AAAAAAAAAAAAAA'  # pad to 16
            if verify(name, candidate):
                return candidate
    # ASSUMPTION: If no printable pair found, return None
    return None


def keygen_all(name, lo=32, hi=127):
    """Generate all valid serials with first two bytes in [lo, hi)."""
    results = []
    for i in range(lo, hi):
        for j in range(lo, hi):
            candidate = chr(i) + chr(j) + 'AAAAAAAAAAAAAA'
            if verify(name, candidate):
                results.append(candidate)
    return results



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
