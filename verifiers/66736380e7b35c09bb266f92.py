#!/usr/bin/env python3
"""
Baby's First Crackme - Key Validation Algorithm

Usage: <prog> <key> <number>
  - key must be exactly 12 characters long
  - number must be 0 <= number <= 50 (0x32)

encode_input() transforms each character of the key:
  - even index, even char: encoded = char - number
  - even index, odd char:  encoded = char + number
  - odd index,  even char: encoded = char + 2 * number
  - odd index,  odd char:  encoded = char - 2 * number

The last non-NUL character of the encoded string must be 0x7c ('|').
A '\n' in the key acts as a terminator (via strcspn), so only characters
before the first '\n' are considered; the encoded string may be truncated
if any encoded character becomes NUL (0x00).
"""

NUM_MIN = 0
NUM_MAX = 0x32  # 50
GRANT_CHAR = 0x7c  # '|'
KEY_LEN = 12


def encode_input(key_bytes, number):
    """Encode the key bytes using the number. Stops at NUL in input.
    Returns encoded bytes, truncated if an encoded byte is NUL."""
    result = []
    for i, c in enumerate(key_bytes):
        if c == 0:
            break
        if (i & 1) == 0:  # even index
            if (c & 1) == 0:  # even char
                encoded = (c - number) & 0xFF
            else:             # odd char
                encoded = (c + number) & 0xFF
        else:               # odd index
            if (c & 1) == 0:  # even char
                encoded = (c + 2 * number) & 0xFF
            else:             # odd char
                encoded = (c - 2 * number) & 0xFF
        if encoded == 0:
            # NUL in encoded string terminates it here
            break
        result.append(encoded)
    return bytes(result)


def verify(name, serial):
    """
    'name' here is the key string (12 chars), 'serial' is the number (int).
    Mimics the program's check_key logic.
    """
    key = name  # key is the first argument
    number = serial

    # Key must be exactly 12 characters
    if len(key) != KEY_LEN:
        return False

    # Number must be in [0, 50]
    if not (NUM_MIN <= number <= NUM_MAX):
        return False

    # strcspn: find length up to first '\n'; use that prefix as the subkey
    newline_pos = key.find('\n')
    if newline_pos == -1:
        subkey = key
    else:
        subkey = key[:newline_pos]

    # Convert subkey to bytes
    subkey_bytes = subkey.encode('latin-1') if isinstance(subkey, str) else subkey

    # Encode the subkey
    encoded = encode_input(subkey_bytes, number)

    # The last character of the encoded string must be 0x7c ('|')
    if len(encoded) == 0:
        return False

    return encoded[-1] == GRANT_CHAR


def keygen(name):
    """
    Given a desired key string of exactly 12 characters, find a valid number.
    Returns (key, number) or None if no valid number exists.
    
    Only the last non-NUL encoded character matters (must be 0x7c).
    The last char is at index 11 (odd index), so:
      - if key[11] is even: encoded = key[11] + 2*number => number = (0x7c - key[11]) / 2
      - if key[11] is odd:  encoded = key[11] - 2*number => number = (key[11] - 0x7c) / 2
    """
    key = name
    if len(key) != KEY_LEN:
        raise ValueError(f"Key must be exactly {KEY_LEN} characters, got {len(key)}")

    key_bytes = key.encode('latin-1') if isinstance(key, str) else key

    # Try all valid numbers
    for number in range(NUM_MIN, NUM_MAX + 1):
        if verify(key, number):
            return number

    return None


def keygen_from_last_char(last_char_ord):
    """
    Compute the number needed so that a key whose last character has
    the given ordinal value will produce 0x7c as the last encoded character.
    Index 11 is odd.
    Returns number or None if out of range or non-integer.
    """
    c = last_char_ord
    if (c & 1) == 0:  # even char, odd index
        # encoded = c + 2*number = 0x7c  =>  number = (0x7c - c) / 2
        diff = GRANT_CHAR - c
    else:             # odd char, odd index
        # encoded = c - 2*number = 0x7c  =>  number = (c - 0x7c) / 2
        diff = c - GRANT_CHAR

    if diff % 2 != 0:
        return None
    number = diff // 2
    if NUM_MIN <= number <= NUM_MAX:
        return number
    return None



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
