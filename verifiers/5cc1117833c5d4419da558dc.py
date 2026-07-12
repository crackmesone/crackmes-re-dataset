# Keygen and verifier for EasyCrack - Much0l0k0 by paypain
# Algorithm fully determined from multiple writeups.

def count_special(s):
    """
    Count characters in the special ranges:
      0x23..0x2B  (i.e., '#$%&\'()*+')  -- strictly: '"' < c < ','
      0x3C..0x40  (i.e., '<=>?@')       -- strictly: ';' < c < 'A'
    """
    count = 0
    for c in s:
        o = ord(c)
        # '"' == 0x22, ',' == 0x2C => range 0x23..0x2B
        # ';'  == 0x3B, 'A' == 0x41 => range 0x3C..0x40
        if (0x22 < o < 0x2C) or (0x3B < o < 0x41):
            count += 1
    return count


def verify(name, serial):
    """
    The 'name' parameter is ignored by the crackme (it only uses 'check' as argv[1]).
    'serial' corresponds to argv[2].

    Checks:
      1. len(serial) == 39
      2. Exactly 4 dashes at positions 7, 15, 23, 31
      3. serial[7], serial[15], serial[23], serial[31] are all '-'
      4. Section 0 (indices 0-6)   has >0 special chars
         Section 1 (indices 8-14)  has >1 special chars
         Section 2 (indices 16-22) has >2 special chars
         Section 3 (indices 24-30) has >3 special chars
         Section 4 (indices 32-38) has >4 special chars
    """
    # Check 1: length must be 39
    if len(serial) != 39:
        return False

    # Check 2 & 3: dashes at positions 7, 15, 23, 31
    dash_positions = [7, 15, 23, 31]
    for pos in dash_positions:
        if serial[pos] != '-':
            return False

    # Check: exactly 4 dashes total
    if serial.count('-') != 4:
        return False

    # Extract the 5 sections (7 chars each, separated by '-')
    sections = [
        serial[0:7],    # indices 0-6
        serial[8:15],   # indices 8-14
        serial[16:23],  # indices 16-22
        serial[24:31],  # indices 24-30
        serial[32:39],  # indices 32-38
    ]

    # Check special char counts per section
    thresholds = [0, 1, 2, 3, 4]  # count must be > threshold
    for i, (section, threshold) in enumerate(zip(sections, thresholds)):
        if count_special(section) <= threshold:
            return False

    return True


def keygen(name=None):
    """
    Generate a valid serial. The 'name' parameter is ignored by the algorithm.
    Strategy: fill every character position with '*' (0x2A), which is in the
    special range 0x23..0x2B, giving 7 special chars per section.
    All sections will easily satisfy their thresholds.
    """
    # '*' = 0x2A is in range (0x22, 0x2C), so it counts as special.
    # 7 '*' per section => section 0: 7>0, section 1: 7>1, ..., section 4: 7>4
    section = '*' * 7
    serial = '-'.join([section] * 5)
    assert verify(name, serial), "keygen produced invalid serial!"
    return serial


def keygen_varied(name=None):
    """
    Generate a more varied valid serial using random characters.
    """
    import random
    # Special chars from both ranges
    special_chars = [chr(c) for c in range(0x23, 0x2C)] + [chr(c) for c in range(0x3C, 0x41)]
    # Non-special printable chars (letters and digits)
    normal_chars = [chr(c) for c in range(ord('a'), ord('z')+1)] + \
                   [chr(c) for c in range(ord('0'), ord('9')+1)]

    while True:
        sections = []
        for i in range(5):
            required = i + 1  # must be > i, so at least i+1 special chars
            section = []
            # Place exactly 'required' special chars, rest normal
            num_special = random.randint(required, 7)
            for j in range(7):
                if j < num_special:
                    section.append(random.choice(special_chars))
                else:
                    section.append(random.choice(normal_chars))
            random.shuffle(section)
            sections.append(''.join(section))
        serial = '-'.join(sections)
        if verify(name, serial):
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
            print(_sv)
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
