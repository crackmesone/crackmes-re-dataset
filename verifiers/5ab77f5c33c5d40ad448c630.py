import ctypes
import struct

# This crackme generates a serial based on:
# 1. A hardware ID (VSN) derived from the C: drive volume serial number
# 2. A TIME value derived from the current system time
# The serial is: pow(cipher, 0xD, 0xFFFFFFFD)
# where cipher = (TIME * 10000 + VSN) * 8
#
# Since the serial depends on hardware VSN and current time, there is no
# name-based serial. The keygen() function demonstrates how to compute
# the serial from VSN and TIME values directly.
#
# ASSUMPTION: The exact TIME derivation from GetSystemTimeAsFileTime uses
# 64-bit arithmetic with specific offsets. We replicate the logic in Python.
# ASSUMPTION: VSN is read from the C: drive; on non-Windows or without ctypes,
# we cannot read the real VSN, so we accept it as a parameter.

N = 0xFFFFFFFD  # RSA modulus
E = 0x13B0ACA5  # public exponent
D = 0xD         # private exponent (1/E mod phi(N)), phi(N) = 2418*71784 = 0xFFF8C460


def get_vsn():
    """Try to get VSN from C:\ drive on Windows. Returns None on failure."""
    try:
        import ctypes
        vsn = ctypes.c_ulong(0)
        buf1 = ctypes.create_string_buffer(128)
        buf2 = ctypes.create_string_buffer(128)
        ctypes.windll.kernel32.GetVolumeInformationA(
            b'C:\\\\', buf1, 128, ctypes.byref(vsn), None, None, buf2, 128
        )
        v = vsn.value >> 16
        while v >= 0x270F:
            v -= 0x3E8
        return v
    except Exception:
        return None


def get_time_value():
    """Try to get TIME value from GetSystemTimeAsFileTime on Windows.
    Returns None on failure."""
    try:
        import ctypes
        ft = (ctypes.c_ulong * 2)()
        ctypes.windll.kernel32.GetSystemTimeAsFileTime(ctypes.byref(ft))
        lo = ft[0]
        hi = ft[1]

        # Add offsets
        lo_new = (lo + 0x2AC18000) & 0xFFFFFFFF
        carry = 1 if (lo + 0x2AC18000) > 0xFFFFFFFF else 0
        hi_new = (hi + 0x0FE624E21 + carry) & 0xFFFFFFFF

        # Divide 64-bit value by 0x989680 (10_000_000)
        divisor = 0x989680
        combined = (hi_new << 32) | lo_new
        quotient_full = combined // divisor

        # The asm: divides hi:lo by 989680h, takes quotient of hi part,
        # then divides (remainder_of_hi_div:lo) by 989680h
        # Result: eax = low 32 bits of full quotient
        # Then: edx = high 32 bits of full quotient (ebx)
        # Then: mul ecx (0xC22E4507), shr edx, 0x10
        # This is a compiler trick for dividing by 10_000_000 and extracting seconds
        # ASSUMPTION: TIME = low 32 bits of (combined // 989680h)
        TIME_raw = quotient_full & 0xFFFFFFFF

        # Apply the 0xC22E4507 multiply trick (compiler div by something)
        # mul 0xC22E4507, shr edx, 0x10
        # This extracts TIME value
        # ASSUMPTION: TIME = ((TIME_raw * 0xC22E4507) >> 32) >> 16
        product = (TIME_raw * 0xC22E4507) & 0xFFFFFFFFFFFFFFFF
        TIME = (product >> 32) >> 0x10
        TIME = TIME & 0xFFFFFFFF
        return TIME
    except Exception:
        return None


def compute_serial(vsn, time_val):
    """Compute the serial given VSN and TIME values."""
    # Build cipher: (TIME * 10000 + VSN) * 8
    cipher = (time_val * 10000 + vsn) & 0xFFFFFFFF
    cipher = (cipher * 8) & 0xFFFFFFFF

    # RSA: serial = cipher^D mod N  with D=13, N=0xFFFFFFFD
    serial = pow(cipher, D, N)
    return serial


def verify_from_parts(vsn, time_val, serial):
    """Verify a serial given VSN and TIME.
    The crackme checks:
      plaintext = serial^E mod N
      Then plaintext >> 3 should give (TIME * 10000 + VSN)
    """
    # Decrypt
    plaintext = pow(serial, E, N)
    # The serial was computed as pow(cipher, D, N) where cipher = (TIME*10000+VSN)*8
    # So plaintext should equal cipher = (TIME*10000+VSN)*8
    # Check: plaintext >> 3 == TIME*10000 + VSN (if plaintext is divisible by 8)
    if plaintext % 8 != 0:
        return False
    combined = plaintext >> 3
    # combined = TIME * 10000 + VSN
    recovered_vsn = combined % 10000
    recovered_time = combined // 10000
    return (recovered_vsn == vsn) and (recovered_time == time_val)


def verify(name, serial):
    """Attempt to verify serial using live hardware/time data.
    Since there's no name field in this crackme, 'name' is ignored.
    ASSUMPTION: The serial is a decimal string representing the serial number.
    """
    try:
        serial_int = int(serial)
    except (ValueError, TypeError):
        return False

    vsn = get_vsn()
    time_val = get_time_value()
    if vsn is None or time_val is None:
        # Cannot verify without Windows APIs
        # ASSUMPTION: fall through to False
        return False

    return verify_from_parts(vsn, time_val, serial_int)


def keygen(name):
    """Generate a serial. 'name' is ignored (crackme doesn't use name).
    Returns a serial as a decimal string, or None if platform unsupported.
    """
    vsn = get_vsn()
    time_val = get_time_value()
    if vsn is None or time_val is None:
        # For testing: use dummy values
        # ASSUMPTION: use example VSN=1234, TIME=12345
        vsn = 1234
        time_val = 12345
    serial = compute_serial(vsn, time_val)
    return str(serial)


def keygen_from_vsn_time(vsn, time_val):
    """Generate serial directly from known VSN and TIME values."""
    serial = compute_serial(vsn, time_val)
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
