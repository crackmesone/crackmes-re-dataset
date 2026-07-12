import ctypes
import struct

def _get_drive_key():
    """
    Simulate the key derivation from drive type and volume label.
    On Windows this would call GetDriveTypeA(NULL) and GetVolumeInformationA(NULL, ...).
    Returns the 32-bit value stored in dword_40339C.
    """
    try:
        import ctypes
        from ctypes import wintypes
        # GetDriveTypeA(NULL) - gets drive type of current directory's drive
        drive_type = ctypes.windll.kernel32.GetDriveTypeA(None)
        
        # GetVolumeInformationA(NULL, buf, 11, 0, 0, 0, 0, 0)
        vol_buf = ctypes.create_string_buffer(12)
        ctypes.windll.kernel32.GetVolumeInformationA(
            None,       # lpRootPathName
            vol_buf,    # lpVolumeNameBuffer
            11,         # nVolumeNameSize
            None, None, None, None, 0
        )
        
        # Read first 4 bytes of volume label as unsigned int (little-endian)
        vol_label_bytes = vol_buf.raw[:4]
        vol_uint = struct.unpack('<I', vol_label_bytes)[0]
        
        # Loop: for i in range(drive_type, 0, -1): sum += i * vol_uint
        # i goes from drive_type down to 1
        total = 0
        i = drive_type
        while i > 0:
            # mul: EAX = ECX * EBX, only lower 32 bits used (add eax to edi)
            product = (i * vol_uint) & 0xFFFFFFFF
            total = (total + product) & 0xFFFFFFFF
            i -= 1
        
        return total
    except Exception:
        # ASSUMPTION: On non-Windows or if API unavailable, return None
        return None


def _serial_to_int(serial_str):
    """
    Replicate sub_4013D2: convert serial string to integer.
    Handles optional leading '-'.
    This is essentially atoi() returning a signed-xor result.
    """
    s = serial_str.encode('ascii') if isinstance(serial_str, str) else serial_str
    idx = 0
    edx = 0  # 0 normally, 0xFFFFFFFF if negative sign
    ecx = 0
    eax = 0
    
    if idx < len(s):
        al = s[idx]
        idx += 1
        if al == 0x2D:  # '-'
            edx = 0xFFFFFFFF
            if idx < len(s):
                al = s[idx]
                idx += 1
        # Jump to loc_4013FB check
        # loc_4013FB: check if al is zero
        while al != 0:
            # loc_4013F0
            al = (al - 0x30) & 0xFF
            # lea ecx, [ecx + ecx*4]  => ecx = ecx * 5
            ecx = (ecx + ecx * 4) & 0xFFFFFFFF
            # lea ecx, [eax + ecx*2]  => ecx = eax + ecx*2
            ecx = (al + ecx * 2) & 0xFFFFFFFF
            if idx < len(s):
                al = s[idx]
                idx += 1
            else:
                al = 0
    
    # lea eax, [edx + ecx]
    eax = (edx + ecx) & 0xFFFFFFFF
    # xor eax, edx
    eax = eax ^ edx
    
    return eax  # This is the parsed serial value returned in EAX


def verify(name, serial):
    """
    Verify a serial for CrackHead by Crudd.
    Note: The crackme does NOT use the name - only the drive volume label matters.
    The serial is valid if: parse(serial) == dword_40339C XOR 'Suzy'
    
    dword_40339C is computed from GetDriveTypeA and GetVolumeInformationA.
    
    From the writeup:
      cmp eax, esi  (eax = parsed serial, esi = dword_40339C XOR 'Suzy')
      The sub_4013D2 does: pop esi; xor esi, 0x797A7553  AFTER returning eax.
      So esi (passed in) is XORed with 'Suzy' in the subroutine... 
      Wait, re-reading: the sub pops ESI (which was pushed at start of sub),
      then XORs it with 0x797A7553. ESI before the call was dword_40339C.
      The return value EAX is the parsed serial.
      Then back in caller: cmp eax, esi
      So: parsed_serial == (dword_40339C XOR 0x797A7553)
    """
    drive_key = _get_drive_key()
    if drive_key is None:
        # ASSUMPTION: Cannot verify without Windows API
        return False
    
    # The expected value is dword_40339C XOR 'Suzy' (0x797A7553)
    # 'Suzy' as little-endian bytes: S=0x53, u=0x75, z=0x7A, y=0x79 => 0x797A7553
    SUZY = 0x797A7553
    expected = (drive_key ^ SUZY) & 0xFFFFFFFF
    
    parsed = _serial_to_int(serial)
    
    return parsed == expected


def keygen(name):
    """
    Generate a valid serial for CrackHead.
    The name is ignored by the crackme.
    Serial = str(dword_40339C XOR 0x797A7553) as decimal.
    Note: Result may be negative if high bit is set (handle sign).
    """
    drive_key = _get_drive_key()
    if drive_key is None:
        raise RuntimeError('keygen() requires Windows API (GetDriveTypeA/GetVolumeInformationA)')
    
    SUZY = 0x797A7553
    key_val = (drive_key ^ SUZY) & 0xFFFFFFFF
    
    # The parser handles '-' prefix for negative, treat as signed 32-bit
    signed_val = ctypes.c_int32(key_val).value
    
    return str(signed_val)



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
