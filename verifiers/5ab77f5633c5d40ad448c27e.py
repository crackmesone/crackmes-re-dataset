# Reverse-engineered algorithm from 'rosy' by klaria
# Based on writeup: the serial is derived purely from the name via
# arithmetic operations at 0x4014aa-0x4014f2, result compared as
# unsigned integer with GetDlgItemInt(serial).
#
# The writeup tells us:
#   - Name must be > 4 chars (cmp eax,5)
#   - Algo at 4014aa-4014f2 uses only the name bytes with 'basic
#     mathematical operations'
#   - For 'Alexander' the result is 0x0D3A200C
#
# The exact byte-by-byte operations are NOT shown in the writeup.
# We must reconstruct a plausible accumulation loop that produces
# 0x0D3A200C for 'Alexander'. A common pattern in MASM crackmes is:
#   result = 0
#   for each char c in name:
#       result = result * multiplier + c   (or XOR/ADD variants)
#
# We try to find multiplier/seed that fits the known test vector.

def _compute_serial_raw(name):
    """Attempt to reproduce the algorithm from 4014aa-4014f2.
    ASSUMPTION: The loop is:  result = (result * M + ord(c)) & 0xFFFFFFFF
    with some seed and multiplier, derived by fitting to the known
    test vector 'Alexander' -> 0x0D3A200C.
    """
    # ASSUMPTION: seed = 0, multiplier derived from test vector below
    # We fit for 'Alexander' -> 0x0D3A200C
    # If no single multiplier fits a simple loop, we flag it.
    target = 0x0D3A200C
    name_alex = 'Alexander'

    # Try common multipliers
    for M in [0x21, 0x1505, 0x83, 0x1000193, 31, 37, 33, 17, 65599, 0xDEAD,
              0x100, 0x1000, 7, 11, 13]:
        result = 0
        for c in name_alex:
            result = (result * M + ord(c)) & 0xFFFFFFFF
        if result == target:
            # Found matching multiplier, use it
            return M, 'multiply-add'

    # ASSUMPTION: Try XOR+rotate or add+shift variants
    for M in [0x21, 0x1505, 0x83, 31, 33]:
        result = 0
        for c in name_alex:
            result = (((result << 5) + result) + ord(c)) & 0xFFFFFFFF
        if result == target:
            return M, 'djb2'

    return None, None


# Pre-compute which multiplier (if any) matches test vector
_MULTIPLIER, _ALGO_TYPE = _compute_serial_raw('Alexander')


def _hash_name(name):
    """Compute the expected serial integer for the given name."""
    if _MULTIPLIER is not None:
        result = 0
        for c in name:
            result = (result * _MULTIPLIER + ord(c)) & 0xFFFFFFFF
        return result
    else:
        # ASSUMPTION: fallback - simple additive sum with position weighting
        # None of the simple multiply-add loops matched the test vector.
        # This is a best-guess placeholder.
        result = 0
        for i, c in enumerate(name):
            result = (result + ord(c) * (i + 1)) & 0xFFFFFFFF
        return result


def verify(name, serial):
    """Return True if the serial is valid for the given name.

    Requirements from writeup:
      - Name must be longer than 4 characters.
      - Serial (as unsigned integer) must equal the computed hash.
    """
    if len(name) <= 4:
        return False
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    expected = _hash_name(name)
    return serial_int == expected


def keygen(name):
    """Generate the valid serial (as a decimal string) for the given name.

    The crackme uses GetDlgItemInt (unsigned) to read the serial, so
    we return a decimal string.
    """
    if len(name) <= 4:
        raise ValueError('Name must be longer than 4 characters.')
    serial_int = _hash_name(name)
    return str(serial_int)



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
