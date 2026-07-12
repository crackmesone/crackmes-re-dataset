import ctypes
import os

def _calc_serial1(name: str) -> int:
    """Check 1 serial: matches calcular_code_1 / keygen source s2 loop."""
    s2 = ctypes.c_uint32(0)
    length = len(name)
    # loop i from 0 to len(name) inclusive (lstrlen(szname)+1 iterations)
    for i in range(length + 1):
        ch = ord(name[i]) if i < length else 0  # null terminator
        s1 = ctypes.c_uint32(ch + 0x1CB1).value
        s1 = ctypes.c_uint32(s1 << 9).value
        s2 = ctypes.c_uint32(s2.value + s1 + (ch - 0x40)).value
    return s2.value

def _calc_serial2_3(name: str) -> int:
    """Check 2 part C: matches calcular_code_2_3 / keygen source s3 loop.
    Uses name[1] and name[4] (0-indexed), iterated len(name)+1 times.
    """
    s3 = ctypes.c_uint32(0)
    length = len(name)
    # ASSUMPTION: name must be at least 5 chars so name[4] is valid;
    # if shorter, treat missing chars as 0
    ch1 = ord(name[1]) if length > 1 else 0
    ch4 = ord(name[4]) if length > 4 else 0
    per_iter = ctypes.c_uint32(ch1 * 0x144 + ch4 * 5).value
    for k in range(length + 1):
        s3 = ctypes.c_uint32(s3.value + per_iter).value
    return s3.value

def _calc_serial2_2(username: str) -> int:
    """Check 2 part B: matches calcular_code_2_2 / keygen source s4 loop.
    Uses Windows username, iterated len(username)+1 times (including null).
    """
    s4 = ctypes.c_uint32(0)
    length = len(username)
    for l in range(length + 1):
        ch = ord(username[l]) if l < length else 0
        s4 = ctypes.c_uint32(s4.value + (ch * 7) + 0xF7C5).value
    return s4.value

def _get_windows_username() -> str:
    """Retrieve Windows username via ctypes, fallback to os.getlogin()."""
    try:
        import ctypes
        buf = ctypes.create_string_buffer(256)
        size = ctypes.c_ulong(256)
        ctypes.windll.advapi32.GetUserNameA(buf, ctypes.byref(size))
        return buf.value.decode('ascii', errors='replace')
    except Exception:
        # ASSUMPTION: on non-Windows, use os.getlogin() as fallback
        try:
            return os.getlogin()
        except Exception:
            return 'user'

def keygen(name: str):
    """Generate the two serials for the given name.
    Returns (serial1_str, serial2_str) where:
      serial1_str is the Check 1 serial (decimal integer as string)
      serial2_str is the Check 2 serial in format A-<username>-B-<snb>-C-<snc>
    """
    if len(name) < 4:
        raise ValueError('Name length must be > 3 (at least 4 characters)')
    username = _get_windows_username()
    s2 = _calc_serial1(name)
    snc = _calc_serial2_3(name)
    snb = _calc_serial2_2(username)
    serial1 = str(s2)
    serial2 = 'A-{}-B-{}-C-{}'.format(username, snb, snc)
    return serial1, serial2

def verify(name: str, serial: str) -> bool:
    """Verify a serial against a name.
    The serial can be either:
      - The Check1 serial (a decimal integer string), or
      - The Check2 serial in format A-<username>-B-<snb>-C-<snc>
    Returns True if it matches either check.
    """
    if len(name) < 4:
        return False
    s1_str, s2_str = keygen(name)
    serial = serial.strip()
    return serial == s1_str or serial == s2_str


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
