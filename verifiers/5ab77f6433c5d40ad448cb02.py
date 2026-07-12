import hashlib
import struct

# Based on the writeup for 'NoMessageBoxAlarm' by losespeed
# The crackme generates a UserID from the current time at startup.
# The serial validation checks the UserID against a derived serial.
#
# From the writeup:
# 1. UserID is generated from current time:
#    - Format time as "%H%M%S" -> e.g. "233504"
#    - Compute sum = hour + minute + second
#    - Concatenate: "Please Crack Me :)" + time_string -> e.g. "Please Crack Me :)233504"
#    - Pass that concatenated string + sum into sub_401600
#    - sub_401600 returns a value formatted as '%u' (unsigned decimal) -> UserID
#
# 2. sub_401600 is NOT fully described in the writeup. The writeup shows it
#    formats the concatenated string as '%ld', but the actual hash/transform
#    applied to produce the final numeric UserID is truncated.
#
# ASSUMPTION: sub_401600 computes a simple checksum or hash of the
# concatenated string. A common pattern in crackmes of this era is to
# sum all character values (possibly multiplied by position) and return
# the result as an unsigned 32-bit integer. We implement a few candidates
# and mark them clearly.
#
# ASSUMPTION: The serial validation likely checks that serial == f(userid)
# for some simple arithmetic function. Since the writeup is truncated before
# revealing the serial check, we cannot fully reconstruct verify().

def _sub_401600_assumption(concatenated: str, hms_sum: int) -> int:
    """
    ASSUMPTION: sub_401600 computes a hash of the concatenated string.
    The writeup shows the string is formatted as '%ld' but the actual
    computation is not fully described. We use a simple byte-sum variant
    common in old crackmes as a placeholder.
    """
    # ASSUMPTION: simple sum of ord(c) * (i+1) mod 2^32
    result = 0
    for i, c in enumerate(concatenated):
        result = (result + ord(c) * (i + 1)) & 0xFFFFFFFF
    return result


def generate_userid(hour: int, minute: int, second: int) -> int:
    """
    Reconstruct how the UserID is generated from the current time.
    This matches the disassembly described in the writeup.
    """
    time_string = "%02d%02d%02d" % (hour, minute, second)  # Format: %H%M%S
    hms_sum = hour + minute + second
    base_str = "Please Crack Me :)"
    concatenated = base_str + time_string
    userid = _sub_401600_assumption(concatenated, hms_sum)
    return userid


def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: 'name' field is actually the UserID shown in the crackme.
    The writeup does not fully describe the serial check (it is truncated).
    We implement a placeholder that checks serial == str(userid * some_constant)
    but mark it as an assumption.
    """
    try:
        userid = int(name)
        serial_int = int(serial)
    except ValueError:
        return False

    # ASSUMPTION: The serial is derived from the UserID via a simple
    # arithmetic transformation. The writeup does not reveal this.
    # Common pattern: serial = userid XOR some_constant, or serial = userid * k
    # Without the full writeup, we cannot determine the real check.
    # ASSUMPTION: serial == userid (trivial check as placeholder)
    # This is almost certainly WRONG - replace when full algorithm is known.
    # ASSUMPTION:
    expected = userid  # placeholder - real formula unknown
    return serial_int == expected


def keygen(name: str) -> str:
    """
    Generate a serial for the given UserID (passed as 'name').
    ASSUMPTION: Same placeholder as verify().
    """
    try:
        userid = int(name)
    except ValueError:
        return ""
    # ASSUMPTION: placeholder - real derivation unknown from truncated writeup
    serial = userid
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
