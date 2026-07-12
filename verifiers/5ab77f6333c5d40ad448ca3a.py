import datetime

def _len_calc(name: str) -> int:
    """Multiply 99 by the username length (capped at 25)."""
    length = min(len(name), 25)
    return 99 * length


def _hex_vb(value: int) -> str:
    """Convert integer to uppercase hex string (no '0x' prefix), as VB Hex() would."""
    return hex(value)[2:].upper()


def generate_serial(name: str, dt: datetime.datetime) -> str:
    """
    Serial mask:
      {LenCalc}-=?/73243-{Day}Ka050584-[%{Minute}Ka-74376BZe-34{Hour}Mi!\"%"

    {LenCalc} = 99 * min(len(name), 25)  (decimal string)
    {Day}     = Hex(day of month)         (uppercase, no prefix)
    {Minute}  = Hex(minute of hour)       (uppercase, no prefix)
    {Hour}    = Hex(hour of day)          (uppercase, no prefix)
    """
    len_calc = _len_calc(name)
    day_hex = _hex_vb(dt.day)
    minute_hex = _hex_vb(dt.minute)
    hour_hex = _hex_vb(dt.hour)

    serial = (
        f"{len_calc}-=?/73243-{day_hex}Ka050584-[%{minute_hex}Ka-74376BZe-34{hour_hex}Mi!\"%"
    )
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against the current system time.
    Also enforces the 'correct serial, wrong time' rule:
    the minute must be in [0, 29] for validation to succeed.
    """
    now = datetime.datetime.now()
    # The crackme rejects serials when minute >= 30
    if now.minute >= 30:
        return False
    expected = generate_serial(name, now)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name using the current time.
    NOTE: You must use this serial within the same minute it was generated,
    and only when the current minute is in [0, 29].
    """
    now = datetime.datetime.now()
    return generate_serial(name, now)



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
