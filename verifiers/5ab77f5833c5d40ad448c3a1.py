from datetime import datetime

def _get_date_int(date=None):
    """Return today's date as integer in ddmmyyyy format."""
    if date is None:
        date = datetime.now()
    return int(date.strftime("%d%m%Y"))


def verify(name: str, serial: str, date=None) -> bool:
    """
    Validate name/serial pair.
    Rules:
      1. Name must be at least 5 characters long.
      2. serial == sum(ord(c) for c in name) * date_as_int
         where date_as_int is today's date formatted as ddmmyyyy (e.g. 25092008).
    Note: serial is date-dependent, so a valid serial today is invalid tomorrow.
    """
    if len(name) < 5:
        return False
    date_int = _get_date_int(date)
    name_sum = sum(ord(c) for c in name)
    expected = name_sum * date_int
    try:
        return int(serial) == expected
    except (ValueError, TypeError):
        return False


def keygen(name: str, date=None) -> str:
    """
    Generate a valid serial for the given name (today's date by default).
    Name must be >= 5 characters.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long.")
    date_int = _get_date_int(date)
    name_sum = sum(ord(c) for c in name)
    return str(name_sum * date_int)



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
