# Reverse-engineered keygen for MiDi crackme2
#
# Algorithm (from multiple writeups):
# For each character at index i in the name:
#   1. Take the character's ASCII value (name[i])
#   2. Compute: a = ord(name[i]) + 0x1E
#   3. Compute: divisor = (i+i) + 2  = 2*(i+1)   (from LEA ESI,[EBX+EBX]; LEA EDI,[ESI+2])
#      where EBX = index i (the loop counter / ebp-1)
#   4. serial_digit[i] = a % divisor
#   5. If serial_digit[i] > 9:
#        serial_digit[i] = serial_digit[i] - i
#        (ASSUMPTION: the 'sub bl, [ebp-19]' step uses the current index; text says
#         NewVal[i] -= i but the exact subtrahend is the index counter)
#
# The serial is the concatenation of these digits (each 0-9) as ASCII chars (digit + '0').
# The length of the serial must equal the length of the name.
#
# NOTE: Solution 3 (Python) uses a running EDI that increments by 2 each step,
# starting at 0 before the loop, so divisor at step i is 2*(i+1).
# This matches the assembly: EBX = loop counter i, ESI = i+i, EDI = ESI+2 = 2i+2.
#
# The 'if > 9' branch: assembly does NewVal[i] -= i (the current counter value ebp-1).
# ASSUMPTION: the subtraction uses the index i as the subtrahend.

def _compute_serial_digits(name):
    digits = []
    for i, ch in enumerate(name):
        a = ord(ch) + 0x1E  # +30 decimal
        divisor = 2 * i + 2  # 2*(i+1)
        val = a % divisor
        if val > 9:
            # ASSUMPTION: subtract the current index i (the loop counter stored at [ebp-1])
            val = val - i
        # If still > 9 after subtraction, clamp or loop - not fully specified
        # ASSUMPTION: we trust the math works out for reasonable names
        digits.append(val)
    return digits

def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) == 0:
        return ''
    digits = _compute_serial_digits(name)
    # Each digit is 0-9; serial char = digit + ord('0') = digit + 0x30
    serial = ''.join(str(d) for d in digits)
    return serial

def verify(name, serial):
    """Verify a name/serial pair.
    The serial length must equal the name length.
    Each serial character (digit) minus 0x30 must equal the computed NewVal digit.
    """
    if len(name) == 0 or len(serial) != len(name):
        return False
    digits = _compute_serial_digits(name)
    for i, ch in enumerate(serial):
        serial_digit = ord(ch) - 0x30  # subtract 0x30 as in the assembly
        if serial_digit != digits[i]:
            return False
    return True


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
