# Reverse-engineered validation for crackme5 by mtador
# Based on the writeup by Kerberos
#
# Key observations from the writeup:
# 1. Name and serial must each be longer than 1 character (length > 1 after +1 increment, so actual length >= 1, i.e. non-empty)
# 2. Each character of the name is transformed: encoded[i] = (char ^ (char * 3)) & 0xFF
#    But __crck5_4 is called on the char before the XOR -- we don't know exactly what __crck5_4 does.
#    ASSUMPTION: __crck5_4 is identity (returns the byte value unchanged), since no other description is given.
# 3. After encoding, a second pass multiplies each encoded byte by (ticks2 - ticks1 + 1).
#    ASSUMPTION: In a keygen/verifier context we treat (ticks2 - ticks1) as 0 (negligible time),
#    so the multiplier is 1 and this step is effectively a no-op (multiply by 1).
# 4. The serial is compared character-by-character against the encoded name.
#    eqChars must equal nameLength for success (based on __crck5_5 doing CMP nameLength, eqChars).
# 5. checkSum1 and checkSum2 comparison: if not equal, a WM_DESTROY is sent but execution continues
#    (jz short loc_403346 skips the destroy call, but either way reaches loc_403346).
#    ASSUMPTION: checkSum1 != checkSum2 does NOT immediately fail; it just sends a message.
#    The real pass/fail is determined by eqChars == nameLength.

def __crck5_4(char_byte):
    # ASSUMPTION: identity function - the writeup calls it but doesn't describe its body
    return char_byte

def encode_name(name, tick_diff=0):
    """
    Encode the name string as described in the writeup.
    Step 1: for each char, encoded = (f(c) ^ (f(c) * 3)) & 0xFF
    Step 2: multiply each encoded byte by (tick_diff + 1), take & 0xFF
    """
    encoded = []
    for ch in name:
        c = ord(ch) & 0xFF
        fc = __crck5_4(c)
        # XOR with 3*fc
        val = (fc ^ (fc * 3)) & 0xFF
        encoded.append(val)

    # Second pass: multiply by (tick_diff + 1)
    # ASSUMPTION: tick_diff = 0 in normal fast execution
    multiplier = (tick_diff + 1) & 0xFFFFFFFF
    result = []
    for val in encoded:
        fv = __crck5_4(val)
        new_val = (fv * multiplier) & 0xFF
        result.append(new_val)
    return result

def verify(name, serial):
    """
    Returns True if the serial matches the encoded name.
    Both name and serial must have length >= 1 (the crackme checks > 1 after +1 increment,
    meaning the original length must be >= 1).
    """
    if len(name) < 1 or len(serial) < 1:
        return False

    encoded = encode_name(name, tick_diff=0)

    # Serial must be at least as long as name for all chars to match
    if len(serial) < len(name):
        return False

    # Compare eqChars == nameLength
    eq_chars = 0
    for i, enc_byte in enumerate(encoded):
        # serial is compared starting at index 1 in the original (counter starts at 1)
        # ASSUMPTION: we compare serial[i] against encoded[i] (0-based)
        if i < len(serial) and ord(serial[i]) & 0xFF == enc_byte:
            eq_chars += 1

    return eq_chars == len(name)

def keygen(name):
    """
    Generate a valid serial for the given name.
    """
    if len(name) < 1:
        raise ValueError("Name must be at least 1 character long")

    encoded = encode_name(name, tick_diff=0)
    # Convert encoded bytes back to characters
    serial = ''.join(chr(b) for b in encoded)
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
