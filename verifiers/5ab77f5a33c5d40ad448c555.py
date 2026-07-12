import random
import string

# The keygen algorithm from algoritam.inc:
# 1. Get name length (must be <= 27)
# 2. Serial length = 27 - len(name)
# 3. Fill serial with random characters from the chars table using RDTSC % 61
#    (RDTSC is a timestamp counter - effectively random)
# 4. The serial is stored in positions [0 .. (27-len(name)-1)]
#
# ASSUMPTION: The verification in the crackme (VB side) checks that:
#   - name length <= 27
#   - serial length == 27 - len(name)
#   - serial characters are all from the allowed charset
# The writeup was truncated so the exact VB check logic is not fully shown.
# The keygen code is fully recovered, but the verify side is only partially known.

CHARS = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
BROJ = 61  # len(CHARS) - 1 = 61, used as AND mask

def keygen(name):
    """Generate a valid serial for the given name."""
    name_len = len(name)
    if name_len > 27:
        raise ValueError('Name too long (max 27 chars)')
    serial_len = 27 - name_len
    if serial_len == 0:
        return ''
    # RDTSC % (BROJ+1) but BROJ=61 means 'and eax, 61' => values 0..61
    # chars has 62 chars (indices 0..61), so AND with 61 gives valid index
    serial = ''
    for _ in range(serial_len):
        idx = random.randint(0, BROJ)  # simulating RDTSC & 61
        serial += CHARS[idx]
    return serial

def verify(name, serial):
    """Verify name/serial pair."""
    name_len = len(name)
    if name_len > 27:
        return False
    expected_len = 27 - name_len
    if len(serial) != expected_len:
        return False
    # ASSUMPTION: each serial character must be from the allowed charset
    for ch in serial:
        if ch not in CHARS:
            return False
    # ASSUMPTION: No further name-dependent transformation was shown in the truncated writeup.
    # The keygen produces purely random serials of the correct length from CHARS.
    # If the crackme does a deeper check (e.g. name-based transformation), it was truncated.
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
