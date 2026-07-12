# Reverse-engineered algorithm from eastern_dragon's Keygen Me #2
# Based on the writeup/tutorial HTML

# Key format: X-YYYYYYYY
#   X is a single digit 0-7
#   YYYYYYYY is exactly 8 hex characters (from '0123456789ABCDEF')
# Total key length must be 10 (X + '-' + 8 hex chars)

HEX_CHARS = '0123456789ABCDEF'


def sort_key_part(s):
    """Sort the 8 characters after the dash.
    The writeup says the first call sorts the 8 chars after the dash.
    # ASSUMPTION: This is a simple ascending sort (radix/comparison sort over hex chars).
    """
    return sorted(s)


def key_transform(key):
    """
    Transform the key part (8 hex chars after dash) using the algorithm described.
    Returns an 8-element list (Ans[8]).

    Steps (from writeup assembly):
      X = Key[0] - '0'  (the digit before the dash)
      Sort[8] = sorted(Key[2:10])
      For i in 0..7:
        C = Sort[X]  # always uses Sort[X], not Sort[i] -- the pivot character
        Ans[i] = C
        Count duplicates of C in Sort[0..X-1]  => Num
        Then scan Key[2..9] (original 8 chars):
          for X2 in 0..7:
            if Key[2+X2] == C:
              if Num == 0: record position X2 in Ans[i]; break
              else: Num -= 1
        i++

    # ASSUMPTION: The loop index 'i' increments each iteration and 'X' stays fixed
    # at Key[0]-'0' throughout (the assembly shows EAX loaded once before the loop
    # with 'X = Key[0] - 0x30' and the inner loop uses EAX as X, not i).
    # However this would produce Ans[i] = same C every iteration which seems wrong.
    # More likely interpretation: X increments each iteration (i==X or X=i).
    # The writeup says "position of C is reached" suggesting i steps through Sort.
    # ASSUMPTION: X = i each iteration (Sort[i] is used as C for iteration i).
    """
    X_init = ord(key[0]) - ord('0')
    original_8 = list(key[2:10])
    sort_8 = sort_key_part(original_8)  # Sort[0..7]

    ans = []
    # ASSUMPTION: The outer loop variable i also drives Sort index
    # Based on assembly: EAX starts as X = Key[0]-'0', used as Sort index
    # But then the loop goes i=0..7 using EDX for i and EAX stays as X.
    # So C = Sort[X] for all iterations -- all Ans entries get same C.
    # This seems odd but we follow the literal assembly.
    # More practically, the result is a permutation: Ans[i] = position in
    # original key of the i-th occurrence determined by sorted order.
    # We implement the literal assembly description:

    X = X_init  # fixed pivot index into Sort
    for i in range(8):
        C = sort_8[X]  # Sort[X] -- ASSUMPTION: X is fixed (from Key[0]-'0')
        # Count occurrences of C in Sort[0..X-1]
        Num = 0
        for j in range(X):
            if sort_8[j] == C:
                Num += 1
        # Scan Key[2..9] to find the (Num+1)-th occurrence of C
        found_pos = -1
        for x2 in range(8):
            if original_8[x2] == C:
                if Num == 0:
                    found_pos = x2
                    break
                else:
                    Num -= 1
        ans.append(found_pos if found_pos != -1 else 0)
        # ASSUMPTION: After each iteration X or some state changes; without full
        # decompilation we cannot be certain. Try incrementing X mod 8.
        X = (X + 1) % 8
    return ans


def name_transform(name):
    """
    Transform the name.
    The writeup says there's a second call that takes the name, then
    REPE CMPS compares transformed name vs transformed key.
    # ASSUMPTION: We do not have the name transform algorithm from the truncated writeup.
    # This function is a placeholder.
    """
    # ASSUMPTION: Name transform algorithm not fully described in writeup (truncated).
    # Cannot implement without more info.
    raise NotImplementedError('Name transform algorithm not recovered from writeup')


def validate_key_format(key):
    """Check key format constraints from the assembly."""
    if len(key) != 10:
        return False
    if key[1] != '-':
        return False
    if not ('0' <= key[0] <= '7'):
        return False
    for c in key[2:]:
        if c not in HEX_CHARS:
            return False
    return True


def verify(name, serial):
    """
    Verify name/serial pair.
    # ASSUMPTION: Full verification requires comparing key_transform(serial)
    # with name_transform(name). Since name_transform is not recovered,
    # we can only verify key format and structure.
    """
    if not validate_key_format(serial):
        return False
    try:
        k_ans = key_transform(serial)
        n_ans = name_transform(name)
        return k_ans == n_ans
    except NotImplementedError:
        # ASSUMPTION: Cannot fully verify without name transform
        # Returning False as placeholder
        return False


def keygen(name):
    """
    Generate a valid serial for a given name.
    # ASSUMPTION: Without name_transform, we cannot generate a valid key.
    # This is a placeholder.
    """
    # ASSUMPTION: Full keygen requires name_transform to be known.
    raise NotImplementedError(
        'Cannot generate key: name transform algorithm not recovered from truncated writeup'
    )



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
