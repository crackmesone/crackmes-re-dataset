import os
import ctypes

# ASSUMPTION: The serial algorithm is reconstructed from the C keygen source code.
# The keygen uses system-specific values (free disk space, total physical memory),
# making it impossible to produce a deterministic serial from name alone.
# The 'company' field is derived from name length parity.
# The serial is: dwFreeSpace_str + reversed(dwFreeSpace_str) ... wait, let me re-read carefully.

# From CalculateSerial():
# 1. Get free disk space (bytes / 1024 = KB) -> szTmp1 = str(dwFreeSpace)
# 2. szSerial = szTmp1                         (part 1)
# 3. ReverseString(szName) -> stores reversed name in szTmp1 global... but wait:
#    ReverseString stores result in global szTmp1, NOT in szName.
#    So after ReverseString(szName), szTmp1 = reversed(szName)
# 4. lstrcat(szSerial, szTmp1) -> serial += reversed(szName)   (part 2)
# 5. szComp = "PERSONAL" if len(szName) even else "HOME"
# 6. ReverseString(szComp) -> szTmp1 = reversed(szComp)
# 7. lstrcat(szSerial, szTmp1) -> serial += reversed(szComp)  (part 3)
# 8. dwFreeMem = total physical RAM >> 10 (in KB)
# 9. szTmp1 = str(dwFreeMem)
# 10. lstrcat(szSerial, szTmp1) -> serial += str(dwFreeMem)   (part 4)
#
# Additionally, SetButtons() manipulates CAPS LOCK (on), SCROLL LOCK (on), NUM LOCK (off)
# before entering data - this is a wacky trick in the crackme validation.
# ASSUMPTION: The crackme validation likely checks keyboard state or uses it as part of check.
# The actual crackme validation is in btnRegisterClick (Delphi), not fully shown here.

def get_free_disk_space_kb():
    """Get free disk space on current drive in KB."""
    # ASSUMPTION: Works on Linux/Mac using os.statvfs; on Windows use shutil
    import shutil
    total, used, free = shutil.disk_usage("/")
    return free // 1024

def get_total_ram_kb():
    """Get total physical RAM in KB."""
    import platform
    if platform.system() == 'Windows':
        class MEMORYSTATUS(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('dwTotalPhys', ctypes.c_ulong),
                ('dwAvailPhys', ctypes.c_ulong),
                ('dwTotalPageFile', ctypes.c_ulong),
                ('dwAvailPageFile', ctypes.c_ulong),
                ('dwTotalVirtual', ctypes.c_ulong),
                ('dwAvailVirtual', ctypes.c_ulong),
            ]
        ms = MEMORYSTATUS()
        ms.dwLength = ctypes.sizeof(MEMORYSTATUS)
        ctypes.windll.kernel32.GlobalMemoryStatus(ctypes.byref(ms))
        return ms.dwTotalPhys >> 10
    else:
        # ASSUMPTION: On non-Windows, read from /proc/meminfo
        try:
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        return int(line.split()[1])  # already in KB
        except Exception:
            pass
        # Fallback
        import shutil
        return 0

def reverse_string(s):
    return s[::-1]

def calculate_serial(name):
    name = name[:15]  # max 15 chars (EM_LIMITTEXT 15)
    
    free_space_kb = get_free_disk_space_kb()
    free_mem_kb = get_total_ram_kb()
    
    part1 = str(free_space_kb)
    part2 = reverse_string(name)
    
    if len(name) % 2 == 0:
        comp = "PERSONAL"
    else:
        comp = "HOME"
    
    part3 = reverse_string(comp)
    part4 = str(free_mem_kb)
    
    serial = part1 + part2 + part3 + part4
    company = comp
    return serial, company

def keygen(name):
    serial, company = calculate_serial(name)
    return serial

def verify(name, serial):
    # ASSUMPTION: The actual crackme validation logic (btnRegisterClick in Delphi)
    # is not fully disclosed in the writeup. We reconstruct based on the keygen.
    # The verify function checks if the provided serial matches the generated one.
    # NOTE: This will only match if called on the same machine with same disk/RAM state.
    expected_serial, _ = calculate_serial(name)
    return serial == expected_serial


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
