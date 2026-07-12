# KeyGenMe #4 by serialcracker
# Algorithm fully recovered from VB source in writeup

code1 = "MRZLB1CA042TPSYJHVKEDGU8635X7WN9TB0S3DZG6ELU5J2MY74H9N8ARPX1VCKWRPD3UYZK1X49VA7TBGNLH0JC8W6S25MELJV7KUN3206B8DMCXT9PW4GHE5YRA1SZ5TN8Z6GK23LDCMEBA4VH91UW0P7JRSXYU4P7Y6HBEL3SJ98AGCN502ZDVWKMRX1TZJ7S3PERN5X29GVL8DBMTY0AW64CH1UKSVBX8A05H247RZ13DWNUC6JY9GPTEMLK"
code2 = "ZHDGTERAFDRDHHFH46FN38DFC32JC83JC8932KX9299DJOA92JAPD192EA3RUJCW903RUAIJF39RFJJFIJW85SIOIFJW390U32IOJSLKFJ3242058W09FI902853095890588AKIDJFAWE8UTRQ3845QF456E4F5A64F65AE4F654564FS564RF65S4RG65S4H65S4JH65456W3TGIOSUB895SUAOSV?YFAUIEJFA?PWIOERFJAWIOEFJWIOEFJW"

# VB Mid() is 1-based; Python substring is 0-based.
# VB: Mid(s, start, length) -> Python: s[start-1 : start-1+length]
# The VB source keygen uses:
#   fname = Asc(Left(name, 1))   -> 1-based ASCII value of first char
#   lname = Asc(Right(name, 1))  -> 1-based ASCII value of last char
#   Parts:
#     Mid(code1, fname,   3)  & Mid(code2, lname,   3)  -> part1
#     Mid(code1, fname-3, 3)  & Mid(code2, lname+2, 3)  -> part2
#     Mid(code1, fname+3, 3)  & Mid(code2, fname-2, 3)  -> part3  (note: uses fname not lname for code2)
#     Mid(code1, Len(name), 6)                           -> part4
#     Mid(code2, fname+4, 6)                             -> part5
#     Mid(code2, lname+9, 6)                             -> part6
# Serial = part1-part2-part3-part4-part5-part6
# The Drakenza VB.NET keygen uses 0-based indexing (C1 = Asc(...) - 1)
# Both are consistent.

def _mid(s, start_1based, length):
    """VB Mid() equivalent: 1-based, returns up to 'length' chars."""
    idx = start_1based - 1
    if idx < 0 or idx >= len(s):
        return ""
    return s[idx:idx + length]


def keygen(name: str) -> str:
    if not name:
        return ""
    fname = ord(name[0])   # Asc(Left(name, 1))
    lname = ord(name[-1])  # Asc(Right(name, 1))
    n = len(name)

    part1 = _mid(code1, fname,   3) + _mid(code2, lname,   3)
    part2 = _mid(code1, fname-3, 3) + _mid(code2, lname+2, 3)
    part3 = _mid(code1, fname+3, 3) + _mid(code2, fname-2, 3)  # note: code2 uses fname, not lname
    part4 = _mid(code1, n,       6)
    part5 = _mid(code2, fname+4, 6)
    part6 = _mid(code2, lname+9, 6)

    serial = part1 + "-" + part2 + "-" + part3 + "-" + part4 + "-" + part5 + "-" + part6
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify by generating the expected serial and comparing."""
    if not name:
        return False
    expected = keygen(name)
    return serial == expected



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
