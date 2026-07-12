import random

def parse_key_a(key_a_str):
    """
    Parse the A key string.
    Format: A-XXXXXXXX-XXXXXXXX-XXXXXXXXX-XXXXXXXXX
    Strips leading 'A-', removes spaces, then extracts:
      a.a = first 8 chars as int
      a.b = next 8 chars as int (after '-')
      a.c = next 8 chars as int (after '-') -- NOTE: 9th char of this segment is IGNORED (bug in original)
      a.d = remaining chars as int (after '-', 9 chars)
    """
    text = key_a_str
    # Remove leading 'A-' (first 2 chars)
    if text.startswith('A-') or text.startswith('a-'):
        text = text[2:]
    # Remove spaces
    text = text.replace(' ', '')
    # Extract a.a: first 8 chars
    aa = int(text[:8])
    text = text[9:]  # skip 8 digits + '-'
    # Extract a.b: next 8 chars
    ab = int(text[:8])
    text = text[9:]  # skip 8 digits + '-'
    # Extract a.c: next 8 chars (9th is ignored - known bug)
    ac = int(text[:8])
    text = text[10:]  # skip 9 digits + '-' (delete 10 chars)
    # Extract a.d: remaining
    ad = int(text)
    return aa, ab, ac, ad

def parse_key_b(key_b_str):
    """
    Parse the B key string.
    Format: B-XXXXXXXXX-XXXXXXXXX
    Strips leading 'B-', removes spaces, then extracts:
      b.a = first 9 chars as int
      b.b = remaining 9 chars as int
    """
    dest = key_b_str
    if dest.startswith('B-') or dest.startswith('b-'):
        dest = dest[2:]
    dest = dest.replace(' ', '')
    ba = int(dest[:9])
    dest = dest[10:]  # skip 9 digits + '-'
    bb = int(dest)
    return ba, bb

def verify(name, serial):
    """
    The crackme does not use the name at all.
    serial should be a tuple (key_a_str, key_b_str) or a string 'A-...|B-...'
    We support both forms.
    """
    if isinstance(serial, str):
        parts = serial.split('|')
        key_a_str = parts[0].strip()
        key_b_str = parts[1].strip()
    else:
        key_a_str, key_b_str = serial

    try:
        aa, ab, ac, ad = parse_key_a(key_a_str)
        ba, bb = parse_key_b(key_b_str)
    except (ValueError, IndexError):
        return False

    # Check: (a.a XOR a.b) == b.a  AND  (a.c XOR a.d) == b.b
    return ((aa ^ ab) == ba) and ((ac ^ ad) == bb)

def keygen(name):
    """
    Generate a valid (key_a, key_b) pair.
    name is ignored (crackme does not use it).
    Key A format: A-XXXXXXXX-XXXXXXXX-XXXXXXXXX-XXXXXXXXX
      a.a: 8-digit number (0..99999999)
      a.b: 8-digit number (0..99999999)
      a.c: 9-digit number, but only first 8 digits used in check; 9th is arbitrary
      a.d: 9-digit number (0..999999999)
    Key B format: B-XXXXXXXXX-XXXXXXXXX
      b.a = a.a XOR a.b  (up to 9 digits)
      b.b = a.c XOR a.d  (up to 9 digits, but a.c only uses first 8 digits)
    """
    # Generate a.a and a.b as 8-digit numbers
    aa = random.randint(0, 99999999)
    ab = random.randint(0, 99999999)
    # Generate a.c as 9-digit number (9th digit arbitrary, first 8 used in check)
    # We pick 8 significant digits and a random 9th digit
    ac_significant = random.randint(0, 99999999)  # 8 digits used in check
    ac_9th = random.randint(0, 9)  # arbitrary 9th digit
    # a.c as stored in the field: 9 chars, but parse reads first 8
    # The field holds a 9-digit number; first 8 digits = ac_significant (zero-padded)
    ac_str = str(ac_significant).zfill(8) + str(ac_9th)
    ac = int(ac_str[:8])  # what parse actually reads
    # Generate a.d as 9-digit number
    ad = random.randint(0, 999999999)
    # Compute key B values
    ba = aa ^ ab
    bb = ac ^ ad  # ac here is only the 8-digit value read by parse
    # Format key A: A-XXXXXXXX-XXXXXXXX-XXXXXXXXX-XXXXXXXXX
    aa_str = str(aa).zfill(8)
    ab_str = str(ab).zfill(8)
    # ac field is 9 chars
    ac_field = str(ac_significant).zfill(8) + str(ac_9th)
    ad_str = str(ad).zfill(9)
    key_a = f'A-{aa_str}-{ab_str}-{ac_field}-{ad_str}'
    # Format key B: B-XXXXXXXXX-XXXXXXXXX
    ba_str = str(ba).zfill(9)
    bb_str = str(bb).zfill(9)
    key_b = f'B-{ba_str}-{bb_str}'
    return key_a + '|' + key_b



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
