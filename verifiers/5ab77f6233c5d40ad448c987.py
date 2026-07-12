import hashlib


def _remove_alpha_bugged(s: str) -> str:
    """
    Mimics the buggy char-removal: iterates with index i, and if chars[i]
    is alphabetic it removes it (but does NOT advance i), so two consecutive
    alphabetic chars means only the first is removed because after removal
    the next char slides into position i and i is incremented normally on
    the next loop iteration -- i.e. every other alpha in a run is kept.
    """
    chars = list(s)
    i = 0
    while i < len(chars):
        if chars[i].isalpha():
            chars.pop(i)
            # do NOT increment i; but the while loop will naturally go to i next
            # which is now the char that slid down -- matching the buggy behavior
        else:
            i += 1
    return ''.join(chars)


# The allowed chars decoded from numOnlyStr.cpp:
# Each value is (hex_val - 0x36EA) cast to chr
_RAW = [
    0x374B, 0x374C, 0x374D, 0x374E, 0x374F,
    0x3750, 0x3751, 0x3752, 0x3753, 0x3756,
    0x3757, 0x3758, 0x3759, 0x375A, 0x375B,
    0x375C, 0x375D, 0x375E, 0x375F, 0x3760,
    0x3764, 0x3763, 0x3761, 0x3762, 0x3755,
    0x3754, 0x37D2, 0x3715, 0x37E3, 0x37CA,
    0x37DC, 0x3714, 0x3719, 0x3726, 0x3728,
    0x3716, 0x3718, 0x3717, 0x3748, 0x37D6,
    0x3711, 0x3729, 0x370C,
]
KEY = 0x36EA
ALLOWED_CHARS = set(chr(v - KEY) for v in _RAW)

# From the writeup: allowed chars are digits and a few others but NO alpha chars.
# The check returns True (fail) if ANY char from ALLOWED_CHARS is found in password.
# So a valid password must contain NONE of those chars -- but also must be
# numeric only (the description says 'only numerical chars').
# ASSUMPTION: the ALLOWED_CHARS set decoded above represents the forbidden set
# (letters + some symbols). A valid serial must not contain any of those chars.
# In practice the decoded chars are letters a-z, A-Z and a few specials,
# so a numeric-only serial passes the first check.


def _passes_char_check(password: str) -> bool:
    """Return True if password contains none of the forbidden chars."""
    for ch in password:
        if ch in ALLOWED_CHARS:
            return False
    return True


def _derive_serial(password: str) -> str:
    """MD5 of password, then strip alpha chars (with the buggy method)."""
    md5_hex = hashlib.md5(password.encode('utf-8')).hexdigest()
    return _remove_alpha_bugged(md5_hex)


def verify(name: str, serial: str) -> bool:
    """
    Validate name/serial pair.
    1. Password (serial) must not contain any of the forbidden chars.
    2. The expected code is derived from MD5(serial) with alpha chars
       removed (buggy removal). That derived code must equal the serial.
    NOTE: The crackme does NOT use the username in the algorithm.
    """
    if not _passes_char_check(serial):
        return False
    expected = _derive_serial(serial)
    return serial == expected


def keygen(name: str) -> str:
    """
    Find a serial S such that:
      - S contains only digits (satisfies char check)
      - _remove_alpha_bugged(MD5(S)) == S
    Strategy: brute-force numeric strings. The MD5 of a numeric string is
    a 32-char hex string; after removing alpha chars (with buggy removal)
    we get a purely numeric substring. We search for a fixed point.
    For efficiency we iterate candidate lengths and values.
    """
    # ASSUMPTION: We search for a fixed point by iterating numeric strings
    # and checking if MD5->strip_alpha gives back the same string.
    # This is a brute-force approach; a smarter approach generates the
    # numeric-only candidate from the MD5 and checks it recursively.
    from itertools import product
    digits = '0123456789'
    # Try lengths 1..12 for tractability
    for length in range(1, 13):
        for combo in product(digits, repeat=length):
            candidate = ''.join(combo)
            derived = _derive_serial(candidate)
            if derived == candidate:
                return candidate
    # ASSUMPTION: If no short fixed point found, raise
    raise ValueError('No serial found in search range')



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
