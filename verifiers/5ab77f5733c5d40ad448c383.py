# Reconstruction of 'crackme_false_by_vctor' validation algorithm
# Based on the namegen.cpp solution by br0ken
#
# KEY INSIGHT from the writeup:
# The crackme ALWAYS shows the badboy when you press 'Check'.
# The GOODBOY appears when you press 'Exit' after entering valid name/serial.
# The namegen works BACKWARDS: given a serial, it generates a valid name.
#
# Algorithm (from namegen.cpp):
#   For each pair of serial characters at positions j and j+1:
#     name[i] = serial[j] + serial[j+1] - 0x23
#   i increments by 1, j increments by 2
#   Loop while i <= len (where len = strlen(serial))
#   name[len/2] = '\0'  (null-terminate at half the serial length)
#
# So: name[i] = ord(serial[2*i]) + ord(serial[2*i+1]) - 0x23
# for i in range(len(serial) // 2)
#
# ASSUMPTION: The serial must have an even number of characters (min 2 chars, numbers preferred)
# ASSUMPTION: The actual check in the crackme compares computed name against the entered name
# ASSUMPTION: The loop bound 'i <= len' with len=strlen(serial) seems like it could read one
#             past the end; we conservatively use i < len//2 pairs.

def _compute_name_from_serial(serial):
    """Given a serial string, compute the expected name."""
    name_chars = []
    s = serial
    n = len(s)
    # ASSUMPTION: serial must have at least 2 characters
    if n < 2:
        return None
    # ASSUMPTION: we process len//2 pairs (the null terminator at len/2 defines the name length)
    num_pairs = n // 2
    for i in range(num_pairs):
        j = 2 * i
        if j + 1 >= n:
            break
        val = ord(s[j]) + ord(s[j + 1]) - 0x23
        # ASSUMPTION: result is a printable ASCII character; no explicit range check in source
        name_chars.append(chr(val & 0xFF))
    return ''.join(name_chars)


def verify(name, serial):
    """
    Verify name/serial pair.
    The algorithm: compute expected name from serial, compare with given name.
    NOTE: The crackme always shows BADBOY on 'Check'; goodboy appears on 'Exit'.
    ASSUMPTION: The underlying check computes name from serial as in namegen.cpp.
    """
    if len(serial) < 2:
        return False
    expected_name = _compute_name_from_serial(serial)
    if expected_name is None:
        return False
    return name == expected_name


def keygen(name):
    """
    Generate a serial for the given name.
    We need to find serial pairs (a, b) such that ord(a) + ord(b) - 0x23 == ord(name[i]).
    We choose a='1' (0x31) and solve for b: ord(b) = ord(name[i]) + 0x23 - 0x31
    ASSUMPTION: result characters are in printable ASCII range.
    """
    if not name:
        return None
    serial_chars = []
    # ASSUMPTION: we pick a fixed first char of each pair as '1' (0x31)
    base = ord('1')  # 0x31
    for ch in name:
        target = ord(ch) + 0x23  # ord(a) + ord(b) = ord(name[i]) + 0x23
        b_val = target - base
        if b_val < 0x20 or b_val > 0x7E:
            # Try a different base if out of printable range
            # ASSUMPTION: try '0' (0x30)
            base_alt = 0x30
            b_val = target - base_alt
            if b_val < 0x20 or b_val > 0x7E:
                # ASSUMPTION: just clamp or skip
                return None
            serial_chars.append(chr(base_alt))
            serial_chars.append(chr(b_val))
        else:
            serial_chars.append(chr(base))
            serial_chars.append(chr(b_val))
    return ''.join(serial_chars)



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
