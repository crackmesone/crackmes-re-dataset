import random
import string

# Based on the keygen source (Source.txt) from the solution writeup.
# The crackme is a console app that takes a Ref-Id and a Key.
# The Key format is: <char><AB_with_ones>-X
# The Ref-Id is: 0x1f3 * key.length + rand1
# where rand1 is the ASCII value of the first character of the key (0x41..0x56 = 'A'..'V')
# The AB string encodes:
#   - 'A' characters each followed by some '1's, total '1's after all A's = 51
#   - 'B' characters each followed by some '1's, total '1's after all B's = 55
# The key must contain both 'A' and 'B' (and '1's), followed by '-X'

# ASSUMPTION: The verify function checks:
#   1. The key ends with '-X'
#   2. The middle part (between first char and '-X') contains only 'A','B','1'
#      with at least one 'A' and one 'B'
#   3. Total '1's following 'A' blocks sum to exactly 51
#   4. Total '1's following 'B' blocks sum to exactly 55
#   5. ref_id == 0x1f3 * len(key) + ord(key[0])
#   where key[0] is between 0x41 and 0x56 inclusive
# ASSUMPTION: The exact verify logic in the crackme binary may differ slightly;
#   this is reconstructed from the keygen source.

def _parse_key(key):
    """Parse key into (first_char, ab_body, suffix_ok)"""
    if not key.endswith('-X'):
        return None
    if len(key) < 4:  # at least: char + one A/B + '-X'
        return None
    first_char = key[0]
    body = key[1:len(key)-2]  # between first char and '-X'
    return first_char, body

def _count_ones_per_letter(body):
    """For each 'A' or 'B' in body, count following '1's.
    Returns (ones_after_A_total, ones_after_B_total, valid)"""
    ones_A = 0
    ones_B = 0
    i = 0
    has_A = False
    has_B = False
    while i < len(body):
        ch = body[i]
        if ch == 'A':
            has_A = True
            i += 1
            cnt = 0
            while i < len(body) and body[i] == '1':
                cnt += 1
                i += 1
            ones_A += cnt
        elif ch == 'B':
            has_B = True
            i += 1
            cnt = 0
            while i < len(body) and body[i] == '1':
                cnt += 1
                i += 1
            ones_B += cnt
        elif ch == '1':
            # leading ones before any letter - invalid
            return None
        else:
            return None
    if not has_A or not has_B:
        return None
    return ones_A, ones_B, True

def verify(name, serial):
    """serial is a tuple (ref_id_str, key_str) or a string 'ref_id:key'"""
    # ASSUMPTION: name is not used in the algorithm (no name-based check found)
    if isinstance(serial, str) and ':' in serial:
        parts = serial.split(':', 1)
        ref_id_str, key = parts[0], parts[1]
    elif isinstance(serial, (tuple, list)) and len(serial) == 2:
        ref_id_str, key = str(serial[0]), serial[1]
    else:
        return False
    
    try:
        ref_id = int(ref_id_str)
    except ValueError:
        return False
    
    parsed = _parse_key(key)
    if parsed is None:
        return False
    first_char, body = parsed
    
    # first_char must be in range 0x41..0x56
    if not (0x41 <= ord(first_char) <= 0x56):
        return False
    
    result = _count_ones_per_letter(body)
    if result is None:
        return False
    ones_A, ones_B, _ = result
    
    # Total ones after A's must be 51, after B's must be 55
    if ones_A != 51:
        return False
    if ones_B != 55:
        return False
    
    # Check ref_id
    expected_id = 0x1f3 * len(key) + ord(first_char)
    if ref_id != expected_id:
        return False
    
    return True

def keygen(name):
    """Generate a valid (ref_id, key) pair."""
    # ASSUMPTION: name is ignored
    # Choose random first char in 0x41..0x56
    rand1 = random.randint(0x41, 0x56)
    
    # Build AB string with at least one A and one B, length 2..14
    rand0 = random.randint(2, 14)
    while True:
        ab_letters = [random.choice(['A', 'B']) for _ in range(rand0)]
        if 'A' in ab_letters and 'B' in ab_letters:
            break
    
    # Count A's and B's
    count_A = ab_letters.count('A')
    count_B = ab_letters.count('B')
    
    # Distribute 51 ones among A positions, 55 ones among B positions
    def distribute(total, count):
        """Distribute 'total' ones among 'count' slots, each >= 1."""
        if count == 0:
            return []
        # Each slot gets at least 1
        if total < count:
            # ASSUMPTION: fallback - give total to last
            slots = [0] * count
            slots[-1] = total
            return slots
        remaining = total - count  # reserve 1 per slot
        slots = [1] * count
        for i in range(count - 1):
            if remaining <= 0:
                break
            give = random.randint(0, remaining) if i < count - 2 else remaining
            slots[i] += give
            remaining -= give
        slots[-1] += remaining
        return slots
    
    ones_per_A = distribute(51, count_A)
    ones_per_B = distribute(55, count_B)
    
    # Build body
    a_idx = 0
    b_idx = 0
    body = ''
    for ch in ab_letters:
        body += ch
        if ch == 'A':
            body += '1' * ones_per_A[a_idx]
            a_idx += 1
        else:
            body += '1' * ones_per_B[b_idx]
            b_idx += 1
    
    key = chr(rand1) + body + '-X'
    ref_id = 0x1f3 * len(key) + rand1
    return str(ref_id), key


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
