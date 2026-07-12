#!/usr/bin/env python3
# Reconstruction of mok_bhanga by obnoxious
# Based on the keygen writeup by Drakenza

import hashlib
import datetime

# --- Helper functions (ported from Python 2 writeup) ---

def lukowa(string):
    """Subtract 1 from each char's ordinal, then remove '/' characters."""
    str2 = ""
    for ch in string:
        str2 += chr(ord(ch) - 1)
    return str2.replace("/", "")

def inv_lukowa(string):
    """Add 1 to each char's ordinal."""
    str2 = ""
    for ch in string:
        str2 += chr(ord(ch) + 1)
    return str2

def _md5_hex_upper(s):
    """Return uppercase hex string of MD5 digest bytes, formatted as %X per byte."""
    if isinstance(s, str):
        s = s.encode('latin-1')
    digest = hashlib.md5(s).digest()
    result = ""
    for b in digest:
        result = "%s%X" % (result, b)
    return result

def aana(string):
    """MD5 of string, take hex chars [10:20]."""
    return _md5_hex_upper(string)[10:20]

def sinakta(sysun):
    """MD5 of sysun string, take hex chars [5:14]."""
    return _md5_hex_upper(sysun)[5:14]

# The large CRC32 lookup table used by saosunkibuja
_SAOSUNKIBUJA_ARR = [
    "00", "00", "00", "00", "96", "30", "07", "77", "2C", "61", "0E", "EE", "BA", "51", "09", "99",
    "19", "C4", "6D", "07", "8F", "F4", "6A", "70", "35", "A5", "63", "E9", "A3", "95", "64", "9E",
    "32", "88", "DB", "0E", "A4", "B8", "DC", "79", "1E", "E9", "D5", "E0", "88", "D9", "D2", "97",
    "2B", "4C", "B6", "09", "BD", "7C", "B1", "7E", "07", "2D", "B8", "E7", "91", "1D", "BF", "90",
    "64", "10", "B7", "1D", "F2", "20", "B0", "6A", "48", "71", "B9", "F3", "DE", "41", "BE", "84",
    "7D", "D4", "DA", "1A", "EB", "E4", "DD", "6D", "51", "B5", "D4", "F4", "C7", "85", "D3", "83",
    "56", "98", "6C", "13", "C0", "A8", "6B", "64", "7A", "F9", "62", "FD", "EC", "C9", "65", "8A",
    "4F", "5C", "01", "14", "D9", "6C", "06", "63", "63", "3D", "0F", "FA", "F5", "0D", "08", "8D",
    "C8", "20", "6E", "3B", "5E", "10", "69", "4C", "E4", "41", "60", "D5", "72", "71", "67", "A2",
    "D1", "E4", "03", "3C", "47", "D4", "04", "4B", "FD", "85", "0D", "D2", "6B", "B5", "0A", "A5",
    "FA", "A8", "B5", "35", "6C", "98", "B2", "42", "D6", "C9", "BB", "DB", "40", "F9", "BC", "AC",
    "E3", "6C", "D8", "32", "75", "5C", "DF", "45", "CF", "0D", "D6", "DC", "59", "3D", "D1", "AB",
    "AC", "30", "D9", "26", "3A", "00", "DE", "51", "80", "51", "D7", "C8", "16", "61", "D0", "BF",
    "B5", "F4", "B4", "21", "23", "C4", "B3", "56", "99", "95", "BA", "CF", "0F", "A5", "BD", "B8",
    "9E", "B8", "02", "28", "08", "88", "05", "5F", "B2", "D9", "0C", "C6", "24", "E9", "0B", "B1",
    "87", "7C", "6F", "2F", "11", "4C", "68", "58", "AB", "1D", "61", "C1", "3D", "2D", "66", "B6"
]

def saosunkibuja(i):
    """Index into the CRC32-like table at position (i*3 + 0x1a7).
    NOTE: The full table was truncated in the writeup; only first 128 entries shown.
    ASSUMPTION: The table continues but was cut off. We only have partial data.
    """
    idx = (i * 3) + 0x1a7
    # ASSUMPTION: table is much larger; only first portion available
    if idx < len(_SAOSUNKIBUJA_ARR):
        return _SAOSUNKIBUJA_ARR[idx]
    raise IndexError("saosunkibuja table truncated at index %d" % idx)

# --- assalek and further functions were truncated in the writeup ---
# ASSUMPTION: assalek takes sinakta output and processes it through saosunkibuja
# to produce part of the serial. The exact logic is unknown due to truncation.

def brute_aana(aana_str):
    """Brute-force a 5-letter lowercase string whose aana() matches aana_str."""
    chars = "abcdefghijklmnopqrstuvwxyz"
    c = [0, 0, 0, 0, 0]
    for _ in range(26**5):
        trial = chars[c[0]] + chars[c[1]] + chars[c[2]] + chars[c[3]] + chars[c[4]]
        if aana(trial) == aana_str:
            return trial
        # increment counter
        c[4] += 1
        for pos in range(4, 0, -1):
            if c[pos] > 25:
                c[pos] = 0
                c[pos - 1] += 1
        if c[0] > 25:
            break
    return None

# --- Serial / verification logic ---
# Based on the writeup structure:
#   1. aana(name) produces a 10-char hex substring of MD5
#   2. lukowa() / inv_lukowa() shift chars by -1/+1 and strip '/'
#   3. sinakta() takes a system/date value, produces 9-char hex substring
#   4. saosunkibuja() does a CRC32-table lookup
#   5. assalek (truncated) combines these into a serial
#   6. The serial appears to be independent of 'name' for the date portion
#      (it uses current date/system value)
# ASSUMPTION: The serial format is: inv_lukowa(aana(name)) + "-" + <date_based_part>
# ASSUMPTION: The name field is the only user input; serial is derived deterministically.

def keygen(name):
    """Generate a serial for the given name.
    ASSUMPTION: Full serial = inv_lukowa(aana(name)) joined with date component.
    The date/system component (sinakta/assalek) is truncated and cannot be fully reconstructed.
    """
    name_part = inv_lukowa(aana(name))
    # ASSUMPTION: date component uses today's date formatted and passed to sinakta
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")  # ASSUMPTION: exact format unknown
    date_part = sinakta(date_str)
    # ASSUMPTION: serial is these two parts joined with '-'
    serial = name_part + "-" + date_part
    return serial

def verify(name, serial):
    """Verify name/serial pair.
    ASSUMPTION: We reconstruct what the serial should be and compare.
    Due to truncation of assalek(), full verification cannot be confirmed.
    """
    # Split serial into parts
    parts = serial.split("-")
    if len(parts) < 2:
        return False
    name_part = parts[0]
    date_part = parts[1]

    # Check name part: should equal inv_lukowa(aana(name))
    expected_name_part = inv_lukowa(aana(name))
    if name_part != expected_name_part:
        return False

    # Check date part: sinakta of today's date
    # ASSUMPTION: date format and exact input to sinakta unknown
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")  # ASSUMPTION
    expected_date_part = sinakta(date_str)
    if date_part != expected_date_part:
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
