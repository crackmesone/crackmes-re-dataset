# Reverse-engineered keygen for Taliesin's KGM1Tal
# Based on solution writeups (especially solution.py by anany and Note.pdf)
#
# The algorithm:
# 1. Name must consist of uppercase letters only (UPPER check)
# 2. Serial must be exactly 10 characters long
# 3. A lookup table string is used: "ZWATRQLCGHPSXYENVBJDFKMU" (24 chars)
# 4. Sum of name ASCII values, mod 0x18 -> index into lookup table
# 5. Serial is built from indices into that lookup table
# 6. The 10th character is derived from the sum of the first 9 serial chars divided by 9
#
# ASSUMPTION: The exact boundary check is 'if total >= 0x18: total -= 0x18'
#   (the assembly uses idiv ecx with ecx=0x18, keeping remainder; Python % 0x18 is equivalent)
# ASSUMPTION: 'second - 0x41' is the 0-based alphabet index of the letter (since 'A'=0x41)
# ASSUMPTION: The 'E' inserted as second character of password is a literal uppercase E
#   as observed in the sample output and described in the writeup.
# ASSUMPTION: The overflow/wrap for total uses simple subtraction by 0x18 (as in solution.py)
#   rather than strict modulo, but for values in range they are equivalent.
# ASSUMPTION: The last character check uses integer division (floor), matching get_last_character.

VALUES = "ZWATRQLCGHPSXYENVBJDFKMU"  # 24 chars


def _wrap(total):
    """Wrap total to be within [0, 0x17] by subtracting 0x18 if needed."""
    # ASSUMPTION: Only one subtraction needed (values won't exceed 2*0x18)
    if total >= 0x18:
        total -= 0x18
    return total


def keygen(name):
    """Generate a valid serial for the given name."""
    # Name should be uppercase letters only
    name = name.upper()

    # Step 1: sum of ASCII values of name, mod 0x18
    name_sum = sum(ord(c) for c in name) & 0xFF  # ASSUMPTION: sum is taken mod 256 first
    # ASSUMPTION: The assembly does idiv 0x18 and keeps remainder (dl), so:
    total = name_sum % 0x18
    temp = total

    # Step 2: First character of password
    first_char = VALUES[total]
    password = first_char + 'E'  # ASSUMPTION: literal 'E' is always inserted here

    # Step 3: Second meaningful character (position 2 in password)
    total = _wrap(total + temp)
    second_char = VALUES[total]
    password += second_char
    second = ord(second_char)

    # Step 4: Characters 4-9 (6 more characters)
    for i in range(6):
        temp2 = second - 0x41  # alphabet index of current char
        total = _wrap(total + temp2)
        current_char = VALUES[total]
        second = ord(current_char)
        password += current_char

    # password is now 9 characters; compute 10th
    # 10th char = sum of first 9 chars // 9
    char_sum = sum(ord(c) for c in password)
    last_char = char_sum // 9
    password += chr(last_char)

    return password


def verify(name, serial):
    """Verify that serial is valid for name."""
    # Check 1: name must be uppercase only
    if not name or not name.isupper():
        return False

    # Check 2: serial must be exactly 10 characters
    if len(serial) != 10:
        return False

    # Generate expected serial and compare
    expected = keygen(name)
    return serial == expected



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
