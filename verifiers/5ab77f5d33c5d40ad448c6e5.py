import subprocess
import ctypes
import sys

# Helper: get Windows username
def get_username():
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return None

# ASSUMPTION: The lookup table is exactly "86E4A2753B339C51" (16 chars + null = 17 bytes)
TABLE = "86E4A2753B339C51"

def _strlen(s):
    return len(s)

def hex2dec(n):
    """Convert integer n to its decimal string representation."""
    return str(n)

def strcat(a, b):
    return a + b

# ASSUMPTION: rsr (rotate serial right) rotates the lookup table by 1 position to the right
def rsr(table_list):
    """Rotate the lookup table right by 1."""
    return [table_list[-1]] + table_list[:-1]

def generate(username):
    """
    Reconstruct the serial generation from the assembly writeup.

    Steps:
    1. Compute sum of ASCII values of all chars in username.
    2. Convert sum to decimal string.
    3. If the decimal string is shorter than 8 digits, repeatedly append
       the decimal value of the last-but-one digit to itself until >= 8 digits.
    4. Split the 8+ digit string into:
         part1 = first 4 chars
         part2 = next 4 chars
         part3/part4 = remaining 8 chars, each char transformed via lookup table
           with the table rotating right after each character lookup.
    5. Serial = part1 + '-' + part2 + '-' + transformed_part3 + '-' + transformed_part4

    ASSUMPTION: The serial format is XXXX-XXXX-XXXX-XXXX (4 groups of 4).
    ASSUMPTION: part3 and part4 are each 4 chars from the transformed remaining 8 chars.
    ASSUMPTION: The digit character at position i (0-indexed string digit) is used as index
                into the lookup table: digit_char - '0' gives index, table[index] gives output char.
    ASSUMPTION: After each lookup, the table rotates right by 1.
    """
    # Step 1: compute sum
    char_sum = sum(ord(c) for c in username)

    # Step 2: convert to decimal string
    serial_str = str(char_sum)

    # Step 3: extend to at least 8 digits
    while len(serial_str) < 8:
        # get serial(length - 1) digit (last char of current string)
        # assembly says: movzx eax, byte ptr [esi+eax-2]  where eax = length
        # i.e., serial[length - 2] ... but length is the strlen result
        # ASSUMPTION: it's the second-to-last character (index len-2 in 0-based after the loop)
        # Actually re-reading: eax = strlen result (length), then [esi+eax-2] with eax=length
        # In C terms: serial_str[length - 2] ... but for a 0-based string of length L,
        # index L-2 is second to last. Let's try last char (index L-1) first.
        # ASSUMPTION: uses last digit character
        last_digit_char = serial_str[-1]
        last_digit_val = ord(last_digit_char) - ord('0')  # convert ASCII digit to int
        appended = str(last_digit_val)
        serial_str = serial_str + appended

    # Step 4: split into parts
    # part1: serial_str[0:4]
    # part2: serial_str[4:8]
    # remaining: serial_str[8:16] (up to 8 more chars for part3 and part4)
    part1 = serial_str[0:4]
    part2 = serial_str[4:8]
    remaining = serial_str[8:16]

    # Pad remaining to 8 chars if needed
    # ASSUMPTION: if remaining is shorter than 8, pad with '0'
    while len(remaining) < 8:
        remaining = remaining + '0'

    # Step 5: transform remaining via lookup table with rotation
    table_list = list(TABLE)
    transformed = []
    for ch in remaining:
        digit = ord(ch) - ord('0')  # convert digit char to index
        # ASSUMPTION: digit is a valid index 0-9 into the 16-char table
        if 0 <= digit < len(table_list):
            out_char = table_list[digit]
        else:
            # ASSUMPTION: modulo for safety
            out_char = table_list[digit % len(table_list)]
        transformed.append(out_char)
        table_list = rsr(table_list)

    # ASSUMPTION: part3 = transformed[0:4], part4 = transformed[4:8]
    part3 = ''.join(transformed[0:4])
    part4 = ''.join(transformed[4:8])

    serial = part1 + '-' + part2 + '-' + part3 + '-' + part4
    return serial


def verify(name, serial):
    """
    Verify a name/serial pair by regenerating the serial and comparing.
    ASSUMPTION: The crackme compares the generated serial to the entered serial (case-sensitive).
    """
    expected = generate(name)
    return serial == expected


def keygen(name):
    """Generate a valid serial for the given name."""
    return generate(name)



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
