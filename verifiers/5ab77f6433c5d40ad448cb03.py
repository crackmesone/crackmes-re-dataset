# Reverse-engineered keygen for crackme_1 by phrozen_crew
# Based on the Keygen.asm source from the solution writeup.
#
# The algorithm uses a lookup table (Spec table) indexed by character value.
# Each entry is two words: (value_word, type_word).
# The 'special value' (spec_val) is computed by XORing (or summing) the first words
# for each character in the name string.
# The password is then derived from spec_val using wsprintfA with format "%.4lu"
# (i.e., zero-padded 4-digit decimal), combined with some arithmetic.
#
# ASSUMPTION: The exact combination/arithmetic to produce the final serial from
# spec_val is not fully shown (writeup truncated). Based on the assembly structure
# (wsprintfA with "%.4lu" format, ValueA/ValueB buffers, and the table), the most
# likely algorithm is:
#   1. For each character in name, look up Spec table entry -> get first word.
#   2. XOR or add those words together to get spec_val.
#   3. Serial = zero-padded 4-digit decimal of spec_val (mod 10000).
#
# ASSUMPTION: Characters with digits cause rejection (see NumberTxt message).
# ASSUMPTION: If spec_val leads to a 'bad case' (BaadTxt), there is no valid serial.
# ASSUMPTION: The combination operation is XOR of the first words (common pattern).
# ASSUMPTION: The second word (type) may modify how the first word contributes,
#             but its exact role is unknown from the truncated writeup.

# Build the Spec table from the assembly data.
# Format: index -> (first_word_octal_decimal, second_word)
# The values in the .asm are octal literals (leading zeros in assembler = octal? No,
# in MASM, numbers without suffix are decimal. So 0024 = 24 decimal, 0004 = 4 decimal.
# ASSUMPTION: All values are decimal (MASM default).

SPEC = {}

# Manually transcribed from the assembly listing (odd indices have data, even are 0,0)
# Format: char_code -> (val, typ)
raw_spec = {
    0x0F: (24, 4),
    0x11: (28, 2),
    0x13: (68, 2),
    0x15: (200, 2),
    0x17: (80, 2),
    0x19: (46, 8),
    0x1B: (42, 2),
    0x1D: (40, 2),
    0x1F: (46, 2),
    0x21: (44, 2),
    0x23: (262, 4),
    0x25: (48, 2),
    0x27: (284, 2),
    0x29: (466, 2),
    0x2B: (402, 2),
    0x2D: (62, 4),
    0x2F: (62, 2),
    0x31: (60, 2),
    0x33: (66, 2),
    0x35: (64, 2),
    0x37: (64, 4),
    0x39: (68, 2),
    0x3B: (424, 2),
    0x3D: (442, 2),
    0x3F: (200, 2),
    0x41: (464, 4),
    0x43: (82, 2),
    0x45: (80, 2),
    0x47: (86, 2),
    0x49: (84, 2),
    0x4B: (80, 8),
    0x4D: (88, 2),
    0x4F: (248, 2),
    0x51: (2202, 2),
    0x53: (260, 2),
    0x55: (264, 4),
    0x57: (620, 2),
    0x59: (282, 2),
    0x5B: (284, 2),
    0x5D: (666, 2),
    0x5F: (864, 4),
    0x61: (884, 2),
    0x63: (2288, 2),
    0x65: (8802, 2),
    0x67: (4028, 2),
    0x69: (2222, 4),
    0x6B: (2044, 2),
    0x6D: (2086, 2),
    0x6F: (0, 0),  # ooooops :/ -> leads to bad case
    0x71: (806, 2),
    0x73: (822, 4),
    0x75: (2000, 2),
    0x77: (844, 2),
    0x79: (862, 2),
    0x7B: (2840, 2),
    0x7D: (880, 8),
    0x7F: (2424, 2),
    0x81: (402, 2),
    0x83: (404, 2),
    0x85: (2804, 2),
    0x87: (422, 4),
    0x89: (426, 2),
    0x8B: (428, 2),
    0x8D: (2408, 2),
    0x8F: (440, 2),
    0x91: (4222, 4),
    0x93: (2804, 2),
    0x95: (462, 2),
    0x97: (464, 2),
    0x99: (2000, 2),
    0x9B: (2024, 4),
    0x9D: (486, 2),
    0x9F: (488, 2),
    0xA1: (4680, 2),
    0xA3: (6046, 2),
    0xA5: (2822, 4),
    0xA7: (6862, 2),
    0xA9: (2208, 2),
    0xAB: (4628, 2),
    0xAD: (2260, 2),
    0xAF: (880, 8),
    0xB1: (4086, 2),
    0xB3: (4844, 2),
    0xB5: (2006, 2),
    0xB7: (2024, 2),
    0xB9: (2422, 4),
    0xBB: (202, 2),
    0xBD: (200, 2),
    0xBF: (206, 2),
    0xC1: (204, 2),
    0xC3: (6062, 4),
    0xC5: (208, 2),
    0xC7: (608, 2),
    0xC9: (2226, 2),
    0xCB: (620, 2),
    0xCD: (222, 4),
    0xCF: (222, 2),
    0xD1: (220, 2),
    0xD3: (226, 2),
    0xD5: (224, 2),
    0xD7: (224, 4),
    0xD9: (228, 2),
    0xDB: (668, 2),
    0xDD: (2000, 2),
    0xDF: (680, 2),
    0xE1: (2046, 8),
    0xE3: (242, 2),
    0xE5: (240, 2),
    0xE7: (246, 2),
    0xE9: (244, 2),
    0xEB: (6824, 4),
    0xED: (248, 2),
    0xEF: (2640, 2),
    0xF1: (2666, 2),
    0xF3: (2202, 2),
    0xF5: (262, 4),
    0xF7: (262, 2),
    0xF9: (260, 2),
    0xFB: (266, 2),
    0xFD: (264, 2),
    0xFF: (264, 4),
}

for code in range(256):
    if code in raw_spec:
        SPEC[code] = raw_spec[code]
    else:
        SPEC[code] = (0, 0)


def compute_spec_val(name: str) -> int:
    """
    Compute the 'special value' from the name string.
    ASSUMPTION: Each character's Spec entry first word is XORed together.
    ASSUMPTION: The table is indexed directly by the ASCII value of the character.
    Characters that are digits cause rejection.
    """
    spec_val = 0
    for ch in name:
        c = ord(ch)
        val, typ = SPEC[c & 0xFF]
        # ASSUMPTION: XOR accumulation
        spec_val ^= val
    return spec_val


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: Serial must be the zero-padded 4-digit decimal of spec_val.
    ASSUMPTION: Name must not contain digits.
    ASSUMPTION: spec_val == 0 is a 'bad case' with no valid serial.
    """
    if not name:
        return False
    # Reject digits in name
    for ch in name:
        if ch.isdigit():
            return False
    spec_val = compute_spec_val(name)
    # Bad case: spec_val is 0 (or leads to no valid password)
    if spec_val == 0:
        return False
    # ASSUMPTION: serial is "%04d" % spec_val (taking lower 4 decimal digits)
    expected = "%04d" % (spec_val % 10000)
    return serial.strip() == expected


def keygen(name: str) -> str:
    """
    Generate serial for given name.
    Returns None if name is invalid or leads to a bad case.
    """
    if not name:
        return None
    for ch in name:
        if ch.isdigit():
            return None
    spec_val = compute_spec_val(name)
    if spec_val == 0:
        return None
    return "%04d" % (spec_val % 10000)



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
