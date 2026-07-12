import random
import string

# Algorithm recovered from solution writeups (jeffli6789 and pale_delirium)
# Constraints:
#   - name must be exactly 10 characters long
#   - serial (password) must be <= 50 characters long
#   - The program reads password from a file
#
# Core check (the 'different length' branch, which is the tractable path):
#   r9 = 0, r10 = 1
#   for k in range(len(data) - 1):         # outer loop over password chars (all but last)
#       for i in range(len(name)):          # inner loop over name chars (0..9)
#           val  = (ord(name[i]) + (ord(data[k]) ^ i)) & 0xf
#           val2 = (ord(data[k]) + i) | (i ^ k)
#           r9  += val * 2
#           r10 *= (val | val2)
#           r10 &= 0xffffffffffffffff
#   rcx = (r10 - r9) % (r9 + r10)
#   pass if rcx & 0xf in {1, 3, 9}   (i.e. 9 % (rcx & 0xf) == 0 and rcx & 0xf != 0)

LEGAL_CHARS = string.ascii_letters + string.digits


def _compute(name: str, serial: str):
    """Return (r9, r10) after running the inner loops."""
    data = serial
    r9 = 0
    r10 = 1
    for k in range(len(data) - 1):          # iterate over all but the last char
        for i in range(len(name)):          # iterate over all name chars
            val  = (ord(name[i]) + (ord(data[k]) ^ i)) & 0xf
            val2 = (ord(data[k]) + i) | (i ^ k)
            r9  += val * 2
            r10 *= (val | val2)
            r10 &= 0xffffffffffffffff        # keep to 64 bits
    return r9, r10


def verify(name: str, serial: str) -> bool:
    """Return True if (name, serial) is a valid pair."""
    # Length constraints
    if len(name) != 10:
        return False
    if len(serial) > 50:
        return False

    # ASSUMPTION: the 'same-length' branch (len(serial)==10) has more complex
    # logic that is not fully described in the writeups. We only implement the
    # 'different-length' branch which is the documented and exploited path.
    # For safety, if len(serial) == 10 we fall through to the same check;
    # the writeup says the other branch exists but gives no algorithm for it.

    r9, r10 = _compute(name, serial)

    # Avoid division by zero (degenerate case)
    divisor = r9 + r10
    if divisor == 0:
        return False

    rcx = (r10 - r9) % divisor
    # Pass condition: rcx & 0xf must be in {1, 3, 9}
    # Equivalently: rcx & 0xf != 0 and 9 % (rcx & 0xf) == 0
    return (rcx & 0xf) in {1, 3, 9}


def keygen(name: str, max_attempts: int = 500_000) -> str:
    """Find a valid serial for the given 10-character name by random search."""
    if len(name) != 10:
        raise ValueError("name must be exactly 10 characters long")

    # Use a password length != 10 to stay in the documented code path.
    # Lengths 7-9 or 11-20 work fine; 8 is used by the reference solutions.
    for _ in range(max_attempts):
        length = random.choice([7, 8, 9, 11, 12])
        candidate = ''.join(random.choice(LEGAL_CHARS) for _ in range(length))
        if verify(name, candidate):
            return candidate

    raise RuntimeError("keygen failed to find a serial within the attempt limit")


# ---- self-test with known-good pairs from the writeup ----

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
