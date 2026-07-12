# Reverse-engineered keygen for 'Crack Me v3 by OutCast3k'
# Based on the writeup/tutorial from crackmes.de
#
# PART 1 SERIAL ALGORITHM (from writeup):
#   - Serial must be > 9 characters long
#   - Take the first two characters of the entered serial, e.g. 'AB'
#   - Get their hex ASCII codes as a string, e.g. '4142'
#   - Concatenate: chars + hex_codes -> e.g. 'AB4142'
#   - Append the constant string 'oc3k' -> e.g. 'AB4142oc3k'
#   - This is the valid Part 1 serial
#
# PART 2 SERIAL ALGORITHM (writeup truncated, partial):
#   - Uses the name entered and iterates over Part1 serial characters
#   - Starts with serial_val = 0, index EBX = 1
#   - Loop over characters of Part1 serial, accumulating some value
#   - ASSUMPTION: it sums the ordinal values of Part1 serial characters
#                 multiplied or indexed by position, then converts to string
#
# PART 3 SERIAL: writeup was truncated, algorithm unknown
#
# NOTE: Only Part 1 is fully described. Parts 2 and 3 are partial/unknown.

def part1_serial(prefix='AB'):
    """
    Generate a valid Part 1 serial from a 2-char prefix.
    The serial = prefix + hex_ascii_codes_of_prefix + 'oc3k'
    E.g. prefix='AB' -> 'AB' + '4142' + 'oc3k' = 'AB4142oc3k'
    """
    if len(prefix) < 2:
        raise ValueError('Prefix must be at least 2 characters')
    p = prefix[:2]
    hex_part = ''.join(f'{ord(c):02X}' for c in p)
    serial = p + hex_part + 'oc3k'
    # Must be > 9 chars: 'AB4142oc3k' = 10 chars, OK
    return serial

def verify_part1(serial):
    """
    Verify a Part 1 serial.
    """
    if len(serial) <= 9:
        return False
    # Extract first two chars
    prefix = serial[:2]
    expected = part1_serial(prefix)
    return serial == expected

# ASSUMPTION: Part 2 serial is a sum of ASCII values of Part1 serial characters
# The writeup shows EBX starts at 1, EAX=0, loops over Part1 serial chars
# and accumulates. The exact accumulation formula is not fully shown (truncated).
def part2_serial_guess(part1_ser, name=''):
    """
    ASSUMPTION: Part2 serial = sum of ordinal values of Part1 serial characters,
    converted to a decimal string. This is a guess based on partial writeup.
    The name may also be involved but the truncated writeup does not clarify.
    """
    # ASSUMPTION: simple sum of ord values of Part1 serial
    val = sum(ord(c) for c in part1_ser)
    return str(val)

def keygen(name, prefix='AB'):
    """
    Generate serials for all parts given a name and a 2-char prefix.
    Returns (part1, part2, part3) where part3 is unknown.
    """
    p1 = part1_serial(prefix)
    p2 = part2_serial_guess(p1, name)  # ASSUMPTION
    p3 = None  # ASSUMPTION: Part 3 algorithm not available (writeup truncated)
    return (p1, p2, p3)

def verify(name, serial):
    """
    Verify function for Part 1 only (Part 2 and 3 algorithms not fully known).
    serial should be the Part 1 serial.
    """
    return verify_part1(serial)


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
