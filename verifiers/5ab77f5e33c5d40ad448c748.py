import ctypes

MIN_LEN = 3
MAX_LEN = 14
SUBTRACT = 0x3C7F  # 15487
PREFIX = 'SR8'


def _compute(name: str) -> int:
    """
    The core algorithm as seen in all writeups:
      sum = 0
      for each character c in name:
          sum = sum + ord(c) - 15487
    Returns sum interpreted as a signed 32-bit integer (matching C 'int' behaviour).
    """
    total = 0
    for c in name:
        total += ord(c)
        total -= SUBTRACT
    # Interpret as signed 32-bit int to match C behaviour (sprintf %d)
    return ctypes.c_int32(total).value


def verify(name: str, serial: str) -> bool:
    """
    Returns True if the serial matches the expected value for the given name.
    Name must be between 3 and 14 characters (inclusive).
    Serial format: SR8-<signed_decimal_int>
    """
    if not (MIN_LEN <= len(name) <= MAX_LEN):
        return False
    expected = keygen(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Raises ValueError if name length is not between 3 and 14.
    """
    if not (MIN_LEN <= len(name) <= MAX_LEN):
        raise ValueError(f'Name must be between {MIN_LEN} and {MAX_LEN} characters.')
    value = _compute(name)
    return f'{PREFIX}-{value}'



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
