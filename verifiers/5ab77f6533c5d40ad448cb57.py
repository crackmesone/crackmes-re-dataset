import os
import getpass

TABLE = 'C456.,NO0jUVR:Axyz;vwB)klm!?(1duDEILMSTfi a78J3KbceHo2qrgphstPQnFGWXYZ9'
TABLE_LEN = len(TABLE)  # Should be 71 (0x47)


def _get_system_username():
    # ASSUMPTION: The Windows username comes from GetUserNameA().
    # On non-Windows systems we fall back to the OS login name.
    try:
        import ctypes
        buf = ctypes.create_string_buffer(256)
        size = ctypes.c_ulong(256)
        ctypes.windll.advapi32.GetUserNameA(buf, ctypes.byref(size))
        return buf.value.decode('latin-1')
    except Exception:
        return getpass.getuser()


def keygen(name, username=None):
    """Generate the serial for the given name.
    username defaults to the current Windows/OS username (GetUserNameA).
    Name must be at least 8 characters long."""
    if len(name) < 8:
        raise ValueError('Name must be at least 8 characters (>7)')

    if username is None:
        username = _get_system_username()

    serial = []
    j = 0  # index into username

    for i, ch in enumerate(name):
        idx_name = TABLE.find(ch)  # -1 if not found

        if idx_name == -1:
            # Character not in table: pass through unchanged
            serial.append(ch)
        else:
            # Get current username character (wrap around if exhausted)
            if j >= len(username):
                j = 0
            user_ch = username[j]
            j += 1

            idx_user = TABLE.find(user_ch)
            # ASSUMPTION: If the username character is not in TABLE,
            # treat its index as -1 (i.e., 0 after +1 offset used in Delphi).
            # The C++ keygen uses Find() which returns -1 for not-found;
            # the subtraction then uses that value directly.
            # We mirror the C++ logic exactly:
            # if iTemp1 < iTemp2: iTemp1 += 0x47 (71)
            # iTemp3 = iTemp1 - iTemp2
            p = idx_name
            unp = idx_user  # may be -1 if not in table

            if p < unp:
                p += TABLE_LEN  # 71 = 0x47

            idx_result = p - unp
            serial.append(TABLE[idx_result])

    return ''.join(serial)


def verify(name, serial, username=None):
    """Verify that serial matches what keygen(name) would produce."""
    if len(name) < 8:
        return False
    try:
        expected = keygen(name, username=username)
    except Exception:
        return False
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
