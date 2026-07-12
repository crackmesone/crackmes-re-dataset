import base64
import ctypes
import sys

# The crackme uses ElGamal-8bit verification.
# From the writeup/keygen:
#
# 1. Take the HDD volume serial number of the system drive, mask to 8 bits: M = vsnr & 0xFF
# 2. Compute s = (M - 0x68) % 0x82
# 3. The serial is base64("3B" + hex(s))  -- e.g. base64("3B65")
#
# The verification inside the crackme:
#   - Decodes base64 serial -> 4 chars
#   - Checks first two chars are "11" (or "3B" in hex? see note below)
#   - Reads the HDD volume serial, masks to 0xFF -> M
#   - Computes: checks (r^s * y^r) mod p == g^M mod p  (ElGamal)
#     simplified with k=1: r=g=0x3B, s = H(M) - 0x68 mod 0x82
#   - The serial string before base64 is "3B" + two-hex-digit s
#
# ASSUMPTION: The volume serial is obtained from the Windows system drive.
# For cross-platform use we accept it as a parameter.

def _compute_s(volume_serial_low_byte):
    """Compute s from the low byte of the volume serial number."""
    M = volume_serial_low_byte & 0xFF
    s = (M - 0x68) % 0x82
    return s

def keygen(volume_serial_low_byte):
    """Generate serial for a given low byte of the HDD volume serial number."""
    s = _compute_s(volume_serial_low_byte)
    plaintext = "3B" + format(s, '02x').upper()
    serial = base64.b64encode(plaintext.encode('ascii')).decode('ascii')
    return serial

def verify(volume_serial_low_byte, serial):
    """Verify a serial for a given low byte of the HDD volume serial number.
    
    The crackme:
    1. base64-decodes the serial -> must be exactly 4 chars
    2. Checks the decoded string starts with 'r' part (here r=0x3B -> '3B')
    3. Reads s from the remaining hex digits
    4. Verifies ElGamal: r^s * y^r == g^M mod p
       With k=1, g=0x3B, p=0x83, the check simplifies to s == (M - 0x68) mod 0x82
    """
    try:
        decoded = base64.b64decode(serial.encode('ascii')).decode('ascii')
    except Exception:
        return False
    
    # Must be exactly 4 characters
    if len(decoded) != 4:
        return False
    
    # First two chars should be '3B' (this is r in hex)
    # ASSUMPTION: The crackme checks the first part equals '3B' (or '11' decimal)
    r_part = decoded[:2]
    s_part = decoded[2:]
    
    if r_part.upper() != '3B':
        return False
    
    try:
        s_given = int(s_part, 16)
    except ValueError:
        return False
    
    # ElGamal verification simplified: s must equal (M - 0x68) mod 0x82
    M = volume_serial_low_byte & 0xFF
    s_expected = (M - 0x68) % 0x82
    
    return s_given == s_expected

def get_system_volume_serial():
    """Get the volume serial number of the system drive on Windows."""
    if sys.platform != 'win32':
        raise RuntimeError("Can only get volume serial on Windows")
    kernel32 = ctypes.windll.kernel32
    serial = ctypes.c_uint32(0)
    max_comp = ctypes.c_uint32(0)
    flags = ctypes.c_uint32(0)
    vol_name = ctypes.create_unicode_buffer(256)
    fs_name = ctypes.create_unicode_buffer(256)
    import os
    drive = os.environ.get('SystemRoot', 'C:\\')[:1] + ':\\'
    kernel32.GetVolumeInformationW(
        drive, vol_name, 256, ctypes.byref(serial),
        ctypes.byref(max_comp), ctypes.byref(flags),
        fs_name, 256
    )
    return serial.value


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
