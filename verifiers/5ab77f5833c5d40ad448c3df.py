# Keygen / verifier for m477hi45's serialme
# Algorithm fully recovered from the VBS keygen and C++ keygen source.
#
# The serial is 7 characters: KEY1 KEY2 KEY3 '-' KEY4 KEY5 KEY6
# (indices 0..6 in the key string, with position 3 always '-')
#
# The name must be at least 5 characters long (trailing spaces/empty not allowed).
# Only the first 4 characters of the name are used to determine the serial.
#
# alphanum = "0123456789abcdefghijklmnopqrstuvwxyz"
# VBS uses 1-based mid(), C++ uses 0-based array — both are consistent.

ALPHANUM = "0123456789abcdefghijklmnopqrstuvwxyz"

# Character group helpers (lowercase expected)
def _group1(c): return c in 'qwertyui'  # Note: VBS says q,w,e,r,t,y,u (7 chars)
def _g1(c): return c in 'qwertyu'
def _g2(c): return c in 'iopasdf'
def _g3(c): return c in 'ghjklzx'
def _g4(c): return c in 'cvbnm01'
def _g5(c): return c in '23456789'


def _get_serial(name: str) -> str:
    """
    Compute the 7-character serial for the given name.
    Name must be at least 5 chars; only first 4 chars matter for the key.
    The name is lowercased before processing (crackme compares lowercase).
    """
    name = name.lower()
    # Default key values (from C++ keygen defaults, 0-based):
    # p_key[0]=alphanum[2]='2', p_key[1]=alphanum[20]='k',
    # p_key[2]=alphanum[27]='r', p_key[3]='-',
    # p_key[4]=alphanum[7]='7', p_key[5]=alphanum[11]='b',
    # p_key[6]=alphanum[22]='m'
    # ASSUMPTION: default values are used only if a char falls into no group (e.g. uppercase after lower, punct)
    key = list("2kr-7bm")

    c0 = name[0] if len(name) > 0 else ''
    c1 = name[1] if len(name) > 1 else ''
    c2 = name[2] if len(name) > 2 else ''
    c3 = name[3] if len(name) > 3 else ''

    # --- 1st char of name -> key[0] and key[1] ---
    if _g1(c0):
        key[0] = ALPHANUM[2]   # '2'
        key[1] = ALPHANUM[10]  # 'a'
    if _g2(c0):
        key[0] = ALPHANUM[4]   # '4'
        key[1] = ALPHANUM[19]  # 'j'
    if _g3(c0):
        key[0] = ALPHANUM[3]   # '3'
        key[1] = ALPHANUM[27]  # 'r'
    if _g4(c0):
        key[0] = ALPHANUM[17]  # 'h'
        key[1] = ALPHANUM[16]  # 'g'
    if _g5(c0):
        key[0] = ALPHANUM[17]  # 'h'
        key[1] = ALPHANUM[16]  # 'g'

    # --- 2nd char of name -> key[2] ---
    if _g1(c1):
        key[2] = ALPHANUM[3]   # '3'
    if _g2(c1):
        key[2] = ALPHANUM[12]  # 'c'
    if _g3(c1):
        key[2] = ALPHANUM[8]   # '8'
    if _g4(c1):
        key[2] = ALPHANUM[4]   # '4'
    if _g5(c1):
        key[2] = ALPHANUM[2]   # '2'

    # key[3] is always '-'
    key[3] = '-'

    # --- 3rd char of name -> key[4] and key[5] ---
    if _g1(c2):
        key[5] = ALPHANUM[5]   # '5'
        key[4] = ALPHANUM[19]  # 'j'
    if _g2(c2):
        key[5] = ALPHANUM[17]  # 'h'
        key[4] = ALPHANUM[11]  # 'b'
    if _g3(c2):
        key[5] = ALPHANUM[11]  # 'b'
        key[4] = ALPHANUM[8]   # '8'
    if _g4(c2):
        key[5] = ALPHANUM[19]  # 'j'
        key[4] = ALPHANUM[2]   # '2'
    if _g5(c2):
        key[5] = ALPHANUM[21]  # 'l'
        key[4] = ALPHANUM[6]   # '6'

    # --- 4th char of name -> key[6] ---
    if _g1(c3):
        key[6] = ALPHANUM[13]  # 'd'
    if _g2(c3):
        key[6] = ALPHANUM[18]  # 'i'
    if _g3(c3):
        key[6] = ALPHANUM[6]   # '6'
    if _g4(c3):
        key[6] = ALPHANUM[16]  # 'g'
    if _g5(c3):
        key[6] = ALPHANUM[4]   # '4'

    return ''.join(key)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be at least 5 characters long.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")
    return _get_serial(name)


def verify(name: str, serial: str) -> bool:
    """
    Verify that the given serial is valid for the given name.
    """
    if len(name) < 5:
        return False
    expected = _get_serial(name)
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
