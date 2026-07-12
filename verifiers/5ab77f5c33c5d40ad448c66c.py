import struct
import ctypes
import platform

# ASSUMPTION: The serial validation is Windows-specific and relies on GetComputerNameA.
# On non-Windows platforms we cannot call GetComputerNameA, so we simulate it.
# The name field is NOT used in serial computation - only the computer name matters.

def _get_computer_name_bytes():
    """Try to get the Windows computer name, fallback to platform hostname."""
    try:
        buf = ctypes.create_string_buffer(256)
        size = ctypes.c_ulong(256)
        ctypes.windll.kernel32.GetComputerNameA(buf, ctypes.byref(size))
        return buf.value
    except Exception:
        # ASSUMPTION: On non-Windows, use hostname as stand-in for computer name.
        return platform.node().encode('ascii', errors='replace')

def _compute_part1(computer_name_bytes):
    """
    Part 1: XOR each DWORD of computer name bytes with 0x41544B41,
    accumulate into ESI starting at 0x0040102B.
    Loop increments index by 2 each iteration, stops when index > len.
    """
    # Pad computer_name_bytes to a multiple of 4 for safe DWORD reads
    data = computer_name_bytes
    length = len(data)
    # Pad to ensure we can always read 4 bytes
    padded = data + b'\x00' * 4

    # ASSUMPTION: ESI initial value is 0x0040102B as seen in the keygen asm and C code.
    esi = 0x0040102B
    ecx = 0  # index

    # Loop: read DWORD at [data + ecx], XOR with 0x41544B41, add to ESI
    # Condition: JLE means loop while ecx <= length (signed <= but effectively same here)
    while True:
        eax = struct.unpack_from('<I', padded, ecx)[0]
        eax = (eax ^ 0x41544B41) & 0xFFFFFFFF
        esi = (esi + eax) & 0xFFFFFFFF
        ecx += 2
        if ecx > length:
            break

    # Treat esi as signed 32-bit integer for %d formatting (like C printf)
    esi_signed = ctypes.c_int32(esi).value
    return esi_signed

def _compute_part2_serial():
    """
    Part 2: The second part of the serial is based on the address of the name buffer (0x4030E0).
    As noted in the writeup, this is a constant address, so the middle part is always
    'CIB-4206816-' (decimal of 0x4030E0 = 4206816).
    The format string for part2 is 'CIB-%d-' then appended 'UI'.
    """
    # ASSUMPTION: 0x4030E0 decimal = 4206816, this is hardcoded per the crackme's memory layout.
    # The writeup confirms: 'Valid Serial: CIB-*-CIB-4206816-UI'
    addr = 0x4030E0  # = 4206816
    # Actually looking at C keygen code:
    # wsprintfA(tmp_str, "CIB-%d-", 0x4030E0)  -> "CIB-4206816-"
    # lstrcatA(real_serial, tmp_str)
    # wsprintfA(tmp_str, "UI")  -> "UI"
    # lstrcatA(real_serial, tmp_str)
    # So part2 suffix = "CIB-4206816-UI"
    return "CIB-%d-UI" % addr  # = "CIB-4206816-UI"

def keygen(name):
    """
    Generate valid serial for the given name (name is NOT actually used in computation).
    Serial = 'CIB-<hash>-CIB-4206816-UI'
    where <hash> is computed from the computer name.
    """
    computer_name = _get_computer_name_bytes()
    part1_val = _compute_part1(computer_name)
    # Format: "CIB-%d-" % part1_val + "CIB-4206816-UI"
    serial = "CIB-%d-CIB-4206816-UI" % part1_val
    return serial

def verify(name, serial):
    """
    Verify serial against the expected value.
    The crackme checks:
    1. Name must not be empty
    2. Serial length must be >= 0x11 (17)
    3. Serial must equal the computed serial (string comparison)
    """
    if not name:
        return False
    expected = keygen(name)
    # Length check: serial must be at least 17 chars (0x11)
    if len(serial) < 0x11:
        return False
    return serial == expected


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
