import math

def _compute_serial_double(name: str) -> str:
    """
    Replicates the original VB.NET behaviour where 'sum' is typed as Object
    (backed by Double/float64). For any non-empty name the result overflows
    to infinity after enough iterations, so the serial is always 'Infinity'.
    """
    left = 0.0  # float64, matches VB Object/Double behaviour
    lname = len(name)
    for i in range(0, 10001):  # 0 to 10000 inclusive
        if i % 100 != 0:
            left = (left * 9) + lname
        else:
            left += 1
    left += lname
    if math.isinf(left):
        return 'Infinity'
    return str(left)


def _compute_serial_long(name: str) -> str:
    """
    What the serial WOULD be if the author had used a Long/int instead of
    Object/Double. Included for completeness and to allow testing.
    """
    left = 0  # arbitrary-precision integer
    lname = len(name)
    for i in range(0, 10001):  # 0 to 10000 inclusive
        if i % 100 != 0:
            left = (left * 9) + lname
        else:
            left += 1
    left += lname
    return str(left)


def verify(name: str, serial: str) -> bool:
    """
    Replicates the actual crackme check.
    - name must be non-empty.
    - Because VB Object arithmetic overflows to Double infinity, the expected
      serial is always the string 'Infinity' for any non-empty name.
    """
    if not name:
        return False  # crackme shows a 'You\'re kidding me.' message
    expected = _compute_serial_double(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Returns the valid serial for the given name.
    Per the write-up, for any non-empty name the Double arithmetic overflows
    and the serial is always 'Infinity'.
    """
    if not name:
        raise ValueError('Name must be non-empty')
    return _compute_serial_double(name)



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
