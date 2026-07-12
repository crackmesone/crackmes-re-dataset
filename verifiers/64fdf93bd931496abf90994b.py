def luna(password: int) -> bool:
    """
    Luhn-like algorithm extracted from the 'luna' function in the crackme.
    Processes pairs of digits from right to left:
      - tens digit of current pair is doubled; if > 9, subtract 9
      - ones digit of current pair is added as-is
    Returns True if total sum % 10 == 0.
    """
    temp = 0
    total = 0
    p = password
    while p:
        temp = 2 * (p // 10 % 10)
        if temp > 9:
            temp -= 9
        total += temp + (p % 10)
        p //= 100
    return total % 10 == 0


def verify(name: str, serial: str) -> bool:
    """
    The crackme ignores 'name'; only the numeric serial matters.
    Valid serial must:
      1. Be a numeric string parseable as an integer.
      2. Satisfy 100000 <= value <= 10000000.
      3. Pass the luna() Luhn-like check.
    """
    # ASSUMPTION: name is not used in the check (confirmed by all writeups)
    try:
        value = int(serial)
    except (ValueError, TypeError):
        return False
    if value < 100000 or value > 10000000:
        return False
    return luna(value)


def keygen(name: str):
    """
    Generator yielding all valid serials in the accepted range.
    Known valid examples from writeups: 100008, 590000, 8648214, 1111111
    """
    for candidate in range(100000, 10000001):
        if luna(candidate):
            yield str(candidate)



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
