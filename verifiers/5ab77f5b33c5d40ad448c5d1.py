import ctypes
import os

# Serial table from the writeup
serialTable = [
    0x13, 0x16, 0x99, 0x11, 0x63, 0x15, 0x54, 0x52, 0x88, 0x01,
    0x31, 0x56, 0x68, 0x55, 0x37, 0x41, 0x74, 0x46, 0x75, 0x57,
    0x76, 0x6C, 0x77, 0x6A, 0x78, 0x44, 0x79, 0x58, 0x48, 0x59,
    0x6F, 0x5A, 0x77, 0x73, 0x64, 0x52
]


def get_windows_username():
    """Try to get the Windows username; fall back to os.getlogin() on non-Windows."""
    try:
        import ctypes
        buf = ctypes.create_string_buffer(257)
        size = ctypes.c_ulong(257)
        ctypes.windll.advapi32.GetUserNameA(buf, ctypes.byref(size))
        return buf.value.decode('latin-1')
    except Exception:
        # ASSUMPTION: On non-Windows systems we use os.getlogin() or a fallback
        try:
            return os.getlogin()
        except Exception:
            return os.environ.get('USERNAME', os.environ.get('USER', ''))


def compute_members(name: str, username: str):
    """
    Replicates the generateSerial logic from the writeup.
    Returns (member0, member1, member2, member3)
    """
    member0 = 0
    member1 = 0
    member2 = 0
    member3 = 0

    # Name must be <= 9 characters
    if len(name) > 9 or len(username) == 0:
        return None

    # First loop: iterate over name characters
    if len(name) != 0:
        for i in range(len(name)):
            member0 += ord(name[i]) * serialTable[i]
            member1 = ord(username[1]) * serialTable[i] + member1
            member2 = member1 - serialTable[i]

    # Second loop: iterate over username characters
    if len(username) != 0:
        for i in range(len(username)):
            member1 += serialTable[i]
            member0 += ord(username[i]) * serialTable[i]
            member3 = member0 - member1

    return member0, member1, member2, member3


def generate_serial(name: str, username: str) -> str:
    """
    Generates the serial string using wsprintfA format: "%X-%X-%X-%X-%X-%X"
    Fields: username[0], 0x99, member2, 0x52, member3, username[2]
    """
    if len(name) > 9:
        return None
    if len(username) == 0:
        return None

    result = compute_members(name, username)
    if result is None:
        return None

    member0, member1, member2, member3 = result

    # Format matches wsprintfA("%X-%X-%X-%X-%X-%X", username[0], 0x99, member2, 0x52, member3, username[2])
    # Note: %X with negative numbers - C's wsprintfA treats these as unsigned 32-bit
    def to_unsigned32(v):
        return v & 0xFFFFFFFF

    serial = "{:X}-{:X}-{:X}-{:X}-{:X}-{:X}".format(
        ord(username[0]),
        0x99,
        to_unsigned32(member2),
        0x52,
        to_unsigned32(member3),
        ord(username[2])
    )
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verifies whether (name, serial) is a valid pair for the current system username.
    ASSUMPTION: The crackme checks the serial against the one computed for the
    system username obtained via GetUserNameA. We replicate that here.
    """
    username = get_windows_username()
    expected = generate_serial(name, username)
    if expected is None:
        return False
    # ASSUMPTION: comparison is case-insensitive or exact; wsprintfA %X is uppercase
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name on the current system.
    Returns None if the name is invalid (> 9 chars or empty username).
    """
    username = get_windows_username()
    return generate_serial(name, username)



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
