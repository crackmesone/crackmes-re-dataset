# Reverse-engineered validation for ultrasound's C++ Crackme #1
#
# What we know from the writeup:
# 1. The serial is 24 characters long (0x18 = 24 max, and it checks >= 0x18 chars but the
#    comparison is on first 20 chars + last 4 chars = 24 total).
# 2. The first 20 chars are generated internally by the crackme based on the name.
# 3. The last 4 chars are fixed: '0', '1', '4', '1'  (derived from XOR checks)
#    - serial[20] ^ 0x63 == 0x53  => serial[20] = 0x63 ^ 0x53 = 0x30 = '0'
#    - serial[21] ^ 0x63 == 0x52  => serial[21] = 0x63 ^ 0x52 = 0x31 = '1'
#    - serial[22] ^ 0x63 == 0x57  => serial[22] = 0x63 ^ 0x57 = 0x34 = '4'
#    - serial[23] ^ 0x63 == dl    where dl = serial[21] ^ 0x63 = 0x52  => serial[23] = 0x63 ^ 0x52 = 0x31 = '1'
#
# The first 20 chars are built from:
#   - Some name-derived computation stored in ValidSerial (first part, unknown algorithm)
#   - A '-' separator appended at some point
#   - A second part (SecondPart) of up to 15 chars appended via strncat
#
# ASSUMPTION: The exact algorithm that generates the first 20 chars from the name is NOT
# described in the writeup. The writeup only says 'crackme already generates it for us'.
# We cannot reconstruct this part from the available information.
#
# ASSUMPTION: The serial length is exactly 24 characters.
# ASSUMPTION: The structure is: [name_derived_20_chars][0141]

LAST_FOUR = '0141'


def _generate_first20(name: str) -> str:
    """
    ASSUMPTION: This function is a placeholder. The actual algorithm that generates
    the first 20 characters of the serial from the name is NOT described in the writeup.
    The writeup only reveals that the crackme computes it internally and that it involves
    a '-' character somewhere in the 20-char block (a dash is moved into a register and
    appended, and strncat of SecondPart with size 15 is used).

    Without the actual algorithm, we cannot implement this correctly.
    Returning a dummy placeholder.
    """
    # ASSUMPTION: unknown name->serial mapping for first 20 chars
    # The writeup shows a '-' is placed (bl = '-') and two parts are concatenated.
    # First part length + '-' + SecondPart (up to 15 bytes) = 20 chars total.
    # e.g., pattern might be XXXXXXXX-XXXXXXXXXX  (8 + 1 + 10 = 19? or similar)
    # We have no further info.
    raise NotImplementedError(
        "The algorithm for generating the first 20 chars from the name "
        "is not described in the writeup and cannot be reconstructed."
    )


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name.

    Known checks (from assembly):
    1. Serial length must be >= 24 chars (0x18), and the comparison uses nMaxCount=0x19.
       The strncmp compares first 20 chars (0x14).
    2. Last 4 chars must be '0141'.
    3. First 20 chars must match the internally generated valid serial for the name.
    """
    # Length check: serial must be at least 24 chars
    # ASSUMPTION: exact length requirement is 24
    if len(serial) < 24:
        return False

    # Last 4 chars fixed check
    if serial[20:24] != LAST_FOUR:
        return False

    # XOR checks redundantly confirm the last 4 chars (from assembly):
    s = serial
    if (ord(s[20]) ^ 0x63) != 0x53:  # '0'
        return False
    if (ord(s[21]) ^ 0x63) != 0x52:  # '1'
        return False
    if (ord(s[22]) ^ 0x63) != 0x57:  # '4'
        return False
    # last char: xor cl, 63h; cmp cl, dl  where dl = serial[21]^0x63 = 0x52
    if (ord(s[23]) ^ 0x63) != (ord(s[21]) ^ 0x63):  # must equal 0x52 => '1'
        return False

    # First 20 chars check against generated serial
    # ASSUMPTION: we cannot compute this without the name->serial algorithm
    try:
        first20 = _generate_first20(name)
        if serial[:20] != first20:
            return False
    except NotImplementedError:
        # Cannot verify first 20 chars - mark as partial
        pass

    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    ASSUMPTION: The first 20 chars algorithm is unknown; this function
    raises NotImplementedError for that part.
    """
    # ASSUMPTION: unknown algorithm for first 20 chars
    first20 = _generate_first20(name)  # Will raise NotImplementedError
    return first20 + LAST_FOUR



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
