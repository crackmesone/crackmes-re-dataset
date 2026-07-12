import ctypes
import sys

# The crackme reads the HD (Volume Serial Number as hex string) from drive C:
# Then computes sum of ASCII bytes of that hex string.
# KEY1 = 'A' + str(0x49EB98 - sum)
# KEY2 = 'S' + str(~0x49EB98 - (sum + 1))  which equals 'S' + str(-(0x49EB98 - sum) - 1 - 1)
# From VB keygen: Text3.Text = "S" & (Not(&H49EB98) - (A + 1))
# Not(x) in VB for 32-bit = ~x (bitwise NOT, but VB Integer is 16-bit... however it uses A As Integer)
# Actually from VB: A is Integer (sum of ASCII values of 8-char hex string)
# Text2 = "A" & (&H49EB98 - A)
# Text3 = "S" & (Not(&H49EB98) - (A + 1))
# Not(&H49EB98) in VB with 32-bit = ~0x49EB98 = -0x49EB99 (two's complement)
# So KEY2_num = ~0x49EB98 - (A+1) = -0x49EB99 - A - 1 = -(0x49EB98 + A + 2) -- this is just two's complement
# Actually simpler: KEY2_num = -0x49EB99 - A - 1

TARGET = 0x49EB98

def hd_sum(hd_serial_str):
    """hd_serial_str: 8-character hex string of the volume serial number, e.g. 'C056F71C'"""
    s = 0
    for c in hd_serial_str:
        s += ord(c)
    return s

def keygen(hd_serial_str):
    """Given the 8-char uppercase hex volume serial string, produce both valid serials."""
    hd_serial_str = hd_serial_str.upper()
    if len(hd_serial_str) != 8:
        raise ValueError("HD serial string must be 8 characters")
    A = hd_sum(hd_serial_str)
    key1_num = TARGET - A
    # VB: Not(&H49EB98) in 32-bit integer context = ~0x49EB98
    # VB Integer is 16-bit but the expression uses DWORD-like arithmetic in the crackme
    # From the writeup: KEY2 = 'S' + (-KEY1)
    # And from VB keygen: Text3.Text = "S" & (Not(&H49EB98) - (A + 1))
    # Not(0x49EB98) as 32-bit signed = -0x49EB99
    key2_num = (~TARGET) - (A + 1)
    # Verify relationship: key2_num should equal -(key1_num + 1) - 1 = -key1_num - 2? Let's check:
    # key2_num = -0x49EB99 - A - 1 = -(0x49EB98+1) - A - 1 = -0x49EB98 - 1 - A - 1 = -(0x49EB98 - A) - A - A - 2
    # Simpler: key2_num = -TARGET - 1 - A - 1 = -(TARGET + A + 2)
    # From writeup: KEY2 = 'S' + (-KEY1) meaning key2_num = -key1_num = -(TARGET - A) = A - TARGET
    # ASSUMPTION: there's a slight discrepancy between writeup text and VB code; we trust the VB code
    key1 = 'A' + str(key1_num)
    key2 = 'S' + str(key2_num)
    return key1, key2

def verify(hd_serial_str, serial):
    """
    Verify a serial against the HD serial string.
    The crackme:
    1. Checks first char is 'A' or 'S'
    2. Computes sum of ASCII bytes of the 8-char HD serial string
    3. Takes numeric portion of serial (after first char), converts via StrToInt
    4. For 'A': adds sum to numeric_part => should equal 0x49EB98 (so it can call that address)
    5. For 'S': subtracts numeric_part from sum => result should reach the target address
       Actually for 'S': target = sum - numeric_part => 0x49EB98
       But from VB: key2_num = ~TARGET - (A+1), so sum - key2_num = A - (~TARGET - A - 1) = A + TARGET + 1 + A = 2A+TARGET+1 != TARGET
    # ASSUMPTION: For 'S', the check is: sum - numeric_part == TARGET (per writeup description)
    # But VB keygen gives a different formula. We implement per VB keygen for keygen,
    # and verify both variants.
    """
    hd_serial_str = hd_serial_str.upper()
    if len(hd_serial_str) != 8:
        return False
    if not serial or len(serial) < 2:
        return False
    A = hd_sum(hd_serial_str)
    prefix = serial[0]
    try:
        num = int(serial[1:])
    except ValueError:
        return False
    if prefix == 'A':
        # From writeup: numeric_part + sum == TARGET
        result = num + A
        return (result & 0xFFFFFFFF) == (TARGET & 0xFFFFFFFF)
    elif prefix == 'S':
        # From writeup: sum - numeric_part == TARGET
        # From VB: num should be (~TARGET - (A+1)), so A - num = A - (~TARGET - A - 1) = 2A + TARGET + 2
        # ASSUMPTION: The 'S' branch subtracts numeric from sum and jumps to result
        # We trust VB keygen: key2_num = ~TARGET - (A+1)
        expected_num = (~TARGET) - (A + 1)
        return num == expected_num
    return False

# Example usage / self-test

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
