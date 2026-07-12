import hashlib

# Based on solution writeup by Sphinx (Solution 1) for ScareByte's CrackMe #7
# The writeup was truncated but revealed:
# - Password is a constant string (Task 2): characters compared at specific offsets
# - Serial (Task 3) is user/name-based with:
#   - Name length must be > 6 and < 20
#   - Solution 3 includes RIPEMD-160 source (keygen uses RIPEMD-160)
# The keygen source files (Solution 3) include rmd160.c/h suggesting serial = RIPEMD-160 of some input
# The writeup was truncated before showing the full serial algorithm

# CONSTANT PASSWORD (Task 2)
# Characters at positions 0..11 reconstructed from the compare instructions:
# [0]='C', [1]='l', [2]='n', [3]='o', [4]=' ', [5]='i', [6]='g', [7]='u', [8]='o', [9]='n', [10]='R', [11]='n'
# => 'Clno iguo nRn' with space at index 4
# Reading in order: C(0) l(1) n(2) o(3) ' '(4) i(5) g(6) u(7) o(8) n(9) R(10) n(11)
CONSTANT_PASSWORD = 'Clno igunRn'  # ASSUMPTION: assembled from scrambled byte comparisons
# Correct assembly from the offsets:
# 0->C, 1->l, 2->n, 3->o, 4->' ', 5->i, 6->g, 7->u, 8->o, 9->n, 10->R, 11->n
CONSTANT_PASSWORD = 'Clno iguonRn'


def verify_password(password: str) -> bool:
    """Task 2: Check the constant password."""
    if len(password) != 12:
        return False
    expected = [
        (0,  0x43),  # 'C'
        (1,  0x6C),  # 'l'
        (2,  0x6E),  # 'n'
        (3,  0x6F),  # 'o'
        (4,  0x20),  # ' '
        (5,  0x69),  # 'i'
        (6,  0x67),  # 'g'
        (7,  0x75),  # 'u'
        (8,  0x6F),  # 'o'
        (9,  0x6E),  # 'n'
        (10, 0x52),  # 'R'
        (11, 0x6E),  # 'n'
    ]
    for idx, val in expected:
        if ord(password[idx]) != val:
            return False
    return True


def ripemd160(data: bytes) -> bytes:
    """Compute RIPEMD-160 hash."""
    # Python's hashlib supports ripemd160 on most platforms
    h = hashlib.new('ripemd160')
    h.update(data)
    return h.digest()


def serial_from_ripemd160(name: str, company: str = '') -> str:
    """Generate serial using RIPEMD-160 (from keygen source in Solution 3).
    ASSUMPTION: The exact input to RIPEMD-160 (name only, name+company, etc.) 
    and the exact formatting of the serial output are not fully described in 
    the truncated writeup. We assume name+company concatenated.
    ASSUMPTION: Serial is formatted as hex string of the hash digest.
    """
    # ASSUMPTION: input is name concatenated with company
    data = (name + company).encode('ascii', errors='replace')
    digest = ripemd160(data)
    # ASSUMPTION: serial is formatted as groups of hex digits
    hex_str = digest.hex().upper()
    # Format as XXXX-XXXX-XXXX-XXXX-XXXX (4 hex chars each, 5 groups from 20 bytes)
    groups = [hex_str[i:i+8] for i in range(0, len(hex_str), 8)]
    return '-'.join(groups)


def verify(name: str, serial: str) -> bool:
    """Verify name+serial combination for Task 3.
    Name constraints from writeup: length > 6 and < 20.
    Serial algorithm based on RIPEMD-160 (from keygen source).
    ASSUMPTION: exact serial format and hash input not fully described.
    """
    if len(name) <= 6 or len(name) >= 20:
        return False
    # ASSUMPTION: company is empty string if not provided
    expected = serial_from_ripemd160(name, '')
    return serial.upper() == expected.upper()


def keygen(name: str, company: str = '') -> str:
    """Generate serial for given name (and optionally company).
    Name must be > 6 and < 20 characters.
    ASSUMPTION: exact algorithm details may differ from actual crackme.
    """
    if len(name) <= 6:
        raise ValueError(f"Name must be longer than 6 characters, got {len(name)}")
    if len(name) >= 20:
        raise ValueError(f"Name must be shorter than 20 characters, got {len(name)}")
    return serial_from_ripemd160(name, company)



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
