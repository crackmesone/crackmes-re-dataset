import hashlib
import base64
import struct
import ctypes

# Standard Base64 encoding (uses the standard alphabet)
def b64encode_str(s: str) -> str:
    return base64.b64encode(s.encode('latin-1')).decode('ascii')

# The UserID (third edit box) is computed from the Windows version.
# It is: str(winver_hex) + b64(str(winver_hex)) concatenated, then b64 encoded.
# Since we can't call GetVersion() in Python, we accept it as a parameter or compute a default.
# ASSUMPTION: For keygen purposes, we need the UserID from the running machine.
# The crackme does:
#   winver = GetVersion()
#   winver_multiplied = winver * 8  (MUL EBX where EBX=8)
#   ver_str = sprintf("%X", winver_multiplied)   <- hex string of (winver*8)
#   e_ver = base64(ver_str)  (only first 8 bytes / chars of ver_str)
#   concat = ver_str + e_ver
#   userid = base64(concat)  (only first 0x10=16 bytes of concat)
# ASSUMPTION: The Base64 call takes (src_ptr, length, dst_ptr) where length is the number of bytes to encode.
# From the writeup: Base64(ver_str[0:8]) then Base64(concat[0:16])

def compute_userid(windows_version_raw: int) -> str:
    """Compute the UserID string the way the crackme does.
    windows_version_raw: the raw DWORD from GetVersion()
    """
    # MUL EBX where EBX=8: EAX = winver * 8 (lower 32 bits)
    val = (windows_version_raw * 8) & 0xFFFFFFFF
    # sprintf("%X", val)
    ver_str = "%X" % val  # uppercase hex
    # Base64 encode first 8 bytes of ver_str
    src8 = ver_str[:8].encode('latin-1')
    src8 = src8.ljust(8, b'\x00')[:8]  # pad/truncate to 8 bytes
    e_ver = base64.b64encode(src8).decode('ascii')
    # concat = ver_str + e_ver
    concat = ver_str + e_ver
    # Base64 encode first 16 bytes of concat
    src16 = concat[:16].encode('latin-1')
    src16 = src16.ljust(16, b'\x00')[:16]
    userid = base64.b64encode(src16).decode('ascii')
    return userid

def generate_serial(name: str, userid: str) -> str:
    """Core serial generation algorithm:
    1. Base64-encode the name
    2. Concatenate with userid
    3. MD5 the result
    4. Sum the four 32-bit little-endian words of the MD5 digest
    5. Format as uppercase hex string
    6. Replace character at index 4 (5th char, 0-indexed) with '-'
    """
    # Step 1: Base64 encode name
    # ASSUMPTION: standard base64, full name string
    e_name = base64.b64encode(name.encode('latin-1')).decode('ascii')
    # Step 2: Concatenate
    combined = e_name + userid
    # Step 3: MD5
    md5_hash = hashlib.md5(combined.encode('latin-1')).digest()
    # Step 4: Sum four 32-bit little-endian words
    w0, w1, w2, w3 = struct.unpack('<IIII', md5_hash)
    total = (w0 + w1 + w2 + w3) & 0xFFFFFFFF
    # Step 5: Format as uppercase hex (with %X, no leading zeros unless needed)
    s = "%X" % total
    # Step 6: Replace index 4 (position 5, the 5th character) with '-'
    # The crackme puts '-' at DS:[40333C] which is 4 bytes after the start of the serial string
    # i.e., serial[4] = '-'
    s_list = list(s)
    if len(s_list) >= 5:
        s_list[4] = '-'
    else:
        # pad to at least 8 chars first (wsprintfA %X may produce up to 8 hex digits)
        s_padded = s.zfill(8)
        s_list = list(s_padded)
        s_list[4] = '-'
    return ''.join(s_list)

def verify(name: str, serial: str) -> bool:
    """Verify a serial for a given name.
    ASSUMPTION: We use the current machine's Windows version for userid.
    On non-Windows or for testing, we attempt ctypes.windll; fall back to a known value.
    """
    try:
        ver = ctypes.windll.kernel32.GetVersion()
    except Exception:
        # ASSUMPTION: fallback for non-Windows testing
        ver = 0x00000005  # placeholder
    userid = compute_userid(ver)
    expected = generate_serial(name, userid)
    return serial == expected

def keygen(name: str) -> str:
    """Generate a valid serial for the given name on the current machine."""
    try:
        ver = ctypes.windll.kernel32.GetVersion()
    except Exception:
        # ASSUMPTION: fallback for non-Windows testing; real keygen needs actual Windows version
        ver = 0x00000005
    userid = compute_userid(ver)
    return generate_serial(name, userid)


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
