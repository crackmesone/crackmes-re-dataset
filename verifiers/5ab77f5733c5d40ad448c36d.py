# Reconstruction of gc_crackme_7 (Gandalf) serial validation algorithm
# Based on the tutorial by {Cronos}
#
# Summary from writeup:
# For each character in the name, four keys are derived:
#   key[0] = char XOR 0xAE
#   key[1] = char XOR 0x3D7  (16-bit)
#   key[2] = char XOR 0x2A3  (16-bit)
#   key[3] = char XOR 0x144  (16-bit)
# Then each key is reduced by dividing by 10 repeatedly until < 10.
# The resulting digits form part of the serial.
# The serial itself is also used in the checking process (making some names have no valid serial).
# NOTE: The writeup was truncated before showing the full serial construction/validation.

def _reduce_to_digit(val):
    """Divide by 10 repeatedly until value < 10, return that digit."""
    val = val & 0xFFFF  # treat as 16-bit
    while val >= 10:
        val = val // 10
    return val

def _compute_keys_for_char(c):
    """Compute the four key values for a single character."""
    char_val = ord(c) & 0xFF
    key0 = char_val ^ 0xAE
    key1 = char_val ^ 0x3D7
    key2 = char_val ^ 0x2A3
    key3 = char_val ^ 0x144
    # Mask to 16-bit
    key0 = key0 & 0xFFFF
    key1 = key1 & 0xFFFF
    key2 = key2 & 0xFFFF
    key3 = key3 & 0xFFFF
    return key0, key1, key2, key3

def _compute_digit_block(c):
    """Return four reduced digits for a character."""
    k0, k1, k2, k3 = _compute_keys_for_char(c)
    d0 = _reduce_to_digit(k0)
    d1 = _reduce_to_digit(k1)
    d2 = _reduce_to_digit(k2)
    d3 = _reduce_to_digit(k3)
    return d0, d1, d2, d3

# ASSUMPTION: The serial is formed by concatenating the digit blocks for each character
# in the name, ordered as key[0], key[1], key[2], key[3] per character.
# The writeup was truncated so the exact serial format and final comparison are unknown.
# ASSUMPTION: The serial check iterates over name characters (from index 1, since
# the disassembly uses bl as index starting at 0 but the Delphi string access uses -1+eax offset)
# and the serial length and grouping are not fully specified.

def keygen(name):
    """Generate a serial for the given name."""
    if not name:
        return ""
    serial_digits = []
    for c in name:
        d0, d1, d2, d3 = _compute_digit_block(c)
        # ASSUMPTION: digits appended in order key[0], key[1], key[2], key[3]
        serial_digits.extend([d0, d1, d2, d3])
    serial = ''.join(str(d) for d in serial_digits)
    return serial

def verify(name, serial):
    """Verify a name/serial pair."""
    if not name or not serial:
        return False
    expected = keygen(name)
    # ASSUMPTION: direct string comparison of computed serial to provided serial
    # The actual check may be more complex (the writeup mentions the serial is used
    # in checking itself, and some names may have no valid serial).
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
