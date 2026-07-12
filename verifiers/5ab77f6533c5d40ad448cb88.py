from datetime import datetime


def _get_keycode(dt: datetime = None) -> int:
    """Compute the keycode for a given date (defaults to today)."""
    if dt is None:
        dt = datetime.now()
    day = dt.day
    month = dt.month
    year = dt.year
    # Format as decimal string 'DDMMYYYY' then parse as integer
    date_str = f"{day}{month}{year}"
    date_int = int(date_str)
    return date_int * 2 + 1004


def _get_expected_checkboxes(dt: datetime = None) -> dict:
    """
    Return the expected checkbox states based on the current day.
    day >= 15: ZRBEACH and HTKEEPER checked
    day < 15:  PHOENIX and NotApplicable checked
    """
    if dt is None:
        dt = datetime.now()
    if dt.day >= 15:
        return {
            'PHOENIX': False,
            'KUHOOK': False,
            'ZRBEACH': True,
            'HTKEEPER': True,
            'NotApplicable': False,
        }
    else:
        return {
            'PHOENIX': True,
            'KUHOOK': False,
            'ZRBEACH': False,
            'HTKEEPER': False,
            'NotApplicable': True,
        }


def verify(name: str, serial: str) -> bool:
    """
    Verify the serial (keycode) for the given date.

    In the crackme:
    - 'name' is not used; the key is purely date-based.
    - The serial must equal str(day*month*year_as_int * 2 + 1004)
      where the date integer is formed by concatenating day, month, year.
    - The interaction sequence must be: CheckBoxes (2), Edit/Fingerprint (3), Buttons (1) = "231"
    - The checkboxes must match the day-dependent state.

    For this Python implementation we just check the numeric value.
    """
    dt = datetime.now()
    expected = _get_keycode(dt)
    try:
        entered = int(serial.strip())
    except (ValueError, AttributeError):
        return False
    return entered == expected


def keygen(name: str = '', dt: datetime = None) -> str:
    """
    Generate the valid serial (keycode) for today (or a given date).
    The serial is: int(str(day) + str(month) + str(year)) * 2 + 1004
    """
    if dt is None:
        dt = datetime.now()
    code = _get_keycode(dt)
    return str(code)



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
