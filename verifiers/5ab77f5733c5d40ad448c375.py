import random
import string
from itertools import product

def _next_lesser(i_value, i, j):
    """i and j are integer char codes"""
    # Use 32-bit unsigned arithmetic
    i_value = (i_value + (i * 2) - j) & 0xFFFFFFFF
    i_value = (i_value << 0x28) & 0xFFFFFFFF
    i_value = (i_value + (i * 2) - j) & 0xFFFFFFFF
    return i_value

def _next_greater(i_value, i, j):
    """i and j are integer char codes"""
    i_value = (i_value + (i * 2) + j) & 0xFFFFFFFF
    i_value = (i_value << 0x48) & 0xFFFFFFFF
    i_value = (i_value + (i * 2) + j) & 0xFFFFFFFF
    return i_value

# Precompute valid first-4-char combinations
_S_COMPARE = 0x5235471F

# Characters used: '0'-'9' and 'A'-'Z'
_CHARS = [chr(c) for c in range(ord('0'), ord('9')+1)] + [chr(c) for c in range(ord('A'), ord('Z')+1)]

_LOOKUP_NUMBER = ['4', '9', 'D', 'G', 'K', 'N', '8', '1', 'S', 'W']
_LOOKUP_STRING = ['Z', '2', '7', 'B', 'F', 'J', 'M', '6', '3', 'R', 'V', 'Y', '5',
                  'T', 'C', 'I', 'L', 'O', 'P', 'U', 'X', 'Q', 'H', 'E', 'A', '0']

def _find_valid_prefixes():
    """Brute-force all 4-char prefixes that satisfy the checksum."""
    valid = []
    for c0, c1, c2, c3 in product(_CHARS, repeat=4):
        i0, i1, i2, i3 = ord(c0), ord(c1), ord(c2), ord(c3)
        i_value = 0
        if i0 > i1:
            i_value = _next_lesser(i_value, i0, i1)
        else:
            i_value = _next_greater(i_value, i0, i1)
        if i1 > i2:
            i_value = _next_lesser(i_value, i1, i2)
        else:
            i_value = _next_greater(i_value, i1, i2)
        if i2 > i3:
            i_value = _next_lesser(i_value, i2, i3)
        else:
            i_value = _next_greater(i_value, i2, i3)
        i_value = (i_value + (i3 * 2) + i0) & 0xFFFFFFFF
        if i_value == _S_COMPARE:
            valid.append(c0 + c1 + c2 + c3)
    return valid

# Cache valid prefixes at module load
try:
    _VALID_PREFIXES = _find_valid_prefixes()
except Exception:
    _VALID_PREFIXES = []

def _encode_char(ch):
    """Encode a single character (already upper-case) using lookup tables."""
    if '0' <= ch <= '9':
        return _LOOKUP_NUMBER[ord(ch) - ord('0')]
    else:
        idx = ord(ch) - ord('A')
        if 0 <= idx < len(_LOOKUP_STRING):
            return _LOOKUP_STRING[idx]
        # ASSUMPTION: characters outside 0-9, A-Z are not handled; return ch unchanged
        return ch

def _build_middle(username, computer_name):
    """Build the 8-char middle segment from username and computer_name (already upper)."""
    u = username
    c = computer_name
    # Indices are 0-based; the C++ code uses .size() which is length
    # sValue[0] = sUserName[size/2 - 2]
    # sValue[1] = sComputerName[size/2 - 2]
    # sValue[2] = sUserName[size/2]
    # sValue[3] = sComputerName[size/2]
    # sValue[4] = sUserName[size - 1]
    # sValue[5] = sComputerName[size - 1]
    # sValue[6] = sUserName[0]
    # sValue[7] = sComputerName[0]
    ul = len(u)
    cl = len(c)
    s_value = [
        u[ul // 2 - 2],
        c[cl // 2 - 2],
        u[ul // 2],
        c[cl // 2],
        u[ul - 1],
        c[cl - 1],
        u[0],
        c[0],
    ]
    return ''.join(s_value)

def _random_suffix(length=7):
    """Generate a random alphanumeric suffix of given length."""
    result = ''
    for _ in range(length):
        r = random.randint(0, 35)
        if r <= 9:
            result += chr(ord('0') + r)
        else:
            result += chr(ord('A') + r - 10)
    return result

def verify(name, serial):
    """
    Verify the serial for (computer_name, username).
    Per the writeup, the crackme takes BOTH a computer name and a username.
    Here 'name' is interpreted as 'username' and we cannot verify the computer_name part
    without it.  We verify the structural constraints we can.
    NOTE: Full verification requires both username and computer_name.
    ASSUMPTION: 'name' is the username only; computer_name is not available in verify().
    We verify the prefix checksum and the length/character-set constraints.
    """
    if len(serial) != 20:
        return False
    # Check character set for positions 7-20 (0-indexed: 6 onwards, after the '-')
    # Serial format: 4 chars + '-' + 8 encoded chars + 7 random chars = 20 chars
    prefix = serial[:4]
    if serial[4] != '-':
        return False
    rest = serial[5:]  # 15 chars: 8 encoded + 7 random
    for ch in rest:
        if not (ch.isdigit() or ('A' <= ch <= 'Z')):
            return False
    # Verify the prefix checksum
    c0, c1, c2, c3 = ord(prefix[0]), ord(prefix[1]), ord(prefix[2]), ord(prefix[3])
    # All must be in _CHARS
    for ch in prefix:
        if ch not in _CHARS:
            return False
    i_value = 0
    if c0 > c1:
        i_value = _next_lesser(i_value, c0, c1)
    else:
        i_value = _next_greater(i_value, c0, c1)
    if c1 > c2:
        i_value = _next_lesser(i_value, c1, c2)
    else:
        i_value = _next_greater(i_value, c1, c2)
    if c2 > c3:
        i_value = _next_lesser(i_value, c2, c3)
    else:
        i_value = _next_greater(i_value, c2, c3)
    i_value = (i_value + (c3 * 2) + c0) & 0xFFFFFFFF
    return i_value == _S_COMPARE

def keygen(username, computer_name=None):
    """
    Generate a valid serial for (username, computer_name).
    username: must be exactly 5 characters (per constraint at 0047F510).
    computer_name: required for the middle part; defaults to 'MYPC' if not provided.
    ASSUMPTION: username length == 5 and computer_name length >= 4 based on index access.
    """
    if computer_name is None:
        # ASSUMPTION: use a default computer name of length 5 to satisfy index access
        computer_name = 'MYPC5'
    username_up = username.upper()
    computer_name_up = computer_name.upper()
    # Validate lengths to avoid index errors
    # username must be 5 chars (per check at 0047F510)
    if len(username_up) < 3:
        raise ValueError('Username too short (need at least 3 chars; 5 required by crackme)')
    if len(computer_name_up) < 3:
        raise ValueError('Computer name too short (need at least 3 chars)')
    if not _VALID_PREFIXES:
        raise RuntimeError('No valid prefixes found; try re-running _find_valid_prefixes()')
    prefix = random.choice(_VALID_PREFIXES)
    middle_raw = _build_middle(username_up, computer_name_up)
    middle_encoded = ''.join(_encode_char(ch) for ch in middle_raw)
    suffix = _random_suffix(7)
    return prefix + '-' + middle_encoded + suffix


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
