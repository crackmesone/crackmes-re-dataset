import math
import ctypes
import sys

def get_c_drive_serial():
    """Get the volume serial number of C:\ using ctypes (Windows only)."""
    try:
        serial = ctypes.c_ulong(0)
        result = ctypes.windll.kernel32.GetVolumeInformationA(
            b"C:\\",
            None, 0,
            ctypes.byref(serial),
            None, None, None, 0
        )
        if result:
            s = serial.value
            # If serial is negative as a signed long, take absolute value
            s_signed = ctypes.c_long(s).value
            if s_signed < 0:
                s = -s_signed
            return s
        return None
    except Exception:
        return None


def compute_serial(name, hdd_serial):
    """
    Serial generation algorithm (from solution writeups):
    1. First part: length of name + "- "
    2. Second part:
       temp = hdd_serial / len(name)
       temp = sqrt(temp)
       temp = round(temp)  # using round-half-away-from-zero via floor(abs+0.5)*sign
       temp = temp - len(name)
    Serial = str(len(name)) + "- " + str(int(temp))
    
    Note: The VB keygen code shows:
      temp = Ret / Len(strText)
      temp = Sqr(temp) - Len(strText)
      temp = Sgn(temp) * Int(Abs(temp) + 0.5)
    
    But the ASM from kao's solution shows the subtraction happens AFTER rounding.
    The VB keygen applies Sgn*Int(Abs+0.5) to (Sqr(Ret/Len) - Len),
    while kao's ASM does: sqrt -> round -> subtract len.
    We follow kao's ASM as it is more authoritative.
    """
    name_len = len(name)
    if name_len == 0:
        return None
    
    # Step 1: divide hdd_serial by name length
    temp = hdd_serial / name_len
    
    # Step 2: take square root
    temp = math.sqrt(temp)
    
    # Step 3: add 0.5 and floor (round half up, i.e., round-half-away-from-zero for positive)
    # From kao's ASM: fadd 0.5, frndint (which rounds to nearest even in x87),
    # but the +0.5 trick effectively does floor(x + 0.5) = round half up
    temp = math.floor(temp + 0.5)
    
    # Step 4: subtract name length
    temp = temp - name_len
    
    serial_part2 = int(temp)
    
    # Format: "<namelen>- <part2>"
    # From SmartCheck output: "7- 12117" and "3- 17090" and "7- 16650"
    # The format is: str(name_len) + "- " + str(serial_part2)
    serial = str(name_len) + "- " + str(serial_part2)
    return serial


def verify(name, serial, hdd_serial=None):
    """
    Verify name/serial pair.
    hdd_serial: if None, attempts to read from C:\ (Windows only).
    """
    if hdd_serial is None:
        hdd_serial = get_c_drive_serial()
    if hdd_serial is None:
        raise RuntimeError("Could not get C:\\ volume serial number")
    
    expected = compute_serial(name, hdd_serial)
    if expected is None:
        return False
    
    # Comparison is case-sensitive string compare (VBA StrComp mode 1 = text, but
    # since the serial is numeric it doesn't matter)
    return serial == expected


def keygen(name, hdd_serial=None):
    """
    Generate valid serial for given name.
    hdd_serial: if None, attempts to read from C:\ (Windows only).
    """
    if hdd_serial is None:
        hdd_serial = get_c_drive_serial()
    if hdd_serial is None:
        raise RuntimeError("Could not get C:\\ volume serial number")
    
    return compute_serial(name, hdd_serial)



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
