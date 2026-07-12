# Reconstructed keygen for BiSHoP's VB Crackme #5
# Based on Pumqara's writeup
#
# Algorithm (as described):
#   1. Name must not contain spaces.
#   2. For each character in name: compute char_val^2, accumulate sum.
#      => sum_sq = sum of (ord(c)^2) for c in name
#   3. After loop: new_val = sum_sq^2 + sum_sq
#      => final_val = sum_sq * sum_sq + sum_sq  (i.e. sum_sq*(sum_sq+1))
#
# The writeup is truncated before showing exactly how the final_val
# is converted to the serial string (e.g. str(final_val), hex, etc.).
# ASSUMPTION: The serial is simply str(final_val) (decimal representation).
# ASSUMPTION: The comparison is a straightforward string equality check.

def compute_serial_value(name: str) -> int:
    """Compute the numeric serial value from the name."""
    # Step 1: sum of squares of char ordinals
    sum_sq = 0
    for c in name:
        val = ord(c)
        sum_sq += val * val  # Char^2 accumulated

    # Step 2: final_val = sum_sq^2 + sum_sq  (i.e. sum_sq * (sum_sq + 1))
    final_val = sum_sq * sum_sq + sum_sq
    return final_val


def keygen(name: str) -> str:
    """Generate a serial for a given name."""
    if ' ' in name:
        raise ValueError("Name must not contain spaces")
    if len(name) == 0:
        raise ValueError("Name must not be empty")
    final_val = compute_serial_value(name)
    # ASSUMPTION: serial is the decimal string representation of final_val
    return str(final_val)


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    if ' ' in name:
        return False
    if len(name) == 0:
        return False
    expected = keygen(name)
    return serial.strip() == expected



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
