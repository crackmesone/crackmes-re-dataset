# Reconstruction of bitpatcher's MY1ST keygenme validation algorithm
# Based on the writeup by Groshenkoa
#
# Summary from the writeup:
# - The serial is split into 5 triads (groups of 3 decimal digits each)
#   making a 15-character serial like "XXXXX-XXXXX-XXXXX" or similar decimal groups
# - Triad1 and Triad4 are used as Y and X pixel coordinates
# - If Triad4 > 300 and/or Triad1 > 65: use (Triad4 mod 300) and/or (Triad1 mod 65)
# - Triads 2, 3, 5 compose a hex value: value = Triad2*10000h + Triad5*100h + Triad3
# - GetPixel is called at (X=coordX, Y=coordY) and the returned RGB is compared to 'value'
# - The third character of the username (ASCII value - 2) must equal the third part of the serial
# - First part of serial must be exactly 15 characters (5 triads of 3 digits)
# - Username must be at least 4 characters long (checked: length > 4, else loop back)
# - A check: length of first part of serial must not be shorter than 15 chars
#   (cmp ebx, 0 after division; if zero -> exception path)
#
# ASSUMPTION: The serial format is 15 decimal digits split as:
#   Triad1 Triad2 Triad3 Triad4 Triad5 (each 3 digits, no separators based on edit box)
#   e.g. "AAABBBCCCDDDEEE"
# ASSUMPTION: The pixel coordinate check (GetPixel) is against a specific bitmap/window
#   that we cannot reproduce here, so we skip that check and mark it as unverifiable.
# ASSUMPTION: The third part check is: serial_triad3 == ASCII(name[2]) - 2
# ASSUMPTION: Serial length == 15 digits exactly (from the 15-char check in the writeup)

def parse_serial(serial):
    """Parse a 15-digit serial into 5 triads."""
    if len(serial) != 15:
        return None
    try:
        triads = [int(serial[i*3:(i+1)*3]) for i in range(5)]
        return triads
    except ValueError:
        return None

def verify(name, serial):
    """
    Verify name/serial pair.
    
    Known checks from the writeup:
    1. Name length must be > 4 (at least 4 chars, writeup says 'cmp ebx, 4 / jl short')
    2. Serial must be exactly 15 characters (digits)
    3. The third character of the name: ASCII(name[2]) - 2 must equal Triad3 (the third 3-digit group)
    4. Triads 1..5 form coordinates and a color value for a GetPixel check -
       this CANNOT be verified without the actual crackme window/bitmap.
       We mark it as ASSUMPTION: always passing here.
    """
    # Check 1: name length > 4
    # ASSUMPTION: the check is length >= 4 (jl short means jump if less than)
    if len(name) < 4:
        return False
    
    # Check 2: serial length == 15
    if len(serial) != 15:
        return False
    
    # Parse serial into 5 triads
    triads = parse_serial(serial)
    if triads is None:
        return False
    
    triad1, triad2, triad3, triad4, triad5 = triads
    
    # Check 3: third char of name
    # From writeup: ASCII value of name[2] minus 2 == triad3 (third 3-digit group)
    # ASSUMPTION: this is the core check derived from the writeup
    name_third_char_val = ord(name[2]) - 2
    if triad3 != name_third_char_val:
        return False
    
    # Check 4: GetPixel RGB check
    # ASSUMPTION: We cannot verify the GetPixel condition without the actual crackme.
    # The pixel coordinates are derived as:
    coord_y = triad1 % 300 if triad1 > 300 else triad1  # ASSUMPTION: mod 300 if > 300
    coord_x = triad4 % 65 if triad4 > 65 else triad4   # ASSUMPTION: mod 65 if > 65
    # The expected RGB value = triad2 * 0x10000 + triad5 * 0x100 + triad3
    expected_rgb = triad2 * 0x10000 + triad5 * 0x100 + triad3
    # ASSUMPTION: skipping actual GetPixel verification
    # In a real keygen, you would need to query the crackme's window pixel here.
    
    return True  # ASSUMPTION: pixel check passes (cannot verify without crackme)

def keygen(name):
    """
    Generate a serial for the given name.
    
    We can only satisfy the checks we know:
    - name length >= 4
    - triad3 = ASCII(name[2]) - 2
    - Other triads: we pick arbitrary valid values since GetPixel check
      cannot be satisfied without the running crackme.
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long")
    
    # Triad3 is determined by the third character of the name
    triad3 = ord(name[2]) - 2
    
    # triad3 must be 0-999 to fit in 3 digits
    if not (0 <= triad3 <= 999):
        raise ValueError("Third character of name produces out-of-range triad3")
    
    # ASSUMPTION: pick arbitrary values for other triads
    # These would need to match a specific pixel in the crackme window
    triad1 = 100  # Y coordinate (arbitrary)
    triad2 = 0    # high byte of RGB (arbitrary)
    triad4 = 50   # X coordinate (arbitrary)
    triad5 = 0    # mid byte of RGB (arbitrary)
    
    serial = (
        f"{triad1:03d}"
        f"{triad2:03d}"
        f"{triad3:03d}"
        f"{triad4:03d}"
        f"{triad5:03d}"
    )
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
