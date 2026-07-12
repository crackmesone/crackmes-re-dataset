#!/usr/bin/env python3
"""
Jenya's my_second_crackme - verification and keygen

Rules:
1) Length >= 8 characters
2) Password contains digits, lowercase letters, AND uppercase letters (all three must be present)
3) Sum of digits == 17  (digit '0' counts as 1, '1' as 2, ..., '9' as 10)
4) Sum of uppercase letters == 19  ('A'=1, 'B'=2, ..., 'Z'=26)
5) Sum of lowercase letters == 25  ('a'=1, 'b'=2, ..., 'z'=26)
"""

import itertools


def verify(name: str, serial: str) -> bool:
    """Verify a serial/password against Jenya's rules (name is not used)."""
    # Rule 1: length >= 8
    if len(serial) < 8:
        return False

    digit_sum = 0
    upper_sum = 0
    lower_sum = 0

    has_digit = False
    has_upper = False
    has_lower = False

    for ch in serial:
        if ch.isdigit():
            has_digit = True
            digit_sum += ord(ch) - ord('0') + 1  # '0'->1, '1'->2, ..., '9'->10
        elif ch.isupper() and ch.isalpha():
            has_upper = True
            upper_sum += ord(ch) - ord('A') + 1  # 'A'->1, ..., 'Z'->26
        elif ch.islower() and ch.isalpha():
            has_lower = True
            lower_sum += ord(ch) - ord('a') + 1  # 'a'->1, ..., 'z'->26
        else:
            # Non-alphanumeric character: not explicitly forbidden by description,
            # but z3 keygen only uses alphanumeric. The source says "digits, small letters, capital letters".
            # ASSUMPTION: non-alphanumeric characters are not allowed.
            return False

    # Rule 2: must contain all three types
    if not (has_digit and has_upper and has_lower):
        return False

    # Rule 3: digit sum == 17
    if digit_sum != 17:
        return False

    # Rule 4: uppercase sum == 19
    if upper_sum != 19:
        return False

    # Rule 5: lowercase sum == 25
    if lower_sum != 25:
        return False

    return True


def keygen(name: str = "") -> str:
    """
    Generate a valid serial (name is not used).
    Uses a simple direct construction:
    - Digits summing to 17: use '7' (value 8) + '8' (value 9) = 17 -> two digits
    - Uppercase summing to 19: 'S' (19) -> one uppercase letter
    - Lowercase summing to 25: 'y' (25) -> one lowercase letter
    - Pad to length 8 with more lowercase letters summing correctly.
    
    Easier approach: build a specific known-valid key.
    Example from comments: 095ABCMabcs
    Let's verify and if not, build one programmatically.
    """
    # Direct construction:
    # Digits: '7'(8) + '9'(10) - wait, 8+10=18, need 17
    # Digits: '8'(9) + '8'(9) - sum=18, no
    # Digits: '7'(8) + '8'(9) = 17  YES  (two digits)
    # Uppercase: 'S' = 19            (one uppercase)
    # Lowercase: 'y' = 25            (one lowercase)
    # Total so far: 4 chars, need >= 8
    # Add more alphanumeric with zero contribution to sums... not possible since all add >= 1
    # So add digits/upper/lower that sum to 0 - impossible.
    # Instead: re-distribute.
    # Digits summing to 17 with more chars:
    #   '1'(2)+'1'(2)+'1'(2)+'1'(2)+'9'(10) = 18, no
    #   '1'(2)+'7'(8)+'6'(7) = 17, three digits
    # Uppercase summing to 19 with more chars:
    #   'A'(1)+'R'(18) = 19, two uppercase
    # Lowercase summing to 25 with more chars:
    #   'a'(1)+'x'(24) = 25, two lowercase
    # Total: 3+2+2 = 7, still need 1 more.
    # Add 'A'(1) to upper: 'A'(1)+'A'(1)+'Q'(17)=19 -> 3 uppercase
    # Now: 3+3+2 = 8 chars exactly!
    serial = '1' + '7' + '6' + 'A' + 'A' + 'Q' + 'a' + 'x'
    # Verify it
    assert verify(name, serial), f"Built serial {serial!r} failed verification!"
    return serial


def keygen_bruteforce(name: str = "", length: int = 8):
    """
    Generator that yields valid serials of the given length using itertools.
    WARNING: Very slow for length > 8. Use z3 for practical key generation.
    """
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for combo in itertools.product(chars, repeat=length):
        s = ''.join(combo)
        if verify(name, s):
            yield s



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
            print(_sv)
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
