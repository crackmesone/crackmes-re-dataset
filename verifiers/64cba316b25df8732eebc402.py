# Reverse-engineered keygen for seawolf's Crackme v1.0
# Based on the solution writeup by cnathansmith
#
# Algorithm summary (from writeup):
#   1. NAME must be 3-15 chars long
#   2. NAME is passed through sub_411C1C which 'Converts NAME somehow'
#   3. The result is reversed via MakeReverse()
#   4. The reversed string and the SERIAL are passed to check_serial()
#   5. check_serial() returns 0 if SERIAL is invalid
#
# From the comment by coquee:
#   name = 'coquee' => serial = '8794E7057C45873C81'
#
# The writeup was truncated before the full details of sub_411C1C were revealed.
# ASSUMPTION: sub_411C1C converts each character of NAME to its hex representation
#   (2 hex digits per char, uppercase), based on the example:
#   'coquee' -> hex of each char: 63 6F 71 75 65 65 -> '636F717565 65' (raw)
#   Then reversed, compared against serial.
#   But that doesn't match '8794E7057C45873C81' directly.
#
# Let's try another ASSUMPTION: sub_411C1C computes something per character
# and the serial is a hex string of those computed values reversed.
#
# From the example: name='coquee', serial='8794E7057C45873C81'
# len(serial) = 18 hex chars = 9 bytes
# len(name) = 6 chars
# 18 / 6 = 3 hex chars per char? Unusual.
# Actually 16 hex chars for 6 chars would be 2-3 per char inconsistently.
#
# ASSUMPTION: Let's try each char XOR or multiplied by something.
# coquee = [0x63, 0x6F, 0x71, 0x75, 0x65, 0x65]
# serial bytes reversed: '8794E7057C45873C81'
# Reversed serial string = '18C3788540 7E4978' -> let's reverse the string:
# '8794E7057C45873C81' reversed as string = '18C378547C507E4978'... 
# Let's just reverse the hex string char pairs:
# '8794E7057C45873C81' -> split into bytes from right:
# This is 18 hex digits = odd, so maybe not pure byte pairs.
#
# ASSUMPTION: The conversion function sub_411C1C converts each wide char to
# a hex string representation, possibly with some arithmetic transformation.
# Since we cannot fully determine the algorithm from the truncated writeup,
# we implement a best-guess based on available data and mark gaps.

def _convert_name(name):
    """
    ASSUMPTION: sub_411C1C converts each character of NAME using some per-char
    transformation to produce a hex string. The exact transform is unknown
    because the writeup was truncated. We attempt to reverse-engineer from
    the known example: name='coquee' -> intermediate -> reversed -> serial='8794E7057C45873C81'
    
    Let's test: if we reverse the serial string and that equals the intermediate:
    reversed serial str = '18C3788540 7E49 78' -- need to be more careful:
    serial = '8794E7057C45873C81'
    reversed as string  = '18C3788540 7E49 78'
    Let me just reverse it: '18C378547C507E4978' - manually:
    '8794E7057C45873C81'
     0123456789...
    reversed: '18C378540 7E49 78' - let me do it properly in code.
    
    '8794E7057C45873C81'[::-1] = '18C378540 7E49 78' computed below.
    
    ASSUMPTION: Each character produces exactly 3 hex-digit output (unlikely)
    OR the serial includes a length/checksum byte.
    
    We cannot determine the exact algorithm. Returning placeholder.
    """
    # ASSUMPTION: multiply each ord by some constant and format as hex
    # Testing: if char_val * K formatted as 2 hex digits reversed gives serial
    result = ''
    for ch in name:
        v = ord(ch)
        # ASSUMPTION: some simple transform per character
        result += format(v, '02X')
    return result


def _check_serial_match(converted_reversed, serial):
    """
    ASSUMPTION: check_serial does a direct string comparison of
    the reversed converted name against the serial (case-insensitive or exact).
    """
    return converted_reversed.upper() == serial.upper()


def verify(name, serial):
    """
    Verify name/serial pair.
    Known constraints:
      - name length must be 3-15 chars
      - serial is the reversed hex-encoded transformation of name
    """
    if not (3 <= len(name) <= 15):
        return False
    
    # ASSUMPTION: sub_411C1C converts name chars to hex string
    converted = _convert_name(name)
    
    # Apply MakeReverse on the converted string
    reversed_converted = converted[::-1]
    
    # Compare with serial
    return _check_serial_match(reversed_converted, serial)


def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: serial = reverse of per-char hex transformation of name
    """
    if not (3 <= len(name) <= 15):
        raise ValueError('Name must be 3-15 characters')
    
    converted = _convert_name(name)
    serial = converted[::-1]
    return serial.upper()


# Validation against known example from comments:
# name='coquee' should give serial='8794E7057C45873C81'
# Let's see what our current algorithm gives and note the discrepancy.

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
