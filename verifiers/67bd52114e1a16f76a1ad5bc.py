from random import randint, choice
import string

# Two different solutions describe two DIFFERENT crackmes (or two different interpretations).
# Solution 1 (ratatu2john) describes a lowercase-letters-and-dashes password.
# Solution 2 (stackpointer7) describes a digits-only password.
# We implement BOTH as verify_v1/keygen_v1 and verify_v2/keygen_v2,
# and expose verify/keygen based on Solution 1 (more detailed algorithm description).

# --- Solution 1 tables ---
arr1_raw = [0x10, 0x2F, 0x1A, 0x1E, 0x27, 0x1E, 0x1B, 0x23, 0x0A, 0x24,
            0x20, 0x0B, 0x1E, 0x0C, 0x11, 0x21, 0x0E, 0x2A, 0x0A, 0x18,
            0x19, 0x29, 0x2C, 0x20, 0x0D, 0x2E]
arr2_raw = [0x40, 0x06, 0xAA, 0x51, 0xC1, 0xDD, 0xB8, 0x1D, 0xF7, 0x08,
            0xD2, 0x5F, 0xBB, 0x20, 0xF7, 0x9F, 0xCB, 0x1B, 0x54, 0x2B,
            0xFF, 0x27, 0x12, 0xD2, 0x51, 0x60]

def to_signed8(x):
    return x if x < 128 else x - 256

arr1 = [to_signed8(x) for x in arr1_raw]
arr2 = [to_signed8(x) for x in arr2_raw]

def get_letter_position(c):
    """Returns 0-25 for a-z."""
    return ord(c) - ord('a')

def verify_v1(password):
    """
    Solution 1 algorithm (lowercase letters + dashes).
    Checks:
      1. 5 < len(password) <= 0xfe
      2. Only lowercase letters and '-'
      3. password[0] != '-' and password[-1] != '-'
      4. Exactly 2 '-' in password
      5. password[0] == password[-1]
      6. xor_res (arr1[pos0] XOR arr2[pos_last]) == computed sum
    """
    pw = password
    # Check 1
    if not (5 < len(pw) <= 0xfe):
        return False
    # Check 2
    allowed = set(string.ascii_lowercase + '-')
    if not all(c in allowed for c in pw):
        return False
    # Check 3
    if pw[0] == '-' or pw[-1] == '-':
        return False
    # Check 4
    if pw.count('-') != 2:
        return False
    # Check 5 (from func3: password[0] == password[length-1])
    if pw[0] != pw[-1]:
        return False
    # Check 6
    pos0 = get_letter_position(pw[0])
    pos_last = get_letter_position(pw[-1])
    xor_res = arr1[pos0] ^ arr2[pos_last]

    ind = 1
    total = 0
    while ind < len(pw) - 1:
        c = pw[ind]
        if c == '-':
            # '-' is not a letter; func3 skips or handles it.
            # ASSUMPTION: '-' has no letter position; we skip it in the sum loop.
            # The keygen never places '-' at odd/even positions in a way that
            # would be processed here -- the keygen builds pairs of letters.
            # The readme says pos = get_letter_position(password[ind]),
            # implying only letters appear in mid positions... but '-' appears too.
            # ASSUMPTION: '-' is skipped in the sum (treated as separator).
            ind += 1
            continue
        pos = get_letter_position(c)
        if pos > 13:
            # letter is n-z
            if ind % 2 == 0:
                total += pos
            else:
                total -= arr2[pos]
        else:
            # letter is a-m
            if ind % 2 == 0:
                total += arr1[pos]
            else:
                total -= pos
        ind += 1

    return xor_res == total

def keygen_v1(name=None):
    """
    Keygen based on Solution 1.
    name is ignored (this crackme appears to be serial-only).
    Returns a valid password string.
    """
    # Pre-build sub-arrays as in the original keygen
    sub_arr_even = []
    sub_arr_odd = []
    for i in range(14):
        for j in range(14, 26):
            sub_arr_odd.append([j - i, chr(ord('a') + i), chr(ord('a') + j)])
            if arr1[i] - arr2[j] < 0:
                sub_arr_even.append([arr1[i] - arr2[j], chr(ord('a') + i), chr(ord('a') + j)])

    sub_arr_odd.sort()
    sub_arr_even.sort()

    for _ in range(10000):  # retry loop
        first_char = randint(ord('a'), ord('z'))
        xor_res = arr1[first_char - ord('a')] ^ arr2[first_char - ord('a')]

        base = ""
        ind = 1

        if xor_res < 0:
            base += '-'
            ind += 1

        remaining = xor_res
        success = True
        steps = 0
        while remaining != 0:
            steps += 1
            if steps > 200:
                success = False
                break
            if remaining > 0:
                if ind % 2 == 1:
                    # find largest odd entry <= remaining
                    max_ind = len(sub_arr_odd) - 1
                    while max_ind >= 0 and remaining < sub_arr_odd[max_ind][0]:
                        max_ind -= 1
                    if max_ind < 0:
                        success = False
                        break
                    rand_ind = randint(0, max_ind)
                    base += sub_arr_odd[rand_ind][1] + sub_arr_odd[rand_ind][2]
                    remaining -= sub_arr_odd[rand_ind][0]
                    ind += 2
                else:
                    base += '-'
                    ind += 1
            else:
                if len(sub_arr_even) == 0:
                    success = False
                    break
                rand_ind = randint(0, len(sub_arr_even) - 1)
                base += sub_arr_even[rand_ind][1] + sub_arr_even[rand_ind][2]
                remaining -= sub_arr_even[rand_ind][0]
                ind += 2

        if not success:
            continue

        # Ensure exactly 2 dashes
        dash_count = base.count('-')
        if dash_count > 2:
            continue
        base += '-' * (2 - dash_count)

        candidate = chr(first_char) + base + chr(first_char)
        if verify_v1(candidate):
            return candidate

    return None

# --- Solution 2 (digits-only) ---

def verify_v2(password):
    """
    Solution 2 algorithm (digits '0'-'9' only... actually '0'-':' based on rand()%(';'-'1')+'0').
    ASSUMPTION: valid chars are '0'-':' (ASCII 48-58).
    """
    pw = password
    if not (4 < len(pw) <= 0xfe):
        return False
    # Only digits (and possibly ':')
    allowed = set('0123456789:')
    if not all(c in allowed for c in pw):
        return False

    num0 = ord(pw[0]) - 0x30
    num1 = ord(pw[-1]) - 0x30
    xor_res = num0 ^ num1

    if xor_res < num0:
        return False
    if xor_res < num1:
        return False
    # xor_res must not be -1 (here represented as sentinel; since digits, this won't be -1)
    # ASSUMPTION: check_id_xor returns -1 on failure, check_id_sum checks != -1

    op_res = 0
    for i in range(1, len(pw) - 1):
        if i & 1:
            op_res += ord(pw[i]) - 0x30
        else:
            op_res -= ord(pw[i]) - 0x30

    return op_res == xor_res

def keygen_v2(name=None):
    """
    Keygen for Solution 2 (digits-only).
    """
    chars = '0123456789'
    for _ in range(100000):
        length = randint(5, 20)
        pw = ''.join(choice(chars) for _ in range(length))
        if verify_v2(pw):
            return pw
    return None

# Default verify/keygen uses Solution 1 (more algorithmically detailed)
def verify(name, serial):
    """
    This crackme appears to be serial-only (name not used).
    Uses Solution 1 algorithm (lowercase + dashes).
    """
    return verify_v1(serial)

def keygen(name):
    """
    Generate a valid serial. name is ignored.
    """
    return keygen_v1(name)


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
