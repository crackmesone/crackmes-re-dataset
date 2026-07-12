import os
import datetime
import socket

def _build_serial(machine_name=None, username=None, now=None):
    """
    Serial format: MACHINENAME-YEARHOUR-USERNAME
    where MACHINENAME is the NetBIOS/hostname (uppercase),
    YEAR is the 4-digit year, HOUR is the current hour (0-23, no zero-padding),
    USERNAME is the current user name in uppercase.
    """
    if machine_name is None:
        machine_name = socket.gethostname().upper()
    else:
        machine_name = machine_name.upper()

    if username is None:
        username = os.getlogin().upper()
    else:
        username = username.upper()

    if now is None:
        now = datetime.datetime.now()

    year = str(now.year)   # e.g. '2024'
    hour = str(now.hour)   # e.g. '3' (no zero-padding, matches C# int.ToString())

    serial = machine_name + "-" + year + hour + "-" + username
    return serial


def verify(name, serial):
    """
    The crackme does not use 'name' in the serial construction.
    It compares the entered serial against:
        MachineName + "-" + Year + Hour + "-" + UserName.ToUpper()
    ASSUMPTION: machine_name and username are taken from the current environment.
    ASSUMPTION: Hour is not zero-padded (matches C# default int.ToString()).
    """
    expected = _build_serial()
    return serial == expected


def keygen(name, machine_name=None, username=None, now=None):
    """
    Generate the valid serial for the current machine/user/time.
    'name' is unused by the algorithm; kept for interface consistency.
    ASSUMPTION: machine_name defaults to socket.gethostname().upper(),
                username defaults to os.getlogin().upper(),
                now defaults to datetime.datetime.now().
    Provide explicit values to generate serials for other environments.
    """
    return _build_serial(machine_name=machine_name, username=username, now=now)



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
