import struct
import ctypes

# NOTE: This crackme is hardware-based (uses GetVolumeInformation).
# The serial is derived from the volume serial number and volume name of the C: drive.
# We reconstruct the algorithm from the writeup.

# ASSUMPTION: vol_serial_number is an integer (e.g., 0xABCD1234)
# ASSUMPTION: vol_name is treated as a DWORD (first 4 bytes or as integer sum)
# The writeup says: EAX = vol_serial_number + vol_name (as DWORD at EBP-44 or EBP-C)
# Solution 1 says ebp-c is volume name, solution 2 says EBP-44 is FileSystemNameBuffer
# ASSUMPTION: vol_name_val is the DWORD value stored at the volume name buffer location
# (i.e., the first 4 bytes of the volume name string interpreted as little-endian DWORD)

def rol32(val, r):
    val &= 0xFFFFFFFF
    return ((val << r) | (val >> (32 - r))) & 0xFFFFFFFF

def shr32(val, r):
    return (val & 0xFFFFFFFF) >> r

def bswap32(val):
    val &= 0xFFFFFFFF
    b = struct.pack('>I', val)
    return struct.unpack('<I', b)[0]

def compute_hash1_hash2(vol_serial, vol_name_dword):
    """Compute hash1 (stored at 403128/403168) and hash2 (403137/403177).
    
    From the writeup (solution 1, routine at 0040137E / solution 2 at 00401378):
      eax = vol_serial + vol_name_dword
      ... (some formatting calls that don't affect the value) ...
      eax = eax >> 2  (SHR EAX, 2)
      hash1 = eax  (stored at 403128)
      hash2 = bswap(eax)  (stored at 403137)
    """
    combined = (vol_serial + vol_name_dword) & 0xFFFFFFFF
    # ASSUMPTION: The calls to 004014CC and 004014E8 are formatting/display routines
    # that don't modify EAX for the purpose of hash computation.
    hash1 = shr32(combined, 2)
    hash2 = bswap32(hash1)
    return hash1, hash2

def compute_id_no(vol_serial, vol_name_dword):
    """From solution 2, the ID No. displayed is computed as:
      eax = vol_serial + vol_name_dword
      call hash_routine -> eax = SHR(combined,2) = hash1
      eax = eax - 0x44464347
      eax = eax << 2  (SHL EAX, 2)
      eax = bswap(eax)
      eax = eax XOR 0x7479
      eax = eax + 0x313233
      -> this is the ID No. (displayed to user)
    """
    combined = (vol_serial + vol_name_dword) & 0xFFFFFFFF
    hash1 = shr32(combined, 2)
    eax = (hash1 - 0x44464347) & 0xFFFFFFFF
    eax = (eax << 2) & 0xFFFFFFFF
    eax = bswap32(eax)
    eax = (eax ^ 0x7479) & 0xFFFFFFFF
    eax = (eax + 0x313233) & 0xFFFFFFFF
    return eax

def serial_to_hex(serial_str):
    """Convert serial string to hex DWORD.
    The crackme calls a routine at 00401494/00401490 to convert input serial to hex.
    ASSUMPTION: This routine converts the ASCII hex string to an integer DWORD.
    e.g., '12345678' -> 0x12345678
    """
    try:
        return int(serial_str, 16) & 0xFFFFFFFF
    except ValueError:
        return 0

def compute_hash3_from_serial(serial_hex):
    """From routine at 004013C6 / 004013C0:
      pushad
      ROL EAX, 2        ; eax = serial_hex rotated left by 2
      MOV [40312D], EAX ; hash3_part1 stored at 40312D
      ADD EAX, 0x7479
      XOR EAX, 0x313233
      SHL EAX, 6
      MOV [403132], EAX ; hash3_part2 stored at 403132
    """
    eax = serial_hex & 0xFFFFFFFF
    eax_rol2 = rol32(eax, 2)
    hash3_part1 = eax_rol2  # stored at 40312D
    
    eax2 = (eax_rol2 + 0x7479) & 0xFFFFFFFF
    eax2 = (eax2 ^ 0x313233) & 0xFFFFFFFF
    eax2 = (eax2 << 6) & 0xFFFFFFFF
    hash3_part2 = eax2  # stored at 403132
    
    return hash3_part1, hash3_part2

def verify(name, serial):
    """Verify serial against hardware ID.
    
    NOTE: Since this is hardware-based, name is not used.
    The 'serial' here is expected as a hex string (what the user enters).
    For simulation, we need the hardware values. We use dummy defaults.
    
    The check (at 004013E3) compares value at 403128 (hash1) with value at 40312D (hash3_part1):
      hash1 == hash3_part1 means the serial is valid for CheckII.
    
    Actually from the code:
      Check at 004013E3 compares bytes at 403128 with 40312D byte by byte until null or mismatch.
      But these are DWORDs stored as memory values, so it's a memory comparison.
      Since hash3_part1 = ROL(serial_hex, 2) and hash1 = SHR(combined, 2),
      we need: ROL(serial_hex, 2) == hash1
      => serial_hex = ROR(hash1, 2)
    
    ASSUMPTION: vol_serial and vol_name_dword must be provided externally.
    We use placeholder values for demonstration.
    """
    # ASSUMPTION: These would come from GetVolumeInformation at runtime
    # For testing, use placeholder values
    vol_serial = 0x12345678  # ASSUMPTION: placeholder
    vol_name_dword = 0x00000000  # ASSUMPTION: placeholder
    
    hash1, hash2 = compute_hash1_hash2(vol_serial, vol_name_dword)
    
    serial_hex = serial_to_hex(serial)
    hash3_part1, hash3_part2 = compute_hash3_from_serial(serial_hex)
    
    # The critical check: hash3_part1 (at 40312D) must equal hash1 (at 403128)
    return hash3_part1 == hash1

def ror32(val, r):
    val &= 0xFFFFFFFF
    return ((val >> r) | (val << (32 - r))) & 0xFFFFFFFF

def keygen(name, vol_serial=0x12345678, vol_name_dword=0x00000000):
    """Generate a valid serial for the given hardware values.
    
    We need: ROL(serial_hex, 2) == hash1
    => serial_hex = ROR(hash1, 2)
    Then convert serial_hex to hex string.
    
    NOTE: name is not used (hardware-based crackme).
    vol_serial and vol_name_dword must match the target machine.
    """
    hash1, hash2 = compute_hash1_hash2(vol_serial, vol_name_dword)
    serial_hex = ror32(hash1, 2)
    return format(serial_hex, '08X')


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
