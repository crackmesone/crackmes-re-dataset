# razkom_v1.1 keygen / verifier
#
# Key format: XXX-XXX-XXX-XXX-XXX-XXX  (23 chars, dashes at positions 3,7,11,15,19)
# Each block: positions 0,1 are free uppercase letters A-Z
#             position 2 is fixed: (char0 + char1) % 26 + 65
# The six third-chars must spell R-A-Z-K-O-M exactly.
#
# From IDA decompilation (solution writeups):
#   block0[2] == 'R'  (ASCII 82)
#   block1[2] == 'A'  (ASCII 65)
#   block2[2] == 'Z'  (ASCII 90)
#   block3[2] == 'K'  (ASCII 75)
#   block4[2] == 'O'  (ASCII 79)
#   block5[2] == 'M'  (ASCII 77)
#
# XOR decryption (for reference, not needed for verify()):
#   plaintext[i] = ciphertext[i] ^ key_char[i % 23]   for i in 0..126

ENCRYPTED = bytes([
    0x11,0x2E,0x3C,0x4A,0x33,0x20,0x35,0x58,0x36,0x20,0x2E,
    0x44,0x24,0x2F,0x38,0x0C,0x45,0x18,0x20,0x58,0x6D,0x32,
    0x22,0x3E,0x37,0x37,0x49,0x61,0x2C,0x38,0x0D,0x3C,
    0x28,0x28,0x5E,0x3F,0x61,0x28,0x5F,0x2E,0x22,0x24,
    0x40,0x28,0x6F,0x47,0x02,0x2D,0x37,0x4C,0x32,0x24,0x61,
    0x41,0x3F,0x35,0x7A,0x40,0x2E,0x61,0x20,0x43,0x20,0x36,
    0x6F,0x5A,0x25,0x20,0x39,0x72,0x38,0x3D,0x58,0x61,0x35,
    0x29,0x42,0x2F,0x26,0x32,0x59,0x6B,0x2E,0x2D,0x0D,0x26,
    0x35,0x6F,0x44,0x23,0x61,0x39,0x3A,0x24,0x72,0x4E,0x2E,
    0x2C,0x2C,0x48,0x34,0x35,0x29,0x03,0x41,0x12,0x2E,0x4E,
    0x3D,0x24,0x3B,0x0D,0x3A,0x2E,0x3F,0x36,0x7B,0x72,0x0A,
    0x03,0x00,0x1B,0x62,0x15,0x0A,0x1B,0x0A,0x4B,0x52,0x41,0x5A,
    0x4B,0x4F,0x4D,
])

# The six required third characters (spell RAZKOM)
REQUIRED = [ord(c) for c in 'RAZKOM']


def _check_format(serial: str) -> bool:
    """Check that serial matches format XXX-XXX-XXX-XXX-XXX-XXX (23 chars, dashes)."""
    if len(serial) != 23:
        return False
    for pos in (3, 7, 11, 15, 19):
        if serial[pos] != '-':
            return False
    return True


def verify(name: str, serial: str) -> bool:
    """
    Validate the key against the algorithm extracted from razkom_v1.1.
    The 'name' parameter is ignored -- the crackme only checks the serial.
    """
    # Format check
    if not _check_format(serial):
        return False

    # All chars (non-dash) must be uppercase A-Z
    blocks_str = serial.replace('-', '')
    if not all('A' <= c <= 'Z' for c in blocks_str):
        return False

    # Extract the six 3-char blocks
    parts = serial.split('-')
    if len(parts) != 6:
        return False

    for i, part in enumerate(parts):
        if len(part) != 3:
            return False
        a = ord(part[0])
        b = ord(part[1])
        c = ord(part[2])
        # Check: (a + b) % 26 + 65 == c
        if (a + b) % 26 + 65 != c:
            return False
        # Check: c must be the i-th letter of RAZKOM
        if c != REQUIRED[i]:
            return False

    return True


def keygen(name: str = '') -> str:
    """
    Generate a valid key.  We iterate over all A-Z pairs and pick the first
    pair (a, b) such that (a+b)%26+65 equals the required character.
    The 'name' parameter is ignored (algorithm is name-independent).
    Returns a single valid serial string.
    """
    blocks = []
    for target in REQUIRED:
        found = False
        for a in range(65, 91):  # A..Z
            for b in range(65, 91):
                if (a + b) % 26 + 65 == target:
                    blocks.append(chr(a) + chr(b) + chr(target))
                    found = True
                    break
            if found:
                break
    return '-'.join(blocks)


def keygen_all() -> list:
    """Generate ALL valid keys (26 choices per block => 26^6 = 308,915,776 total,
    but only ~25 valid (a,b) pairs exist per target character, so much fewer)."""
    from itertools import product
    block_options = []
    for target in REQUIRED:
        opts = []
        for a in range(65, 91):
            for b in range(65, 91):
                if (a + b) % 26 + 65 == target:
                    opts.append(chr(a) + chr(b) + chr(target))
        block_options.append(opts)
    keys = []
    for combo in product(*block_options):
        keys.append('-'.join(combo))
    return keys


def decrypt(serial: str) -> str:
    """XOR-decrypt the embedded ciphertext using the key."""
    key = serial.encode('ascii')
    klen = len(key)  # should be 23
    return ''.join(chr(ENCRYPTED[i] ^ key[i % klen]) for i in range(len(ENCRYPTED)))



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
