# Reverse-engineered from CRM1KEY.PAS and the assembly writeup
# The serial format is: '1' + 4-digit-a + 4-digit-b
# where a and b are 0..9999, (a XOR b) mod <name_mod> == 0xD (13)
# and neither a nor b contain any of the chars '1','3','5','7','9','#'
#
# The modulus depends on the registered name/username:
#   '1'          -> mod 0x31 (49)
#   'Vncracking' -> mod 0x20 (32)
#   'luucorp'    -> mod 0x62 (98)
# For other names the modulus is not fully determined from the text.
#
# The assembly shows the name is split into two halves based on some character
# classification (a bitmap at 0x427840), the halves are XOR-summed to get DI,
# then (first_half_value XOR second_half_value) mod DI == 0xD
# The exact split/XOR logic is partially reconstructed below.

def _compute_modulus(name):
    """ASSUMPTION: The modulus is the XOR of all character values in the name.
    This is inferred from the assembly loop at 0042606C-00426084 which XORs
    bytes of the second part into DI. The exact character classification
    (bitmap at 427840) that splits the name into two halves is unknown.
    We fall back to known values for known names."""
    known = {
        '1': 0x31,
        'vncracking': 0x20,
        'luucorp': 0x62,
    }
    lower = name.lower()
    if lower in known:
        return known[lower]
    # ASSUMPTION: fallback - XOR all character ordinals
    mod = 0
    for ch in name:
        mod ^= ord(ch)
    return mod if mod != 0 else 0x31


BAD_CHARS = set('13579#')


def _has_bad_char(s):
    """Return True if string contains any of '1','3','5','7','9','#'"""
    return any(c in BAD_CHARS for c in s)


def verify(name, serial):
    """
    Verify a serial for a given name.
    Serial format: '1' + 4-digit-A + 4-digit-B (total 9 chars)
    Condition: (A XOR B) mod modulus == 13 (0xD)
    Neither A nor B (as strings) may contain chars from '13579#'
    """
    if not serial or serial[0] != '1':
        return False
    if len(serial) != 9:
        return False
    part_a = serial[1:5]
    part_b = serial[5:9]
    if not part_a.isdigit() or not part_b.isdigit():
        return False
    if _has_bad_char(part_a) or _has_bad_char(part_b):
        return False
    a = int(part_a)
    b = int(part_b)
    modulus = _compute_modulus(name)
    if modulus == 0:
        return False
    return (a ^ b) % modulus == 0xD


def keygen(name):
    """Generate all valid serials for the given name (0..9999 x 0..9999)."""
    modulus = _compute_modulus(name)
    if modulus == 0:
        return
    for a in range(10000):
        sa = str(a).zfill(4)
        if _has_bad_char(sa):
            continue
        for b in range(10000):
            if (a ^ b) % modulus == 0xD:
                sb = str(b).zfill(4)
                if not _has_bad_char(sb):
                    yield '1' + sa + sb



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
