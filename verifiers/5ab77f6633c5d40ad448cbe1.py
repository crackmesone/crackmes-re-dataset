import random
import datetime

# Prime numbers list used by the keygen (4-digit primes starting from 1009)
SMALL_PRIMES_4 = [
    1009,1013,1019,1021,1031,1033,1039,1049,1051,1061,1063,1069,1087,1091,1093,
    1097,1103,1109,1117,1123,1129,1151,1153,1163,1171,1181,1187,1193,1201,1213,
    1217,1223,1229,1231,1237,1249,1259,1277,1279,1283,1289,1291,1297,1301,1303,
    1307,1319,1321,1327,1361,1367,1373,1381,1399,1409,1423,1427,1429,1433,1439,
    1447,1451,1453,1459,1471,1481,1483,1487,1489,1493,1499,1511,1523,1531,1543,
    1549,1553,1559,1567,1571,1579,1583,1597,1601,1607,1609,1613,1619,1621,1627,
    1637,1657,1663,1667,1669,1693,1697,1699,1709,1721,1723,1733,1741,1747,1753,
    1759,1777,1783,1787,1789,1801,1811,1823,1831,1847,1861,1867,1871,1873,1877,
    1879,1889,1901,1907,1913,1931,1933,1949,1951,1973,1979,1987,1993,1997,1999,
    2003,2011,2017,2027,2029,2039,2053,2063,2069,2081,2083,2087,2089,2099,2111,
    2113,2129,2131,2137,2141,2143,2153,2161,2179,2203,2207,2213,2221,2237,2239,
    2243,2251,2267,2269,2273,2281,2287,2293,2297,2309
]

# Day code mapping: Python weekday() returns 0=Monday..6=Sunday
# VB Weekday with vbSunday: 1=Sunday,2=Monday,...,7=Saturday
DAY_CODES = {
    1: "EIV9",  # Sunday
    2: "AXYZ",  # Monday
    3: "BW8J",  # Tuesday
    4: "NPLM",  # Wednesday
    5: "HKOD",  # Thursday
    6: "CFGQ",  # Friday
    7: "RSTU",  # Saturday
}

def _python_weekday_to_vb(py_weekday):
    """Convert Python weekday (0=Mon) to VB Weekday with vbSunday (1=Sun,2=Mon,...,7=Sat)"""
    # Python: 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri,5=Sat,6=Sun
    # VB:     2=Mon,3=Tue,4=Wed,5=Thu,6=Fri,7=Sat,1=Sun
    mapping = {0:2, 1:3, 2:4, 3:5, 4:6, 5:7, 6:1}
    return mapping[py_weekday]

def _get_day_str(date=None):
    if date is None:
        date = datetime.date.today()
    py_wd = date.weekday()
    vb_wd = _python_weekday_to_vb(py_wd)
    return DAY_CODES.get(vb_wd, "NONE")

def _get_serial_parts(name, prime, day_str):
    """
    Serial format from VB keygen (Solution 2):
    daystr + "-" + rprime + "-" + last_char + first_char + third_char
    i.e., name[-1] + name[0] + name[2]
    """
    last_char = name[-1]
    first_char = name[0]
    third_char = name[2]
    suffix = last_char + first_char + third_char
    serial = "{}-{}-{}".format(day_str, prime, suffix)
    return serial

def keygen(name, date=None):
    """
    Generate a valid serial for the given name.
    The prime is chosen randomly from SMALL_PRIMES_4 (indices 1..175 in VB, 0-based here).
    The day string depends on the current day of week.
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long")
    # ASSUMPTION: the prime index range in VB was Rand(1,175) meaning indices 1..175 inclusive
    # The VB string was 4-char primes concatenated; index a gives Mid(str, a*4+1, 4)
    # so a in [1..175] maps to primes at positions 1..175 in the string (0-indexed: 1..175)
    # SMALL_PRIMES_4[0] = 1009 (a=0), SMALL_PRIMES_4[1]=1013 (a=1), ...
    # VB Rand(1,175) -> a in [1,175], so primes index 1..175
    prime_idx = random.randint(1, min(175, len(SMALL_PRIMES_4)-1))
    prime = SMALL_PRIMES_4[prime_idx]
    day_str = _get_day_str(date)
    return _get_serial_parts(name, prime, day_str)

def verify(name, serial):
    """
    Verify a serial for a given name.
    Serial format: XXXX-PPPP-YZW
    where XXXX = day code (4 chars), PPPP = 4-digit prime, YZW = name[-1]+name[0]+name[2]
    ASSUMPTION: the crackme also validates the day code against the current day.
    ASSUMPTION: the prime must be in SMALL_PRIMES_4.
    ASSUMPTION: the serial length must be 13 chars (4+1+4+1+3).
    """
    if len(name) < 4:
        return False
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    day_str, prime_str, suffix = parts
    # Check day code matches today
    expected_day_str = _get_day_str()
    if day_str != expected_day_str:
        # ASSUMPTION: day must match current weekday
        return False
    # Check prime
    try:
        prime_val = int(prime_str)
    except ValueError:
        return False
    if prime_val not in SMALL_PRIMES_4:
        return False
    # Check suffix: name[-1] + name[0] + name[2]
    expected_suffix = name[-1] + name[0] + name[2]
    if suffix != expected_suffix:
        return False
    return True


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
