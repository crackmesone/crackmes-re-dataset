# Upgraded Levels Keygen - verify/keygen for Levels 1-3 (and partial Level 4)
# Based on write-up by MrEdMakes

# ---------------------------------------------------------------------------
# LEVEL 1
# Each character has its 3rd bit (0-indexed bit 2, value 4) toggled.
# Input is transformed: char ^ 4, then compared to expected password.
# The write-up does not state the expected password for level 1 explicitly;
# ASSUMPTION: the check simply verifies the transformed string equals some
# hardcoded target. Since the transform is self-inverse (XOR 4), we can
# say: valid inputs are any string whose XOR-4 transform equals the stored
# password. Without knowing the stored password we cannot implement verify
# for level 1, but we implement the transform.

def _xor_bit3(s):
    """Toggle bit 2 (value 4) of every character."""
    return ''.join(chr(ord(c) ^ 4) for c in s)

def verify_level1(password):
    # ASSUMPTION: the stored (target) password after transform is unknown;
    # the write-up only describes the transform, not the target string.
    # We re-implement the transform and leave the target as a placeholder.
    # ASSUMPTION: target is unknown; returning NotImplemented placeholder.
    transformed = _xor_bit3(password)
    # ASSUMPTION: actual target string not given in write-up for level 1
    raise NotImplementedError("Level 1 target password not stated in write-up")

def keygen_level1():
    # ASSUMPTION: target not known; cannot produce valid input.
    raise NotImplementedError("Level 1 target password not stated in write-up")


# ---------------------------------------------------------------------------
# LEVEL 2
# Transform: for each character at index i:
#   transformed[i] = (char ^ 0b00010010) + i   (flip bits 1 and 4, i.e. values 2 and 16)
# The stored/expected transformed password is "1d86ce".
# Additionally, the first command-line argument must start with 'e'.
# Working backwards: stored = "1d86ce", so input[i] = (ord(stored[i]) - i) ^ 0b00010010

LEVEL2_STORED = "1d86ce"
# Bits flipped: bit1 (value 2) and bit4 (value 16) => mask = 0x12
LEVEL2_MASK = 0x12

def _level2_transform(s):
    """Apply level 2 transform to input string."""
    result = []
    for i, c in enumerate(s):
        result.append(chr((ord(c) ^ LEVEL2_MASK) + i))
    return ''.join(result)

def verify_level2(password, argv1_starts_with_e=True):
    """Verify level 2 password. argv1 is the first CLI argument."""
    if not argv1_starts_with_e:
        return False
    transformed = _level2_transform(password)
    return transformed == LEVEL2_STORED

def keygen_level2():
    """Generate the valid level 2 password."""
    # Invert: input[i] = (ord(stored[i]) - i) ^ LEVEL2_MASK
    password = []
    for i, c in enumerate(LEVEL2_STORED):
        password.append(chr((ord(c) - i) ^ LEVEL2_MASK))
    return ''.join(password)

# Known answer from write-up: "#q$!Mr" -> transforms to "1d86ce"
assert keygen_level2() == "#q$!Mr", f"keygen_level2 mismatch: {keygen_level2()}"


# ---------------------------------------------------------------------------
# LEVEL 3
# Password must be "01267567".
# The program must be called with argument "0x3".
# ASSUMPTION: verification is a direct string comparison after some setup
# (strncat builds "0x3"); the password check is against "01267567".

LEVEL3_PASSWORD = "01267567"
LEVEL3_ARG = "0x3"

def verify_level3(password, cli_arg=None):
    """Verify level 3 password and CLI argument."""
    if cli_arg != LEVEL3_ARG:
        return False
    return password == LEVEL3_PASSWORD

def keygen_level3():
    return LEVEL3_PASSWORD, LEVEL3_ARG


# ---------------------------------------------------------------------------
# LEVEL 4 (partial - based on keygen script in write-up)

wizardHatTable  = {"@": "Q", "\\": "$", "&": "@"}

