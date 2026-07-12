import math

def encrypt(name: str) -> int:
    """
    Reimplements the VB.NET Encrypt() function.

    For each character in `name` (after trimming):
      1. Convert the current feedback integer (num2) to a string.
      2. Take the first character of that string (the leading digit/char).
      3. Get the ASCII ordinal of that first character.
      4. Convert that ordinal to its octal representation (as a string, no prefix).
      5. Get the ASCII ordinal of the current name character.
      6. Convert that ordinal to its octal representation (as a string, no prefix).
      7. Concatenate step-4 result with step-6 result.
      8. Parse the concatenated string as a float, add 666.0, round to nearest int.
      9. That becomes the new num2.

    Return num2 after processing all characters.

    Note: VB's Asc() on a string returns the ordinal of the *first* character.
    Note: VB's Oct() returns the octal string without '0o' prefix, e.g. Oct(65) == '101'.
    Note: num2 starts as 0 (uninitialized int in VB, defaults to 0).
    """
    num2 = 0
    for ch in name:
        # Step 1-4: octal of ASCII of first char of str(num2)
        str_num2 = str(num2)          # convert feedback to string
        first_char = str_num2[0]      # first character of that string
        asc_first = ord(first_char)   # ASCII ordinal of that first character
        oct_first = oct(asc_first)[2:]  # octal string without '0o' prefix

        # Step 5-6: octal of ASCII of current character
        asc_ch = ord(ch)              # ASCII ordinal of current name character
        oct_ch = oct(asc_ch)[2:]      # octal string without '0o' prefix

        # Step 7: concatenate
        combined = oct_first + oct_ch

        # Step 8: parse as float, add 666, round
        num2 = int(math.floor(float(combined) + 666.0 + 0.5))  # banker's round matches Math.Round
        # ASSUMPTION: Python's round() uses banker's rounding like .NET's Math.Round;
        # using explicit +0.5 and floor to mimic standard rounding (round half up).
        # In practice the difference rarely matters here.
        num2 = round(float(combined) + 666.0)  # use Python's built-in round (banker's rounding, matches .NET)

    return num2


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    The serial must equal str(Encrypt(Trim(name))).
    """
    trimmed_name = name.strip()
    expected_serial = str(encrypt(trimmed_name))
    return serial.strip() == expected_serial


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    trimmed_name = name.strip()
    return str(encrypt(trimmed_name))



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
