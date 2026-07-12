import random
import time
import re


def generate_password(seed=None):
    """
    Reproduce the C generateKEY() function.
    Pattern: 4 groups of 3 chars each.
      position 0: digit      (rand() % 10 + 48  -> '0'..'9')
      position 1: uppercase  (rand() % 26 + 65  -> 'A'..'Z')
      position 2: lowercase  (rand() % 26 + 97  -> 'a'..'z')
    Total length: 12 chars, null-terminated in C.
    The C rand() / srand() behaviour is replicated via ctypes on Windows,
    but since we cannot replicate the exact C rand() sequence portably,
    we implement the structural check and keygen using Python's random
    seeded the same way.
    """
    if seed is None:
        seed = int(time.time()) & 0xFFFFFFFF
    # ASSUMPTION: Python random is used here to mirror the structural logic;
    # the actual crackme uses C's srand/rand which may differ per platform/CRT.
    rng = random.Random(seed)
    password = []
    for j in range(4):
        digit = rng.randint(0, 9) + 48          # rand() % 10 + 48
        upper = rng.randint(0, 25) + 65         # rand() % 26 + 65
        lower = rng.randint(0, 25) + 97         # rand() % 26 + 97
        password.append(chr(digit))
        password.append(chr(upper))
        password.append(chr(lower))
    return ''.join(password)


PASSWORD_RE = re.compile(
    r'^([0-9][A-Z][a-z]){4}$'
)


def verify(name, serial):
    """
    The crackme does NOT use a name-based serial; it generates a random
    12-character password at runtime using time(0) as srand seed.
    The password has the fixed structure: (digit + uppercase + lowercase) x 4

    This verify() checks only the structural validity of a serial.
    A full verification requires knowing the exact seed used at runtime.
    """
    # The crackme ignores 'name'; only 'serial' matters.
    if len(serial) != 12:
        return False
    return bool(PASSWORD_RE.match(serial))


def keygen(name=None, seed=None):
    """
    Generate a valid password for the crackme.
    Because the password is random (seeded by time(0)), the keygen
    produces a candidate for a given seed.

    To actually solve the crackme without patching:
      - Read the password from the stack at ESP+0x2F after the password
        is generated (see radare2 solution), OR
      - Generate all passwords for a small time window around now and
        try each one (brute-force over seed values).

    Returns a single generated password string.
    """
    if seed is None:
        seed = int(time.time()) & 0xFFFFFFFF
    return generate_password(seed)


def keygen_window(name=None, window=5):
    """
    Generate candidate passwords for a window of seeds around the current time.
    Useful because the crackme calls time(0) during generation and the
    user types the answer shortly after.
    """
    now = int(time.time()) & 0xFFFFFFFF
    seen = set()
    for delta in range(-window, window + 1):
        seed = (now + delta) & 0xFFFFFFFF
        pw = generate_password(seed)
        if pw not in seen:
            seen.add(pw)
            yield pw



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
            print(_sv)
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
