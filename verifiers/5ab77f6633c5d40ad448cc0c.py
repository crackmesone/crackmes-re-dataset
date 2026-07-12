import datetime
import os
import sys

# Reconstructed from the writeup for abu_crackme_5 by gauri
# The serial is built from system date/time/drive-letter at the moment of checking.
#
# Serial format (11 chars):
#   [1] First letter of weekday name  (e.g. 'M' for Monday)
#   [1] First char of hour string     (12-hour format, e.g. '3' for 3:xx PM)
#         NOTE: If hour is 10,11,12 only the first digit '1' is appended
#   [2] 'AM' or 'PM'                  (only works correctly on 12-hr systems;
#         on 24-hr systems seconds are appended instead - NOT supported here)
#   [4] Year digits                   (e.g. '2005')
#   [1] Drive letter of current directory (e.g. 'E')
#   [1] First letter of month name    (e.g. 'O' for October)
#   --- Total target = 1+1+2+4+1+1 = 10 chars, but writeup says 11 ---
#
# ASSUMPTION: The writeup example 'M03PM2005EO' gives 11 chars.
#   Breaking it down: M=Mon, 0=? (unclear), 3=hour digit, PM, 2005, E=drive, O=Oct
#   It seems a literal '0' is always inserted between day-letter and hour-digit
#   (the code shows PUSH 00401E48 which is a literal '0' string pushed before strcat)
#   So: day_letter + '0' + left(hour,1) + am_pm + year + drive_letter + month_letter
#   = 1 + 1 + 1 + 2 + 4 + 1 + 1 = 11 chars  -- matches!

DAY_NAMES   = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
MONTH_NAMES = ['January','February','March','April','May','June',
                'July','August','September','October','November','December']


def _build_serial(name=None, now=None, drive_letter=None):
    """
    Build the expected 11-character serial from system state.
    name     - not used in the algorithm (crackme ignores username)
    now      - datetime.datetime object (defaults to datetime.datetime.now())
    drive_letter - single char, uppercase drive letter (defaults to CWD drive)
    """
    if now is None:
        now = datetime.datetime.now()

    if drive_letter is None:
        cwd = os.getcwd()
        # ASSUMPTION: Use the drive letter as-is from GetCurrentDirectoryA
        # (the writeup notes a bug: sometimes lowercase is returned from winrar)
        if len(cwd) >= 2 and cwd[1] == ':':
            drive_letter = cwd[0]  # may be upper or lower depending on how it was launched
        else:
            # ASSUMPTION: non-Windows or no drive letter; use 'C' as fallback
            drive_letter = 'C'

    # 1. First letter of weekday name (Monday=0 in Python)
    weekday_idx = now.weekday()  # 0=Monday .. 6=Sunday
    day_letter = DAY_NAMES[weekday_idx][0]  # e.g. 'M'

    # 2. Literal '0' (hardcoded in the binary at 00401E48)
    literal_zero = '0'

    # 3. First character of 12-hour clock hour string
    hour_12 = now.strftime('%I').lstrip('0') or '12'  # '1'..'12'
    # ASSUMPTION: stripping leading zero to get "3" from "03"
    # The example shows '3' for 3 PM, so VB's Format/Time gives e.g. "3:xx:xx PM"
    # Left(hour_string, 1) gives first digit
    # For hours 10,11,12 Left gives '1'; for 1-9 gives the digit itself
    hour_letter = hour_12[0]  # first char

    # 4. AM/PM indicator (2 chars)
    # ASSUMPTION: 12-hour system; on 24-hr system seconds are appended instead (not supported)
    am_pm = now.strftime('%p')  # 'AM' or 'PM'

    # 5. Year (4 digits)
    year_str = str(now.year)  # e.g. '2005'

    # 6. Drive letter (1 char, case depends on GetCurrentDirectoryA)
    dl = drive_letter

    # 7. First letter of month name
    month_idx = now.month - 1  # 0-based
    month_letter = MONTH_NAMES[month_idx][0]  # e.g. 'O' for October

    serial = day_letter + literal_zero + hour_letter + am_pm + year_str + dl + month_letter
    return serial


def verify(name, serial):
    """
    Verify the serial against the current system date/time/drive.
    NOTE: The crackme does NOT use the name in the algorithm.
    Also checks length == 11.
    """
    if len(serial) != 11:
        return False
    expected = _build_serial(name=name)
    return serial == expected


def keygen(name):
    """
    Generate the valid serial for the current moment.
    Must be entered quickly (within the same minute / AM-PM period).
    """
    return _build_serial(name=name)



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
