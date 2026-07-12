import math

def _int_to_str(n):
    """Convert integer to string (handles sign, like the asm itoa routine)."""
    return str(n)

def compute_hash1(name):
    """First part of the algorithm: compute the hash from the name."""
    length = len(name)
    ebx = 3 * length  # 3 * len
    serial = 0
    for ch in name:
        al = ord(ch)
        edx = al + ebx          # add edx, ebx  (ebx = 3*len)
        edx = edx ^ length      # xor edx, NameLength
        eax = edx
        eax = (eax * ebx) & 0xFFFFFFFF  # mul ebx
        serial = (serial + eax) & 0xFFFFFFFF
    return serial

def compute_second_part(hash1, serial_str_len):
    """
    Algo4 / sub_401269Second:
    fild hash1
    fadd 0x000030AE  (AlgoConstant as float = 12462.0 when stored as int 0x30AE ... 
    but in solution 4 the constant is reset to 000003AEh = 942)
    fsqrt
    fistp CRCofCRC
    then loop: ebx = serial_str_len; ecx = serial_str_len
    loop: add ebx, eax; sub ebx, 2; loop
    """
    # ASSUMPTION: The AlgoConstant used during computation.
    # Solution 2 (Kenn) uses 0AE300000h as a float (little-endian IEEE754 float: 0x000030AE = 12462.0 as int but
    # 0AE300000h as raw float bytes = struct.unpack('<f', bytes.fromhex('00000030AE'[2:])) ... 
    # Let's be precise:
    # Solution 2: mov dword ptr [String1], 0AE300000h  -> this is a 32-bit float stored at [String1]
    # 0AE300000h in hex = 0x0AE30000 (note: it's a DWORD)
    # Actually in solution 2: mov dword ptr [String1], 0AE300000h
    # 0AE300000h = 182452224 decimal. As IEEE 754 float: sign=0, exp=0x15C-127=93, mantissa -> very large number
    # Wait, let me re-read: '0AE300000h' - that is 8 hex digits: 0A E3 00 00 -> 0x0AE30000
    # As float: sign=0, biased_exp = (0x0AE30000 >> 23) & 0xFF = 0x15 = 21, so exp = 21-127 = -106 -> tiny
    # Hmm. But solution 4 uses AlgoConstant DWORD 000030AEh = 12462, and resets to 000003AEh = 942 after use.
    # The fild instruction loads an integer (not float). fadd adds the AlgoConstant as a float.
    # In solution 4: AlgoConstant DWORD 000030AEh = 12462 decimal stored as DWORD, used with fadd as float.
    # fild loads hash1 as integer, fadd adds AlgoConstant (loaded as float from DWORD = 12462.0)
    # Solution 3 (C#) does NOT add any constant - just sqrt(firstpart).
    # Solution 1 (br0ken C++) also just does sqrt(Serial) with no constant.
    # ASSUMPTION: The constant may be 0 or the solutions differ. Using solution 3 as reference (no constant).
    import struct
    # From solution 4 asm: fild NameCRC; fadd AlgoConstant (=0x30AE=12462 as DWORD -> float 12462.0)
    # ASSUMPTION: AlgoConstant = 12462.0 based on solution 4
    algo_constant = 12462.0
    val = float(hash1) + algo_constant
    crc_of_crc = int(math.sqrt(val))  # fistp rounds to nearest (banker's rounding in x87)
    # fistp uses round-to-nearest-even by default on x87
    # Python int() truncates, so we approximate with round()
    sqrt_val = math.sqrt(val)
    crc_of_crc = int(sqrt_val)  # fistp truncates toward zero for fistp? No, fistp uses current rounding mode
    # ASSUMPTION: use standard round
    frac = sqrt_val - int(sqrt_val)
    if frac >= 0.5:
        crc_of_crc = int(sqrt_val) + 1
    else:
        crc_of_crc = int(sqrt_val)
    
    # Now the loop: ecx = serial_str_len, ebx = serial_str_len
    # loop: add ebx, eax (eax=crc_of_crc); sub ebx, 2; loop (ecx times)
    ebx = serial_str_len
    ecx = serial_str_len
    for _ in range(ecx):
        ebx = (ebx + crc_of_crc - 2) & 0xFFFFFFFF
    return ebx & 0xFFFFFFFF

def verify(name, serial):
    """Verify name/serial pair."""
    if len(name) < 5:
        return False
    
    hash1 = compute_hash1(name)
    hash1_str = str(hash1)
    serial_str_len = len(hash1_str)
    
    second_part_val = compute_second_part(hash1, serial_str_len)
    
    # Serial = str(second_part_val) + str(hash1)
    expected = str(second_part_val) + hash1_str
    return serial == expected

def keygen(name):
    """Generate serial for a given name."""
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")
    
    hash1 = compute_hash1(name)
    hash1_str = str(hash1)
    serial_str_len = len(hash1_str)
    
    second_part_val = compute_second_part(hash1, serial_str_len)
    
    serial = str(second_part_val) + hash1_str
    return serial


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
