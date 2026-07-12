def gen(s, a1, a2):
    """
    Compute the key value from the username string using the two seeds a1 and a2.
    This matches the gen() function in kg.cpp and calcKey() in keygen.cpp.
    """
    a3 = 0
    for ch in s:
        ebx = a3 * a2
        a3 = ebx + ord(ch)
        a2 = a2 * a1
    return a3 & 0x7fffffff


def calc_part(key):
    """
    Convert the numeric key into the digit-string portion of the serial.
    This mirrors calcPart() in keygen.cpp:
      while edx (i.e., the quotient) != 0:
        edx = (key * 0xcccccccd) >> 35   (i.e., floor(key/10))
        remainder = key - edx*10
        emit keychrs[remainder + 4]   -> keychrs = "-+xX0123456789abcdef0123456789ABCDEF"
                                         index 4 = '0', so this just gives decimal digit
        key = edx
    Result is built in reverse, so we reverse it before returning.

    NOTE: keychrs[4 + digit] for digit in 0-9 maps to '0'-'9', so this is
    simply a base-10 decimal conversion.
    """
    keychrs = "-+xX0123456789abcdef0123456789ABCDEF"
    digits = []
    act = key
    if act == 0:
        return "0"
    while act:
        # edx = floor(act / 10) using the multiply-shift trick (equivalent)
        edx = int((act * 0xcccccccd) & 0xffffffff) >> 3
        edx = edx >> 32 if False else (act * 0xcccccccd) >> 35
        edx = edx & 0xffffffff
        remainder = act - edx * 10
        digits.append(keychrs[remainder + 4])
        act = edx
    # digits were built LSB first, reverse to get the number
    digits.reverse()
    return ''.join(digits)


def keygen(name):
    """
    Generate the valid serial for the given username.
    Format: ReWrit-<key1><key2>-Swe
    where key1 = gen(name, 0x17a, 0x289) and key2 = gen(name, 0x2b9, 0x155)
    printed as decimal integers.
    """
    key1 = gen(name, 0x17a, 0x289)
    key2 = gen(name, 0x2b9, 0x155)
    # The simplest correct form (from solution 1 kg.cpp) is just decimal repr
    return "ReWrit-{}{}-Swe".format(key1, key2)


def verify(name, serial):
    """
    Verify that the serial matches the one generated for the given name.
    Also checks that name != serial (the crackme verifies this too).
    """
    if name == serial:
        return False
    expected = keygen(name)
    return serial == expected



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
