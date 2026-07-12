# Two different algorithms are described in the solutions.
# Solution 1 (NecroTechno) and Solution 2 (estew) describe:
#   sum(ord(c) for c in serial) == (len(serial) * -10) + 13543
# Solution 4 (ne0n_c4lic0) describes a Caesar-cipher based check:
#   password = chr(ord(c) + number) for each c in username
#   where number is between 2 and 9
# Solution 3 (St@rLord) hints at a static password hidden in hex values.
#
# It is likely the binary has TWO modes or the solutions describe different binaries/versions.
# The most mathematically explicit description is from Solutions 1 & 2 (no name input required),
# while Solution 4 describes a name+number->serial scheme.
#
# We implement BOTH interpretations.

# ASSUMPTION: Solutions 1 & 2 describe the real single-input check.
# ASSUMPTION: Solution 4 describes a separate (or same) binary with name+number input.
# ASSUMPTION: The constant 0x34e7 == 13543 is confirmed by both solutions.

CONSTANT = 13543  # 0x34e7

# ---- Interpretation A: single serial input, sum check ----
def verify_sum(serial: str) -> bool:
    """
    sum(ord(c) for c in serial) == (len(serial) * -10) + 13543
    """
    n = len(serial)
    char_sum = sum(ord(c) for c in serial)
    target = CONSTANT + (-10 * n)
    return char_sum == target


def keygen_sum(length: int = None) -> str:
    """
    Generate a valid serial for a given length using the sum-check algorithm.
    Uses 'z' (122) as the primary character and fills the remainder.
    """
    # Find a working length if none provided
    if length is None:
        # Find minimum viable length where max_char * length >= target
        for l in range(1, 10000):
            target = CONSTANT + (-10 * l)
            if target <= 0:
                break
            if 122 * l >= target and 65 * l <= target:  # 65='A', 122='z'
                length = l
                break
    if length is None:
        raise ValueError("Could not find valid length")

    target = CONSTANT + (-10 * length)
    if target <= 0:
        raise ValueError(f"Target sum is non-positive for length {length}")

    # Greedily fill with 'z' (122), then adjust last character
    # ASSUMPTION: character set is printable ASCII a-zA-Z only per solution 2,
    # but solution 1 uses any ASCII including ']' (93), so we allow any printable.
    serial = []
    remaining = target
    for i in range(length):
        slots_left = length - i
        # max we can put here without exceeding remaining for rest
        # pick 'z'=122 if possible, else pick remaining - (slots_left-1)*65
        max_char = min(122, remaining - (slots_left - 1) * 32)  # 32=space min
        min_char_val = max(32, remaining - (slots_left - 1) * 122)
        if min_char_val > 126 or max_char < 32:
            raise ValueError("Cannot generate serial for this length")
        pick = max(32, min(122, max_char))
        pick = max(pick, min_char_val)
        serial.append(chr(pick))
        remaining -= pick
    if remaining != 0:
        raise ValueError("Adjustment needed; try different length")
    result = ''.join(serial)
    assert verify_sum(result), f"Generated serial failed verification: {result!r}"
    return result


# ---- Interpretation B: name + number input, Caesar cipher ----
def verify_caesar(name: str, number: int, serial: str) -> bool:
    """
    serial[i] == chr(ord(name[i]) + number) for each i in range(len(name))
    number must be between 2 and 9 (inclusive).
    """
    if number < 2 or number > 9:
        return False
    if len(serial) != len(name):
        return False
    for i in range(len(name)):
        if serial[i] != chr(ord(name[i]) + number):
            return False
    return True


def keygen_caesar(name: str, number: int = 2) -> str:
    """
    Generate serial by shifting each character in name by number.
    number should be between 2 and 9.
    """
    if number < 2 or number > 9:
        raise ValueError("number must be between 2 and 9")
    return ''.join(chr(ord(c) + number) for c in name)


# ---- Unified interface (defaults to sum-check interpretation) ----
def verify(name: str, serial: str) -> bool:
    """
    Primary verify using sum-check (Solutions 1 & 2).
    'name' is ignored for the sum-check; serial is the full input.
    ASSUMPTION: The sum-check algorithm is the primary/correct one.
    """
    return verify_sum(serial)


def keygen(name: str) -> str:
    """
    Generate a valid serial using the sum-check algorithm.
    'name' is ignored; returns a valid serial string.
    ASSUMPTION: We pick length=225 as a reasonable starting point.
    """
    # Try lengths from min to max to find one that works cleanly
    for l in range(1, 1355):
        target = CONSTANT + (-10 * l)
        if target <= 0:
            break
        # Check if achievable with printable ASCII (32-126)
        if 126 * l >= target >= 32 * l:
            remaining = target
            serial_chars = []
            ok = True
            for i in range(l):
                slots = l - i
                pick = min(122, remaining - (slots - 1) * 32)
                if pick < 32:
                    ok = False
                    break
                serial_chars.append(chr(pick))
                remaining -= pick
            if ok and remaining == 0:
                result = ''.join(serial_chars)
                if verify_sum(result):
                    return result
    raise ValueError("No valid serial found")



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
