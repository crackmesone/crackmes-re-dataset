import ctypes
import platform

# The crackme validation algorithm:
# 1. At a specific point in execution, esp is captured (call it start_esp)
# 2. serial_bin = start_esp >> 8  (upper bytes of esp, via fs:1 trick)
# 3. User enters a decimal string (digits only)
# 4. serial_bin += int(user_input)
# 5. esp is SET to serial_bin -- if this crashes the program, serial is wrong
# 6. Valid serial = start_esp - (start_esp >> 8)
#    so that serial_bin + serial = start_esp >> 8 + (start_esp - start_esp >> 8) = start_esp
#    Wait -- re-reading: serial_bin starts as start_esp >> 8, then += serial_int
#    We want the result = start_esp (original esp), so:
#    serial = start_esp - (start_esp >> 8)
#
# From the writeup:
#   start_esp on WinXP SP2 = 0x0012FF6C
#   serial_bin initial = 0x0012FF6C >> 8 = 0x12FF
#   Wait, but the solution says serial_bin = esp >> 8 which for 0x0012FF6C = 0x12FF
#   But then: serial = start_esp - (start_esp >> 8) = 0x12FF6C - 0x12FF = 0x12EC6D = 1240173
#
# ASSUMPTION: The algorithm is purely stack-address dependent, not name-dependent.
# ASSUMPTION: The keygen.DPR uses a correction factor for its own ESP vs crackme ESP:
#   add eax, ($12FF6C - $12FFB0)  which is -0x44 = -68
#   This means the keygen's esp at that point differs from crackme's esp by 0x44
#
# Since this crackme has NO name field (serial only), verify(name, serial) ignores name.
#
# Known valid serials by platform (from writeup):
#   WinXP SP2: 1240173
#   Win98:     6527462

KNOWN_ESP = {
    'winxp_sp2': 0x0012FF6C,
    'win98':     None,  # ASSUMPTION: win98 start_esp not given directly
}

def compute_serial(start_esp: int) -> int:
    """
    Given the start_esp value at the critical point in the crackme,
    compute the valid serial.
    Formula from writeup: serial = start_esp - (start_esp >> 8)
    """
    serial_bin_initial = start_esp >> 8
    serial = start_esp - serial_bin_initial
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for this crackme.
    - serial must be a string of only digits '0'-'9'
    - The numeric value must equal start_esp - (start_esp >> 8)
      for some plausible start_esp value.
    Since we can't know the exact ESP at runtime from Python,
    we check against known values from the writeup.
    ASSUMPTION: We check against the WinXP SP2 known good serial.
    """
    # Check digits only
    if not serial.isdigit():
        return False
    serial_int = int(serial)
    # Check against known WinXP SP2 value
    xp_serial = compute_serial(0x0012FF6C)
    if serial_int == xp_serial:
        return True
    # ASSUMPTION: Also accept win98 known value from writeup
    if serial_int == 6527462:
        return True
    # ASSUMPTION: Could also verify by checking the formula holds for any valid ESP range
    # Typical stack addresses on Windows are in range 0x00120000 - 0x0013FFFF
    # Try to find a start_esp that satisfies the formula
    # serial_int = start_esp - (start_esp >> 8)
    # start_esp ~= serial_int + serial_int//255  (approx)
    for candidate_esp in range(0x00100000, 0x00200000, 4):
        if compute_serial(candidate_esp) == serial_int:
            return True
    return False

def keygen(name: str) -> str:
    """
    Generate a valid serial.
    ASSUMPTION: Uses WinXP SP2 stack address (most common target).
    The real keygen uses runtime ESP detection.
    """
    # WinXP SP2 value from writeup
    start_esp = 0x0012FF6C
    serial = compute_serial(start_esp)
    return str(serial)


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
