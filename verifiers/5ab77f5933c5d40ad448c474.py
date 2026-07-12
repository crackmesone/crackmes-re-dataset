import ctypes
import struct

# Helper: integer division matching compiler's signed divide-by-10 trick
def signed_div10(val):
    # The compiler trick: IMUL 0x66666667, SAR EDX 2, subtract sign bit
    # This is equivalent to integer division by 10 for 32-bit signed integers
    val = ctypes.c_int32(val).value
    result = val // 10
    return ctypes.c_int32(result).value

def screen_width():
    # ASSUMPTION: GetSystemMetrics(0) = screen width; typical 1920 but unknown at keygen time
    # We'll parameterize this
    try:
        import ctypes as ct
        user32 = ct.windll.user32
        return user32.GetSystemMetrics(0)
    except Exception:
        return 1920  # ASSUMPTION: default fallback

def screen_height():
    # ASSUMPTION: GetSystemMetrics(1) = screen height
    try:
        import ctypes as ct
        user32 = ct.windll.user32
        return user32.GetSystemMetrics(1)
    except Exception:
        return 1080  # ASSUMPTION: default fallback

def get_windows_version():
    # ASSUMPTION: GetVersion() returns a DWORD; typical Win7 = 0x00000006 (low byte=major)
    # GetVersion returns low word = version, low byte = major, next byte = minor
    try:
        import ctypes as ct
        k32 = ct.windll.kernel32
        return k32.GetVersion()
    except Exception:
        return 0x00000006  # ASSUMPTION: fallback

def compute_ebp5c(first_char_ord, width, height):
    """
    Compute EBP-5C:
    1. Multiply width * height
    2. XOR with first char of name
    3. Keep dividing by 10 while value > 0xF423F
    4. Must be in range (0x1869F, 0xF423F] and != 0
    """
    product = ctypes.c_int32(width * height).value
    val = ctypes.c_int32(first_char_ord ^ product).value

    # Adjust: keep dividing by 10 while > 0xF423F
    while ctypes.c_int32(val).value > 0xF423F:
        val = signed_div10(val)
        val = ctypes.c_int32(val).value

    return val

def compute_ebp60(win_version, name_len, first_char_ord):
    """
    Compute EBP-60:
    win_version * name_len + first_char_ord
    Then similar range checks as EBP-5C (ASSUMPTION based on description)
    """
    win_version = ctypes.c_int32(win_version).value
    product = ctypes.c_int32(win_version * name_len).value
    val = ctypes.c_int32(product + first_char_ord).value
    return val

def compute_serial_parts(name, width=None, height=None, win_version=None):
    """
    Compute the three serial box values.
    """
    if width is None:
        width = screen_width()
    if height is None:
        height = screen_height()
    if win_version is None:
        win_version = get_windows_version()

    if not name:
        return None

    first_char = ord(name[0]) & 0xFF
    name_len = len(name)
    if name_len > 25:
        name = name[:25]
        name_len = 25

    # --- Compute EBP-5C ---
    ebp5c = compute_ebp5c(first_char, width, height)

    # Must be != 0, > 0x1869F, <= 0xF423F
    if ebp5c == 0 or ebp5c <= 0x1869F or ebp5c > 0xF423F:
        # ASSUMPTION: if out of range, algorithm fails
        return None

    # --- Compute EBP-60 ---
    ebp60_raw = compute_ebp60(win_version, name_len, first_char)

    # ASSUMPTION: same range normalization applied (writeup says "put EBP-5C in EBP-60" after checks)
    # The description says EBP-60 goes through similar checks then gets replaced by EBP-5C
    # Near end: EAX = (EBP-5C + EBP-60) * name_len, stored back to EBP-60
    ebp60 = ctypes.c_int32((ebp5c + ebp60_raw) * name_len).value

    # --- Compute EBP-64 ---
    ebp64 = ctypes.c_int32(ebp60 ^ ebp5c).value

    return ebp5c, ebp60, ebp64

def verify(name, serial):
    """
    Verify name/serial combo.
    Serial format: 'XXXXX-XXXXX-XXXXX-XXXX' or similar 3+1 box format.
    ASSUMPTION: serial is 'part1-part2-part3-part4' where part4 can be anything (4 chars).
    Parts 1-3 are decimal representations of the computed values.
    """
    parts = serial.split('-')
    if len(parts) != 4:
        return False

    # Part 4 must be exactly 4 chars
    if len(parts[3]) != 4:
        return False

    try:
        s1 = int(parts[0])
        s2 = int(parts[1])
        s3 = int(parts[2])
    except ValueError:
        return False

    result = compute_serial_parts(name)
    if result is None:
        return False

    ebp5c, ebp60, ebp64 = result

    return s1 == ebp5c and s2 == ebp60 and s3 == ebp64

def keygen(name, width=None, height=None, win_version=None):
    """
    Generate a serial for the given name.
    ASSUMPTION: Part 4 can be any 4 characters; we use '1234'.
    ASSUMPTION: width, height, win_version must match target machine values.
    """
    if width is None:
        width = screen_width()
    if height is None:
        height = screen_height()
    if win_version is None:
        win_version = get_windows_version()

    result = compute_serial_parts(name, width, height, win_version)
    if result is None:
        return None

    ebp5c, ebp60, ebp64 = result
    # ASSUMPTION: serial format is three numeric parts + any 4-char string
    serial = '{}-{}-{}-{}'.format(ebp5c, ebp60, ebp64, '1234')
    return serial


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
