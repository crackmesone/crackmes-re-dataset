# Reverse-engineered serial validation for TiGa's Vista Sidebar Gadget Crackme
# Based on the JavaScript logic described in the writeup.
#
# The serial (envPath) is computed as:
#   envPath = cpu_count + (recycle_bin_size_used + 1) + variableSerial2 * (recycle_bin_file_count + 10)
#
# where variableSerial2 = standardDisplayName.length * (displayName.length + DSTDisplayName.length) * name.length * name.length
#
# Several values are machine/environment-specific:
#   - cpu_count                : number of CPUs (System.Machine.CPUs.count)
#   - recycle_bin_size_used    : bytes used in Recycle Bin (System.Shell.RecycleBin.sizeUsed)
#   - recycle_bin_file_count   : number of files in Recycle Bin (System.Shell.RecycleBin.fileCount)
#   - standardDisplayName      : e.g. "GMT Standard Time" (System.Time.currentTimeZone.standardDisplayName)
#   - displayName              : e.g. "(UTC+00:00) Dublin, Edinburgh, Lisbon, London" (System.Time.currentTimeZone.displayName)
#   - DSTDisplayName           : e.g. "GMT Daylight Time" (System.Time.currentTimeZone.DSTDisplayName)
#
# ASSUMPTION: varHappyApiHappy == "BackDoor" (mentioned in writeup as the backdoor username)
# ASSUMPTION: The serial is an integer (JavaScript number), compared with == (loose equality possible)
# ASSUMPTION: Empty name or empty serial causes failure (truthy check in JS)

def compute_serial2(name, std_display_name, display_name, dst_display_name):
    """
    Compute variableSerial2 as done in settings.html.
    variableSerial2 = len(standardDisplayName) * (len(displayName) + len(DSTDisplayName)) * len(name) * len(name)
    """
    varMint = len(std_display_name)
    varvarvar = len(display_name) + len(dst_display_name)
    variable_serial2 = varMint * varvarvar * len(name)
    variable_serial2 *= len(name)
    return variable_serial2


def compute_envpath(name, cpu_count, recycle_bin_size_used, recycle_bin_file_count,
                   std_display_name, display_name, dst_display_name):
    """
    Compute the expected serial (envPath) as done in crackme.html.
    envPath = cpu_count + (recycle_bin_size_used + 1) + variableSerial2 * (recycle_bin_file_count + 10)
    """
    variable_serial2 = compute_serial2(name, std_display_name, display_name, dst_display_name)
    env_path = cpu_count + (recycle_bin_size_used + 1) + variable_serial2 * (recycle_bin_file_count + 10)
    return env_path


# ASSUMPTION: varHappyApiHappy = "BackDoor"
BACKDOOR_NAME = "BackDoor"


def verify(name, serial,
           cpu_count=1,
           recycle_bin_size_used=0,
           recycle_bin_file_count=0,
           std_display_name="GMT Standard Time",
           display_name="(UTC+00:00) Dublin, Edinburgh, Lisbon, London",
           dst_display_name="GMT Daylight Time"):
    """
    Returns True if the serial is valid for the given name on the given machine.

    Parameters that are machine-specific must be provided by the caller:
      cpu_count              - number of CPUs
      recycle_bin_size_used  - bytes used in Recycle Bin
      recycle_bin_file_count - number of files in Recycle Bin
      std_display_name       - time zone standard display name
      display_name           - time zone display name
      dst_display_name       - time zone DST display name

    ASSUMPTION: The serial comparison is numeric (int == int).
    ASSUMPTION: name must not be empty, serial must not be falsy (0 or empty string), name must not be 'BackDoor'.
    """
    if not name:
        return False
    if not serial:
        return False
    if name == BACKDOOR_NAME:
        return False  # ASSUMPTION: backdoor check excluded per writeup

    env_path = compute_envpath(
        name, cpu_count, recycle_bin_size_used, recycle_bin_file_count,
        std_display_name, display_name, dst_display_name
    )

    try:
        return int(serial) == env_path
    except (ValueError, TypeError):
        return str(serial) == str(env_path)


def keygen(name,
           cpu_count=1,
           recycle_bin_size_used=0,
           recycle_bin_file_count=0,
           std_display_name="GMT Standard Time",
           display_name="(UTC+00:00) Dublin, Edinburgh, Lisbon, London",
           dst_display_name="GMT Daylight Time"):
    """
    Generate a valid serial for the given name and machine configuration.
    ASSUMPTION: The machine-specific values must be provided to generate a working serial.
    """
    if not name or name == BACKDOOR_NAME:
        raise ValueError("Name must not be empty or 'BackDoor'")

    env_path = compute_envpath(
        name, cpu_count, recycle_bin_size_used, recycle_bin_file_count,
        std_display_name, display_name, dst_display_name
    )
    return str(env_path)

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
