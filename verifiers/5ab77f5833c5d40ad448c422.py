import math
import datetime
import os
import getpass

# ASSUMPTION: 'indk' is an instance variable initialized before Button1_Click is called.
# The writeup does not show its initialization value. Common default for VB integer fields is 0,
# but that would make misfit=0 and the whole chain collapse to 0.
# ASSUMPTION: indk is likely initialized to some non-zero value (e.g., 1) in Form_Load or as a field initializer.
# We assume indk=1 here since no other info is provided.
INDK_DEFAULT = 1

# ASSUMPTION: WindowsIdentity.GetCurrent.Name returns "DOMAIN\username" or just "username".
# In Python we approximate with getpass.getuser() which gives just the username.
# The length used is Strings.Len(Convert.ToString(WindowsIdentity.GetCurrent.Name))
# which counts the full string including domain prefix if present.

def _vb_oct(n):
    """VB Conversion.Oct returns octal string without '0o' prefix, uppercase (no letters in octal)."""
    # VB Oct() for integers returns octal digits as string
    if n == 0:
        return '0'
    negative = n < 0
    if negative:
        # VB treats negative integers as unsigned 32-bit for Oct
        n = n & 0xFFFFFFFF
    return oct(n)[2:].upper()

def _vb_hex(n):
    """VB Conversion.Hex returns uppercase hex string without '0x' prefix."""
    if n == 0:
        return '0'
    if n < 0:
        # VB Hex for negative treats as unsigned 32-bit
        n = n & 0xFFFFFFFF
    return hex(n)[2:].upper()

def _to_double(s):
    """DoubleType.FromString equivalent."""
    return float(s)

def _round_to_int(d):
    """CType(Math.Round(...), Integer) - VB uses banker's rounding."""
    # Python's round() uses banker's rounding too
    return int(round(d))

def keygen(username=None, indk=INDK_DEFAULT):
    """
    Generate serial and keyfile content for the current date and given username.
    username: the full Windows identity name (e.g. 'DOMAIN\\user' or just 'user')
              If None, uses getpass.getuser()
    indk: internal variable (ASSUMPTION: default 1)
    Returns (serial, keyfile_content)
    """
    if username is None:
        username = getpass.getuser()

    now = datetime.datetime.now()
    day = now.day
    month = now.month
    year = now.year

    # nofx = day * month * year
    nofx = day * month * year

    # misfit = str(Len(username) * indk * nofx)
    # Strings.Len returns length of the string representation
    username_len = len(str(username))
    misfit_int = username_len * indk * nofx
    misfit = str(misfit_int)

    # dk = Round((Float(misfit) * nofx) * Float(misfit))
    misfit_d = float(misfit)
    dk = _round_to_int((misfit_d * nofx) * misfit_d)

    # af = Round(((Float(misfit) * Float(misfit)) * nofx) * 4)
    af = _round_to_int(((misfit_d * misfit_d) * nofx) * 4)

    # misfit = Hex((((Float(misfit)^3) * nofx) - nofx))
    misfit_cubed_nofx = (misfit_d * misfit_d * misfit_d) * nofx - nofx
    misfit = _vb_hex(int(misfit_cubed_nofx))

    # dk = Round(Float(Oct(dk*dk)) * (dk*5))
    dk_sq = dk * dk
    oct_dk_sq = _vb_oct(dk_sq)
    # ASSUMPTION: DoubleType.FromString(Conversion.Oct(...)) parses the octal string as a decimal number
    # (VB's DoubleType.FromString treats the string as decimal, not octal)
    dk = _round_to_int(float(oct_dk_sq) * (dk * 5))

    # vandals = misfit & dk & af  (serial)
    vandals = str(misfit) + str(dk) + str(af)

    # snfu = af & dk & misfit  (keyfile content)
    snfu = str(af) + str(dk) + str(misfit)

    return vandals, snfu

def verify(name, serial):
    """
    Verify serial for a given username (name = full Windows identity name).
    Note: serial is date-dependent and username-dependent.
    ASSUMPTION: indk=1
    """
    vandals, snfu = keygen(username=name, indk=INDK_DEFAULT)
    return serial == vandals

def verify_with_keyfile(name, serial, keyfile_content):
    """Full verification: serial + keyfile content."""
    vandals, snfu = keygen(username=name, indk=INDK_DEFAULT)
    return serial == vandals and keyfile_content == snfu


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
            print(_sv)
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
