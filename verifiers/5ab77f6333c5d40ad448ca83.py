import struct

# Standard CRC-32 (PKZIP/ISO-HDLC style) as described in the keygen source
def crc32(data: bytes) -> int:
    """Compute CRC-32 matching the assembly implementation in crc32.inc"""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return (~crc) & 0xFFFFFFFF


# ASSUMPTION: The serial is a 4-digit hex string (e.g. '24E4') that is compared
# against a value derived from the name/input. The Possibles.txt file shows
# entries like '24E4=24E4', '1E5E=1E5E', etc., suggesting the serial equals
# itself (i.e. any value from the listed set is valid regardless of name).
# This crackme appears to be name-independent with a fixed set of valid serials.

# ASSUMPTION: The valid serials are those listed in Possibles.txt. The format
# appears to be hex values. The serial check may simply verify that the entered
# value is in a known set, OR it may compute CRC32 of the name and compare
# some derived value. Without the actual crackme binary or more detailed
# writeup, we cannot determine the exact relationship.

# The Possibles.txt suggests name-independent valid serials (key=value pairs
# where key==value, implying the serial IS the expected value).

VALID_SERIALS = {
    '24E4', '20FC', '1E5E', '1E54', '1DFA', '1DF0', '1D46', '1D3C',
    '1D32', '1D28', '1D1E', '1D14', '1D0A', '1D00', '1CF6', '1CEC',
    '1A76', '1A6C', '1A12', '1A08', '195E', '1954', '194A', '1940',
    '1936', '192C', '1922', '1918', '190E', '1904',
    # The large block from 1600-176F (every hex value in that range)
}

# Populate the large contiguous range from 0x1600 to 0x176F
for _v in range(0x1600, 0x1770):
    VALID_SERIALS.add(f'{_v:04X}')

# Also add the very large range from 0x14B0 to 0x15FF (truncated in writeup)
# ASSUMPTION: the truncated portion continues the same pattern
for _v in range(0x14B0, 0x1600):
    VALID_SERIALS.add(f'{_v:04X}')


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name.
    
    ASSUMPTION: Based on Possibles.txt showing key=value pairs where every
    listed serial equals itself, the check appears to be: the serial (as a
    4-character uppercase hex string) must be in the set of valid serials.
    The name may or may not factor in - the listed file shows no name
    dependency in the pairs shown.
    
    The keygen uses CRC32, so one interpretation is:
      crc32(name.encode()) & 0xFFFF gives a 4-hex-digit value that must
      match the serial. But without binary confirmation this is an assumption.
    """
    serial_upper = serial.strip().upper()
    
    # ASSUMPTION: Check 1 - serial is in the known valid set (name-independent)
    if serial_upper in VALID_SERIALS:
        return True
    
    # ASSUMPTION: Check 2 - CRC32-based: serial == (crc32(name) & 0xFFFF) as hex
    # This is speculation based on the keygen including CRC32 code
    name_bytes = name.encode('ascii', errors='replace')
    computed = crc32(name_bytes) & 0xFFFF
    computed_hex = f'{computed:04X}'
    if serial_upper == computed_hex:
        return True
    
    return False


def keygen(name: str) -> str:
    """
    Generate a serial for a given name.
    
    ASSUMPTION: Returns a serial from the valid set. If CRC32-based derivation
    is the real algorithm, returns the CRC32-derived serial. Otherwise returns
    a known-good serial from the valid list.
    """
    # ASSUMPTION: Try CRC32-based first
    name_bytes = name.encode('ascii', errors='replace')
    computed = crc32(name_bytes) & 0xFFFF
    computed_hex = f'{computed:04X}'
    
    if computed_hex in VALID_SERIALS:
        return computed_hex
    
    # ASSUMPTION: Fallback - return first known valid serial
    return '1700'



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
