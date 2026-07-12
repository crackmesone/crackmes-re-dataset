import string
import itertools

# Based on the writeup by Cyclops for dybolic_v1_keygen
# The serial format is: XXXX-XXXX-XXXX-XXXX (4 groups of 4 chars, separated by '-')
#
# Key insight from generateNameString:
#   num  = (name[0] + name[1]) + 0x7d0
#   num2 = (name[1] + name[2]) + 0xfa0
#   num3 = (name[2] + name[3]) + 0x1770
#   num4 = (name[3] + name[4]) + 0x1f40
# The string szName is built in a loop 0..0x4e1f, inserting "Ruty","eoDl","iDue","Idsk"
# at positions num, num2, num3, num4 respectively (before a random char each iteration).
#
# getSerialHash: splits serial on '-', for each 4-char group:
#   hash_val = (group[0] + group[2]) + (group[3] - group[1])
#   i.e. ord(group[0]) + ord(group[2]) + ord(group[3]) - ord(group[1])
#
# The validation then checks if szName contains the substring that corresponds
# to the serial hash values. Specifically, the check verifies that the
# character at position hash[i] in szName matches certain expected characters.
#
# ASSUMPTION: The check compares szName[hash[i]] to specific characters
# from the inserted substrings "RutyeoDliDueIdsk".
# Looking at valid serials from comments (e.g. "0Aam-0Avz-0Buv-9Axw" for some name),
# and the getSerialHash function:
#   hash_val = ord(s[0]) + ord(s[2]) + ord(s[3]) - ord(s[1])
# For "0Aam": ord('0')+ord('a')+ord('m')-ord('A') = 48+97+109-65 = 189
# For "0Avz": ord('0')+ord('v')+ord('z')-ord('A') = 48+118+122-65 = 223
# etc.
#
# ASSUMPTION: The 4 hash values must equal num, num2, num3, num4 respectively
# (positions where "Ruty","eoDl","iDue","Idsk" are inserted in szName).
# This means the serial encodes the name-derived positions.
#
# So:
#   hash[0] = (ord(name[0]) + ord(name[1])) + 0x7d0  => num
#   hash[1] = (ord(name[1]) + ord(name[2])) + 0xfa0  => num2
#   hash[2] = (ord(name[2]) + ord(name[3])) + 0x1770 => num3
#   hash[3] = (ord(name[3]) + ord(name[4])) + 0x1f40 => num4
#
# NOTE: name must be len > 4 (buggy check: >3, but index [4] requires len>=5)

def compute_targets(name):
    """Compute the 4 target hash values from a name (must be len >= 5)."""
    n = [ord(c) for c in name]
    num  = n[0] + n[1] + 0x7d0
    num2 = n[1] + n[2] + 0xfa0
    num3 = n[2] + n[3] + 0x1770
    num4 = n[3] + n[4] + 0x1f40
    return [num, num2, num3, num4]

def serial_hash(group):
    """Compute hash value for a 4-char serial group."""
    # hash_val = ord(s[0]) + ord(s[2]) + ord(s[3]) - ord(s[1])
    return ord(group[0]) + ord(group[2]) + ord(group[3]) - ord(group[1])

def find_group_for_target(target):
    """
    Find a 4-char group (printable ASCII, no '-') such that
    ord(s[0]) + ord(s[2]) + ord(s[3]) - ord(s[1]) == target
    All characters in range 0x21..0x7c (printable, avoiding '-' which is 0x2d)
    ASSUMPTION: character range based on crackme's random char generation range (0x21..0x7d exclusive)
    """
    # We'll use a simple search: fix s[0], s[1], s[2], solve for s[3]
    # s[3] = target - ord(s[0]) - ord(s[2]) + ord(s[1])
    valid_chars = [c for c in range(0x21, 0x7d) if c != ord('-')]
    for c0 in valid_chars:
        for c1 in valid_chars:
            for c2 in valid_chars:
                c3_val = target - c0 - c2 + c1
                if c3_val in valid_chars:
                    return chr(c0) + chr(c1) + chr(c2) + chr(c3_val)
    return None

def keygen(name):
    """Generate a valid serial for a given name (must be at least 5 chars)."""
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long (crackme bug: >3 check but uses index 4)")
    targets = compute_targets(name)
    groups = []
    for t in targets:
        g = find_group_for_target(t)
        if g is None:
            raise ValueError(f"Cannot find group for target {t}")
        groups.append(g)
    return '-'.join(groups)

def verify(name, serial):
    """Verify a name/serial pair."""
    if len(name) < 5:
        return False
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    for p in parts:
        if len(p) != 4:
            return False
    targets = compute_targets(name)
    hashes = [serial_hash(p) for p in parts]
    return hashes == targets


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
