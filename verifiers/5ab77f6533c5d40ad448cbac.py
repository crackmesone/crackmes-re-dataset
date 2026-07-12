def calcul_serial(name: str) -> str:
    """
    Reconstructed from the decompiled VB.NET source in the writeup.
    Steps:
    1. Uppercase the name.
    2. For each character at position i (1-based), compute:
           text2 = Asc(char)          # ASCII value of the character
           text2 = text2 + (i - 48)   # add (i - 48), where i is 1-based
       Concatenate all text2 values (as decimal digit strings) into text3.
    3. Walk text3 two digits at a time (positions 1,3,5,... in 1-based indexing):
           num2 = int(text3[num1-1])   # digit at num1
           num3 = int(text3[num1])     # digit at num1+1
           sum  = num2 + num3
       If num1 == 3 (i.e., the third pair), insert " - OEM - " before the sum.
       Otherwise just append the sum as a string.
    4. Return the resulting Serial string.
    """
    text1 = name.upper()
    if not text1:
        return ""

    # Step 2: build text3
    text3 = ""
    for i, ch in enumerate(text1, start=1):  # i is 1-based
        text2 = ord(ch)          # Asc(char)
        text2 = text2 + (i - 48) # add (i - 48)
        text3 += str(text2)

    # Step 3: build serial from text3
    serial = ""
    num7 = len(text3)  # Strings.Len(text3)
    num1 = 1           # 1-based index
    while num1 <= num7:
        # Need at least two characters for a pair
        # ASSUMPTION: if there's an odd leftover character, the loop condition
        #             'num1 <= num7' may include it but num1+1 might be out of range;
        #             we guard against that.
        if num1 > len(text3):
            break
        num2_str = text3[num1 - 1]      # Strings.Mid(text3, num1, 1)
        if num1 < len(text3):
            num3_str = text3[num1]      # Strings.Mid(text3, num1+1, 1)
        else:
            # ASSUMPTION: odd-length text3, treat missing digit as 0
            num3_str = "0"
        try:
            num2 = int(num2_str)
            num3 = int(num3_str)
        except ValueError:
            # ASSUMPTION: non-digit chars are treated as 0
            num2 = 0
            num3 = 0
        pair_sum = num2 + num3
        if num1 == 3:
            serial += " - OEM - " + str(pair_sum)
        else:
            serial += str(pair_sum)
        num1 += 2

    return serial


def verify(name: str, serial: str) -> bool:
    """
    The program calls Calcul_Serial and then Verification_Serial which
    compares TextBox2.Text (entered serial) to Me.Serial (computed serial).
    ASSUMPTION: comparison is case-insensitive string equality based on
    standard VB.NET String comparison.
    """
    if len(name) < 4:
        return False
    expected = calcul_serial(name)
    return serial.strip() == expected.strip()


def keygen(name: str) -> str:
    """Return the valid serial for the given name."""
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long.")
    return calcul_serial(name)



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