wizardWordTable = {
    "Hunga":   ["&", "+JQ&"],
    "Bunga":   ["&", "+JQ&"],
    "Funga":   ["&", "+JQ&"],
    "Lunga":   ["+", "+Q%%"],
    "Skrunga": ["+", "+Q%%"],
}

prophecyTable = {
    "THIS": 1, "HATE": 1, "I": 1, "REVERSING": 1, "IS": 1,
    "COOL": 1, "STUPID": 1, "DECOMPILER": 1, "XOR": 1, "AND": 1,
    "KEYGEN": 1, "SYSCALL": 1, "CRACKME": 1, "DISASSEMBLER": 1,
    "DEBUGGER": 1, "OBFUSCATED": 1, "UNPACKED": 1, "PACKED": 1,
    "INJECTED": 1, "DAUNTING": 1, "AWESOME": 1,
    "ELEPHANT": -1, "RAINBOW": -1, "KEYBOARD": -1,
    "PORCUPINE": -1, "DAZZLING": -1, "UNIVERSE": -1,
    "GUITAR": -1, "PANCAKE": -1, "PARACHUTE": -1, "COMPUTER": -1,
    "MOUSE": -1, "CAT": -1, "SOUP": -1, "DIVINE": -1,
    "INTELLECT": -1, "THE": -1, "GETS": -1, "ME": -1, "YOU": -1,
}

def keygen_level4(wizard_hat, wizard_word, wizard_eyes, prophecy_words):
    """
    Generate level 4 password from visual clues in the prompt.
    wizard_hat   : one of '@', '\\', '&'
    wizard_word  : word before 'Shlunga', e.g. 'Hunga', 'Lunga', etc.
    wizard_eyes  : character used for eyes, e.g. '@', '$', '*', '+'
    prophecy_words: list of uppercase words appearing in the prophecy
    Returns 6-character password string.
    """
    password = ['.'] * 6

    # Clue 1: hat -> password[5]
    password[5] = wizardHatTable[wizard_hat]

    # Clue 2: word -> password[2] and remaining chars for clue 3
    char3, remaining = wizardWordTable[wizard_word]
    password[2] = char3

    # Clue 3: eyes -> password[1] and password[3]
    if wizard_eyes in ("@", "$"):
        password[1] = remaining[0]
        password[3] = remaining[1]
    else:  # '*' or '+'
        password[1] = remaining[2]
        password[3] = remaining[3]

    # Clue 4: prophecy score -> password[0] and password[4]
    score = sum(prophecyTable.get(w, 0) for w in prophecy_words)
    if score < 0:
        password[0] = 'Z'
        password[4] = '$'
    else:
        password[0] = '+'
        password[4] = '*'

    return ''.join(password)

def verify_level4(candidate, wizard_hat, wizard_word, wizard_eyes, prophecy_words):
    return candidate == keygen_level4(wizard_hat, wizard_word, wizard_eyes, prophecy_words)


# ---------------------------------------------------------------------------
# Generic dispatcher

def verify(name, serial):
    """
    name  = level identifier: '2', '3', or '4'
    serial = password string (for level 4, pass a tuple of (pw, hat, word, eyes, words))
    """
    if name == '2':
        return verify_level2(serial)
    elif name == '3':
        return verify_level3(serial, LEVEL3_ARG)
    elif name == '4':
        # ASSUMPTION: serial is tuple (password, hat, word, eyes, prophecy_words)
        pw, hat, word, eyes, pwords = serial
        return verify_level4(pw, hat, word, eyes, pwords)
    else:
        raise NotImplementedError(f"Level {name} not fully implemented")

def keygen(name):
    if name == '2':
        return keygen_level2()
    elif name == '3':
        pw, arg = keygen_level3()
        return f"{pw}  (run with arg: {arg})"
    else:
        raise NotImplementedError(f"Keygen for level {name} requires runtime prompt clues")



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
