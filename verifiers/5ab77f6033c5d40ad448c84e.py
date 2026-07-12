# Reverse-engineered from crackmes.de solutions for 'self_destructed' by d4ph1
# 
# Key findings from solutions:
# 1. The serial is stored at address 0x403370 and is computed from the computer name
#    (GetProcAddress path that's also used for anti-debug creates part of the serial)
# 2. The comparison loop at 0x401491 compares entered serial byte-by-byte with computed serial
# 3. Solution 1 reveals a hardcoded example serial: "7E86E6BA7E86D62A-3605-6BF980FD5600FE00002F2975F65800"
# 4. Solution 4 confirms: serial depends on computer name (Windows API GetComputerName likely used)
# 5. The exact serial generation algorithm is NOT fully disclosed in any writeup -
#    all solutions bypass by patching or reading computed serial at runtime
# 
# ASSUMPTION: The serial shown in solution 1 is a sample output for one specific machine.
# ASSUMPTION: The algorithm uses the computer name (via Windows API) to generate the serial.
# ASSUMPTION: The format appears to be hex-encoded bytes with dashes, similar to a GUID-like structure.
# ASSUMPTION: The generation involves some transformation of computer name bytes 
#             producing hex characters (seen from the 0x401207 region used for both anti-debug and serial).
# We cannot fully reconstruct the serial generation algorithm from the writeups alone.
# The comparison at 0x403270 (entered serial buffer) vs 0x403370 (computed serial) is clear.

import ctypes
import platform
import struct

def _get_computer_name_windows():
    """Try to get computer name via ctypes on Windows."""
    try:
        buf = ctypes.create_string_buffer(256)
        size = ctypes.c_ulong(256)
        ctypes.windll.kernel32.GetComputerNameA(buf, ctypes.byref(size))
        return buf.value.decode('ascii', errors='replace')
    except Exception:
        return platform.node()

def _get_computer_name():
    """Get computer name cross-platform."""
    if platform.system() == 'Windows':
        return _get_computer_name_windows()
    return platform.node()

def keygen(name):
    """
    ASSUMPTION: The serial is computed from the computer name, NOT the user name.
    The exact algorithm inside the crackme (around 0x401207-0x401484) is not disclosed
    in the writeups. All solutions patch the binary to display the computed serial at runtime.
    
    We know:
    - Serial is stored at 0x403370 after computation
    - It is compared byte-by-byte with entered serial at 0x403270
    - The format from solution 1 looks like: '7E86E6BA7E86D62A-3605-6BF980FD5600FE00002F2975F65800'
    - Username must be >= 4 and <= 20 characters (from solution 4)
    
    Without the actual assembly listing for the serial generation routine (0x401207 to 0x401484),
    we cannot reconstruct the algorithm. This is a STUB.
    """
    computer_name = _get_computer_name()
    
    # ASSUMPTION: The serial generation XORs or otherwise transforms computer name bytes
    # into hex pairs. The exact operations are unknown.
    # This is a placeholder that cannot produce correct serials.
    
    # ASSUMPTION: Based on the sample serial format, it looks like pairs of hex bytes
    # possibly derived from some hash or transformation of computer name bytes
    result_bytes = []
    comp_bytes = computer_name.encode('ascii', errors='replace')
    
    # ASSUMPTION: Some rolling computation over computer name bytes
    # The code at 0x401207 is shared with anti-debug and serial gen
    val = 0
    for i, b in enumerate(comp_bytes):
        val = ((val ^ b) + i) & 0xFF
        result_bytes.append(val)
        # ASSUMPTION: padding or extending to fixed length
    
    # Pad to at least 24 bytes to match sample serial length (without dashes)
    while len(result_bytes) < 24:
        result_bytes.append((result_bytes[-1] if result_bytes else 0xAA) ^ 0x55)
    
    # ASSUMPTION: Format with dashes like shown in solution 1
    # Sample: '7E86E6BA7E86D62A-3605-6BF980FD5600FE00002F2975F65800'
    # This formatting is also a guess
    hex_str = ''.join(f'{b:02X}' for b in result_bytes)
    # ASSUMPTION: Insert dashes at positions similar to the sample
    # Sample has dash after char 16, then after 4, then rest
    serial = f"{hex_str[0:16]}-{hex_str[16:20]}-{hex_str[20:]}"
    
    return serial  # NOTE: This will NOT produce correct serials - algorithm unknown

def verify(name, serial):
    """
    From the solutions we know:
    - Username must be 4-20 characters
    - The comparison is done byte-by-byte between entered serial and computed serial
    - We cannot compute the correct serial without the actual algorithm
    
    ASSUMPTION: Username length check is 4 <= len(name) <= 20
    """
    if not (4 <= len(name) <= 20):
        return False
    
    # ASSUMPTION: generate the serial for this machine and compare
    computed = keygen(name)
    
    # Comparison is byte-by-byte (case-sensitive, per the CMP EAX, EBX in the loop)
    return serial == computed


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
