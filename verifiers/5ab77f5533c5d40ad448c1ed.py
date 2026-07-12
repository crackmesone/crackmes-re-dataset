import datetime
import platform

# ASSUMPTION: The platform ID (ID constant) depends on the OS.
# On Windows: 0=Win32s->0x228C, 1=Win9x->0x26CD, 2=WinNT->0x1E4B
# On non-Windows (Linux/Mac), we cannot call GetVersionEx.
# We default to platform ID 2 (WinNT/modern Windows) -> 0x1E4B
# ASSUMPTION: The second keygen (ASM) differs slightly from the C keygen.
# The C keygen is more clearly readable, so we implement it.
# The C keygen iterates i from 1 to m-1 (skipping index 0).
# Variables are unsigned ints (we simulate with & 0xFFFFFFFF masking).

def get_platform_id():
    # ASSUMPTION: Assume modern Windows NT platform (ID=2 -> 0x1E4B)
    # Adjust if running on different platform.
    return 0x1E4B

def keygen(name, year=None, month=None, platform_id=None):
    """
    Generate serial for given name.
    year, month: current year and month (UTC). If None, uses current system time.
    platform_id: 0=Win32s, 1=Win9x, 2=WinNT. If None, defaults to 2.
    """
    if year is None or month is None:
        now = datetime.datetime.utcnow()
        year = now.year
        month = now.month

    if platform_id is None:
        platform_id = get_platform_id()

    ID_map = {0: 0x228C, 1: 0x26CD, 2: 0x1E4B}
    ID = ID_map.get(platform_id, 0x00)

    # Name must be at least 4 characters
    m = len(name)
    if m < 4:
        return None

    MASK = 0xFFFFFFFF

    # PARTE_3: k2 = sum of (nome[i] * ID * m) for i in range(1, m)
    k2 = 0
    for i in range(1, m):
        k1 = (ord(name[i]) * ID * m) & MASK
        k2 = (k2 + k1) & MASK

    # PARTE_4:
    k3 = (k2 ^ year) & MASK
    k5 = 0
    for i in range(1, m):
        k4 = (ord(name[i]) ^ k3) & MASK
        k5 = (k5 + k4) & MASK
    k5 = (k5 + k3) & MASK

    # PARTE_5:
    k6 = (k5 ^ month) & MASK
    k8 = 0
    for i in range(1, m):
        k7 = (ord(name[i]) * k6) & MASK
        k8 = (k8 + k7) & MASK

    serial = f"{k2}-{k5}-{k8}"
    return serial

def verify(name, serial, year=None, month=None, platform_id=None):
    """
    Verify that the serial matches the name.
    NOTE: The serial is time-dependent (year/month at generation time).
    If year/month not given, uses current UTC time.
    """
    expected = keygen(name, year=year, month=month, platform_id=platform_id)
    return expected is not None and serial == expected


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
