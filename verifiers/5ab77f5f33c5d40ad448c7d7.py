import random
import string

CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def _compute_sum(name: str, password20: str) -> float:
    """
    Replicates the C# logic:
      length = len(name) + 20
      sum = length
      sum += sum of (ord(c) * 0x10) for c in name
      sum += sum of (ord(c) * 0x10) for c in password20
    The check passes when sum / length == int(sum / length),
    i.e. sum is divisible by length (as a float with no remainder).
    Note: C# Convert.ToInt16(char * 0x10) converts char to short then multiplies.
    In Python we use ord(c) * 0x10 which matches for ASCII.
    """
    length = len(name) + 20
    total = float(length)
    for c in name:
        total += ord(c) * 0x10
    for c in password20:
        total += ord(c) * 0x10
    return total, length


def verify(name: str, serial: str) -> bool:
    """
    Verifies a serial for a given name.
    Serial format: XXXXX-XXXXX-XXXXX-XXXXX  (20 alphanum chars + 3 dashes = 23 chars)
    Each group is 5 chars from 0-9 and A-Z.
    """
    # Remove dashes and check format
    stripped = serial.replace('-', '')
    if len(stripped) != 20:
        return False
    # Check all chars are valid
    for c in stripped:
        if c not in CHARS:
            return False
    # Check serial has dashes at positions 5,11,17 (groups of 5)
    parts = serial.split('-')
    if len(parts) != 4 or any(len(p) != 5 for p in parts):
        return False
    # Compute sum check
    total, length = _compute_sum(name, stripped)
    # Condition: sum / length has no fractional part
    return (total / length) == int(total / length)


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name using random search (same approach as original keygen).
    Stops when the divisibility condition is met.
    # ASSUMPTION: The charset is exactly '0'-'9' and 'A'-'Z' (36 chars), as shown in the switch statement.
    # ASSUMPTION: The condition is sum % length == 0 (float division check from C# code).
    """
    length = len(name) + 20
    # Precompute the name contribution
    name_contrib = float(length)
    for c in name:
        name_contrib += ord(c) * 0x10

    while True:
        pwd_chars = [random.choice(CHARS) for _ in range(20)]
        pwd_contrib = sum(ord(c) * 0x10 for c in pwd_chars)
        total = name_contrib + pwd_contrib
        if (total / length) == int(total / length):
            raw = ''.join(pwd_chars)
            serial = raw[0:5] + '-' + raw[5:10] + '-' + raw[10:15] + '-' + raw[15:20]
            return serial



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
