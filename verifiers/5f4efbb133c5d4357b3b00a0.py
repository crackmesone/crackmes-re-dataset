from datetime import date, timedelta
import random


def _parse_date(serial: str):
    """Parse a date string in m/d/Y format, returning (month, day, year) or None."""
    parts = serial.strip().split('/')
    if len(parts) != 3:
        return None
    try:
        month = int(parts[0])
        day = int(parts[1])
        year = int(parts[2])
        return month, day, year
    except ValueError:
        return None


def verify(name: str, serial: str) -> bool:
    """
    The program reads a date of birth in M/D/YYYY format.
    It uses strptime with '%m/%d/%Y' to parse the date into a struct tm,
    then mktime() to convert to epoch seconds.
    It then calls time(NULL) and localtime() to get the current date.
    
    The age check compares year fields using a SIGNED comparison (jg).
    The flaw: tm_year in struct tm stores years since 1900, stored in a
    signed integer. If the birth year is >= 128 (i.e., year 2028+),
    the tm_year field (year - 1900) would be >= 128, which wraps to a
    negative value in a signed byte interpretation -- but more precisely
    the bug is that when comparing the year difference, using signed
    integer comparison allows negative differences (very old dates or
    overflow dates) to pass the >= 18 check.
    
    The actual validation logic (reconstructed from the writeup and keygen):
    1. Parse birth date via strptime("%m/%d/%Y")
    2. Get current date via time(NULL) + localtime()
    3. Compute age = current_year - birth_year (using tm_year, years since 1900)
    4. The check uses signed comparison: if age > 18 (jg = jump if greater, signed)
       OR (age == 18 and month/day checks pass), accept.
    
    The FLAW exploited by the keygen:
    tm_year is stored as an int (years since 1900). If birth year is such that
    tm_year is large enough to appear as if year-difference is negative when
    truncated to a signed byte (or the mktime result overflows time_t and
    wraps negative), the signed comparison treats a huge future year as
    'older than 18 years ago'.
    
    Specifically from the keygen: valid years are those where
    (today.year - birth_year) in binary has bit 7 set (i.e., the low byte
    of the year difference is >= 128 when interpreted as unsigned but < 0
    when interpreted as signed 8-bit), causing the signed jg to pass.
    
    The keygen uses: year_offset = 128 + i*256, birth_year = today.year - year_offset
    This makes the difference = year_offset = 128, 384, 640, ...
    As a signed 8-bit value, 128 = -128 < 0, so the signed comparison
    'age > 18' (signed) passes because a large positive int like 128
    is > 18 as a 32-bit signed int... 
    
    ASSUMPTION: The exact comparison is on the full 32-bit tm_year difference,
    and the bug is simply that extremely old dates (birth year far in the past)
    cause mktime to return -1 or a very large/small time_t, making the
    time difference calculation overflow or produce a value that passes
    the signed age check. The keygen finds years where today.year - year = 128, 384, etc.
    which as signed values are all > 18, so they pass. The 'exploit' is dates
    like year 100 AD where the age difference overflows or strptime produces
    an unexpected tm_year.
    
    For our Python verify(), we reimplement the keygen's logic:
    A serial is valid if the birth year satisfies:
        diff = today.year - birth_year
        diff in {128 + 256*i for i in 0, 1, 2, ...} and diff > 0
    AND the birth month/day match today's month/day (approximately, +1 day)
    
    ASSUMPTION: The day/month check is loose (the keygen adds timedelta(1) to handle
    boundary, suggesting the program checks if birthday has passed this year).
    We implement a generous check.
    """
    parsed = _parse_date(serial)
    if parsed is None:
        return False
    month, day, year = parsed
    
    try:
        birth = date(year=year, month=month, day=day)
    except ValueError:
        return False
    
    today = date.today()
    diff_years = today.year - birth.year
    
    # Normal 18+ check
    if diff_years > 18 or (diff_years == 18 and (today.month, today.day) >= (birth.month, birth.day)):
        return True
    
    # ASSUMPTION: The signed integer overflow exploit:
    # The binary uses a signed comparison on what should be an age check.
    # Years that are 128 + 256*k years ago from today pass the signed check.
    # The keygen generates: year_offset = 128 + i*256, birth_year = today.year - year_offset
    # We check if diff_years matches this pattern (128 mod 256 == 128, i.e., diff_years % 256 == 128)
    # AND diff_years > 0 (birth year must be valid / in the past)
    if diff_years > 0 and diff_years % 256 == 128:
        return True
    
    return False


def keygen(name: str) -> str:
    """Generate a valid date-of-birth serial exploiting the signed integer flaw."""
    keys = []
    today = date.today()
    i = 0
    while True:
        year_offset = 128 + i * 256
        birth_year = today.year - year_offset
        if birth_year < 1 or year_offset >= today.year:
            # ASSUMPTION: stop when birth year would be <= 0 or unreasonably old
            if birth_year < 1:
                break
        try:
            # The birth date is today + 1 day, but in the calculated birth year
            birth_day = date(year=birth_year, month=today.month, day=today.day) + timedelta(days=1)
            keys.append(birth_day)
        except ValueError:
            pass
        i += 1
        if year_offset >= today.year:
            break
    
    if not keys:
        # Fallback: use i=0 directly
        birth_year = today.year - 128
        birth_day = date(year=birth_year, month=today.month, day=today.day) + timedelta(days=1)
        keys.append(birth_day)
    
    key = random.choice(keys)
    return "{}/{}/{}".format(key.month, key.day, key.year)



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
