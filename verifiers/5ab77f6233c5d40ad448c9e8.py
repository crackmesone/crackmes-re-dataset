# Reverse-engineered from eraghant's writeup of Sunshine's CrackMe #1
#
# Summary of the algorithm (from the writeup):
#
# 1. Serial must be all hexadecimal characters (last 7 chars converted to integer).
# 2. Username length must be > 3.
# 3. Serial length must be between 5 and 8 characters (size - 5 <= 3, so size in [5..8]).
# 4. A value is read from address 0x4043D8 (written at 0x401298 from ESI, which was read
#    from the same address earlier -- the comment shows DS:[004043D8]=0x2C = 44 decimal).
#    If this value <= 0, jump to badboy.
# 5. The check is:
#      file_value + sum_of_username_chars + int(serial_hex) == 0x004010B0
#
# The value at 0x4043D8 appears to be 0x2C (44) based on the OllyDbg comment.
# ASSUMPTION: The value at [4043D8] is fixed at 0x2C (44 decimal) at check time.
# ASSUMPTION: The serial is interpreted as a hex integer (last 7 hex digits -> int).
# ASSUMPTION: 'int(serial_hex)' means the integer value of the hex string of the serial.
# ASSUMPTION: The serial can be 5-8 hex characters long.
# ASSUMPTION: The address value 0x004010B0 is the target of the comparison.

FILE_VALUE = 0x2C  # Value read from [4043D8], seen as 0x2C in the writeup comment
TARGET = 0x004010B0


def sum_name(name: str) -> int:
    """Sum of ASCII values of the name characters."""
    return sum(ord(c) for c in name)


def verify(name: str, serial: str) -> bool:
    # Check 1: username length must be > 3
    if len(name) <= 3:
        return False

    # Check 2: serial length must be between 5 and 8
    if not (5 <= len(serial) <= 8):
        return False

    # Check 3: serial must be all hexadecimal characters
    try:
        serial_int = int(serial, 16)
    except ValueError:
        return False

    # Check 4: file_value must be > 0 (it is 0x2C, so this passes)
    if FILE_VALUE <= 0:
        return False

    # Check 5: file_value + sum_of_name + serial_int == TARGET
    name_sum = sum_name(name)
    total = FILE_VALUE + name_sum + serial_int
    return total == TARGET


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) <= 3:
        raise ValueError("Name must be longer than 3 characters")

    name_sum = sum_name(name)
    # serial_int = TARGET - FILE_VALUE - name_sum
    serial_int = TARGET - FILE_VALUE - name_sum

    if serial_int < 0:
        raise ValueError(f"Computed serial is negative ({serial_int}); name sum too large")

    # Format as hex, check it fits in 1..8 hex digits and is <= 8 chars
    serial_hex = format(serial_int, 'X')
    if len(serial_hex) > 8:
        raise ValueError(f"Serial too large: {serial_hex}")

    # Pad to at least 5 hex chars (minimum serial length from the check: size-5 <= 3 => size >= 5)
    if len(serial_hex) < 5:
        serial_hex = serial_hex.zfill(5)

    return serial_hex



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
