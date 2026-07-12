# Crackme 4 by kcom - Reverse engineered serial validation
# Based on the partial writeup/disassembly provided
#
# From the disassembly we can see:
# 1. Name must be >= 8 characters
# 2. Serial must be >= 8 characters
# 3. There is a string at 00403024: "ckkb&pkh&@-" which appears to be
#    an XOR/transform key or a transformed string used in comparison
# 4. The algorithm manipulates the name/serial in some way
#
# The string "ckkb&pkh&@-" looks like it could be an encoded form of something.
# XORing each char with small values or shifting bytes.
#
# ASSUMPTION: The serial validation XORs or otherwise transforms the name
# using a fixed key or arithmetic on character values, then compares to serial.
#
# ASSUMPTION: Looking at "ckkb&pkh&@-" - if we XOR each char with some value:
# 'c'^0x0A='i', 'k'^0x0A='a', etc. - unclear without full disassembly.
#
# ASSUMPTION: A common pattern for crackmes of this era:
# serial is derived from the name by summing/XORing character values.
# We implement what we can determine and mark assumptions clearly.

def _transform_name(name):
    """
    ASSUMPTION: Transform name into a serial candidate.
    The exact algorithm is not fully recoverable from the truncated writeup.
    We implement a plausible reconstruction based on the visible string
    '"ckkb&pkh&@-"' at 00403024 and the structure of the validation loop.
    """
    # ASSUMPTION: The algorithm iterates over name characters,
    # applies some arithmetic (XOR, ADD, shift), and produces serial digits.
    result = []
    for i, ch in enumerate(name):
        v = ord(ch)
        # ASSUMPTION: XOR with index and some constant, then map to printable
        transformed = (v ^ (i + 1) ^ 0x05) & 0xFF
        # ASSUMPTION: map to printable ASCII range 0x20-0x7E
        transformed = (transformed % 95) + 0x20
        result.append(chr(transformed))
    return ''.join(result)


def _check_against_encoded_string(name, serial):
    """
    ASSUMPTION: The string 'ckkb&pkh&@-' at 00403024 is used as an XOR mask
    or as a comparison target after transforming the serial or name.
    The REPNE SCAS + comparison loop suggests character-by-character check.
    """
    # The visible encoded string from the disassembly
    encoded = "ckkb&pkh&@-"

    # ASSUMPTION: serial XOR'd with name chars produces the encoded string,
    # or the name is encoded and compared to serial directly.
    # We cannot determine the exact check without the full disassembly.
    # Returning False as a placeholder for the real check.
    return None  # Cannot determine


def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: Name and serial must each be >= 8 characters (confirmed from disasm).
    ASSUMPTION: The exact byte-by-byte transformation is not fully recoverable
    from the truncated writeup. The core structure is implemented as best as possible.
    """
    if len(name) < 8:
        return False
    if len(serial) < 8:
        return False

    # ASSUMPTION: Derive expected serial from name using the transform
    expected = _transform_name(name)

    # Compare at least the first min(len(serial), len(expected)) chars
    # ASSUMPTION: comparison is for first 8+ characters
    check_len = min(len(serial), len(expected), 8)
    return serial[:check_len] == expected[:check_len]


def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: Uses the transform above. May not be correct without
    full disassembly of the validation routine.
    """
    if len(name) < 8:
        # Pad name to minimum length
        name = name.ljust(8, 'A')
    return _transform_name(name)



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
