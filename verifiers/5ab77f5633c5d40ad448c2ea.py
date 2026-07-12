import ctypes
import os
import platform

# Helper: sum of ASCII values of a string
def char_sum(s):
    return sum(ord(c) for c in s)

# Helper: convert integer to modified string
# Each digit char: subtract 48 (ASCII '0'), add 65 (ASCII 'A')
def modified_string(n):
    digits = str(n)
    result = []
    for ch in digits:
        val = ord(ch) - 48 + 65
        result.append(chr(val))
    return ''.join(result)

# ASSUMPTION: age contribution: the write-up says "the age is the key (add it up)"
# example given: for 21 = 10+11. This likely means sum of digits of age.
# ASSUMPTION: The checkboxes number is added to the age sum somehow.
# Since we cannot determine the exact age/checkbox logic from the writeup,
# we model the serial construction from name+company+disk_serial.

def get_disk_serial():
    """Try to get volume serial number. Returns decimal string or fallback."""
    # ASSUMPTION: Uses GetVolumeInformationA on Windows for C:\\
    if platform.system() == 'Windows':
        try:
            import ctypes
            volumeName = ctypes.create_unicode_buffer(261)
            fsName = ctypes.create_unicode_buffer(261)
            serial = ctypes.c_uint32(0)
            maxComponentLen = ctypes.c_uint32(0)
            fsFlags = ctypes.c_uint32(0)
            result = ctypes.windll.kernel32.GetVolumeInformationW(
                'C:\\\\',
                volumeName, 261,
                ctypes.byref(serial),
                ctypes.byref(maxComponentLen),
                ctypes.byref(fsFlags),
                fsName, 261
            )
            if result:
                return str(serial.value)
        except Exception:
            pass
    # ASSUMPTION: fallback disk serial for non-Windows or failure
    return '0'

def build_serial(name, company, disk_serial_decimal=None):
    """
    Build the real serial based on reverse-engineered algorithm:
    1. sum_name = sum of ASCII values of name
    2. sum_company = sum of ASCII values of company
    3. total_sum = sum_name + sum_company
    4. modified = modified_string(total_sum)  -- each digit d -> chr(d + 65)
    5. serial = modified + 'AS' + disk_serial_decimal + 'CM5'

    ASSUMPTION: The exact separator or order is inferred from the writeup:
    '...first the sum of both name and company/group then the weird string
    that were made of the sum.. and the first hardcoded string "AS"
    after that is the decimal of DiskSerial and then the last hardcoded string "CM5"'
    """
    if disk_serial_decimal is None:
        disk_serial_decimal = get_disk_serial()

    sum_name = char_sum(name)
    sum_company = char_sum(company)
    total_sum = sum_name + sum_company
    mod_str = modified_string(total_sum)

    # ASSUMPTION: serial format is: modified_string + "AS" + disk_serial + "CM5"
    # The writeup lists: sum-derived string, "AS", disk serial decimal, "CM5"
    serial = mod_str + 'AS' + disk_serial_decimal + 'CM5'
    return serial

def verify(name, serial, company='', disk_serial_decimal=None):
    """Verify if serial matches the expected serial for name+company."""
    # ASSUMPTION: company defaults to empty string if not provided
    expected = build_serial(name, company, disk_serial_decimal)
    return serial == expected

def keygen(name, company='', disk_serial_decimal=None):
    """Generate a valid serial for the given name and company."""
    return build_serial(name, company, disk_serial_decimal)

# Example / demo

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
