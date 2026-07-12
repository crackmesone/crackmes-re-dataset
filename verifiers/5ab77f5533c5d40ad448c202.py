# Reverse-engineered from EsKiMo's writeup of sam's keygenme by samfisher9000
# Algorithm is only partially described; several steps are ambiguous.
# Mark gaps with # ASSUMPTION: comments.

def compute_adjusted_ascii(c):
    """
    For each character, compute: base = Asc(c) - 11
    Then apply range-based adjustments.
    The writeup mentions checks against 90 and 150, but the exact
    adjustments (add/subtract amounts) are NOT fully described.
    """
    v = ord(c) - 11
    # ASSUMPTION: The checks at 00402261 and 0040230A gate two branches.
    # The writeup only says 'some checks to select how much to increase/decrease'.
    # We guess: if v < 90 add something, if v >= 90 and < 150 do something else.
    # Without the actual deltas we cannot replicate this precisely.
    # We pass v through unchanged as a placeholder.
    return v


def compute_number1(username):
    """
    Iterate over each character of the username.
    First char: Number1 = adjusted_ascii(char[0])
    Subsequent chars:
        Temp   = adjusted_ascii(char[i])
        Mul    = Int(Temp / 50)
        Number1 = Number1 * Mul
    After loop:
        if Number1 < 2000:
            Number1 = Number1 * (Number1 / 10)
    """
    number1 = None
    for i, c in enumerate(username):
        val = compute_adjusted_ascii(c)
        if i == 0:
            number1 = val
        else:
            # ASSUMPTION: Mul = Int(val / 50) as shown at 0040247B-0040249D
            mul = int(val / 50)
            number1 = number1 * mul

    if number1 is not None and number1 < 2000:
        # Number1 = Number1 * (Number1 / 10)  -- shown at 004024F1-00402510
        number1 = number1 * (number1 / 10)

    return int(number1) if number1 is not None else 0


def compute_number2(username, number1):
    """
    Take the last char of username.
    A value is added to its ascii code depending on the char (exact table unknown).
    Number2 = Int(5 * number1 * Temp / 15)
    where Temp = Int((Asc(last_char) + value) * 5)
    """
    last_char = username[-1]
    base_asc = ord(last_char)

    # ASSUMPTION: The 'value added depending on the char' is not specified in the writeup.
    # We assume 0 as a placeholder.
    added_value = 0  # ASSUMPTION: unknown lookup/formula

    temp = int((base_asc + added_value) * 5)

    # Number2 = Int(5 * Number1 * Temp / 15)  -- from writeup summary line
    # But the assembly shows: multiply by Number1, then divide by 15
    # and an earlier multiply by 5 is already in temp.
    # ASSUMPTION: formula is Number2 = Int(number1 * temp / 15)
    number2 = int(number1 * temp / 15)
    return number2


def make_part(n):
    """
    Convert a number to its Part string.
    The writeup says 'Part1 and Part2 are generated from Number1 and Number2'
    but does NOT describe the conversion.
    # ASSUMPTION: We just use str(int(n)) as the part value.
    """
    return str(int(n))  # ASSUMPTION: exact formatting unknown


def keygen(name):
    """
    Serial format: <Part1>-11-<Part2>-11
    """
    if len(name) < 5 or len(name) > 15:
        raise ValueError("Username must be between 5 and 15 characters")

    number1 = compute_number1(name)
    number2 = compute_number2(name, number1)

    part1 = make_part(number1)
    part2 = make_part(number2)

    return f"{part1}-11-{part2}-11"


def verify(name, serial):
    """
    Check that the serial matches the keygen output.
    Since the algorithm is only partially recovered, this may not match the real crackme.
    """
    if len(name) < 5 or len(name) > 15:
        return False
    try:
        expected = keygen(name)
        return serial == expected
    except Exception:
        return False



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
