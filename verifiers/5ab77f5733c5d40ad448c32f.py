import ctypes
import datetime

# Reconstructed from Key1 proc in Keygen.asm
# The algorithm uses the CURRENT LOCAL TIME to generate the serial,
# so the serial is time-dependent (generated at runtime).
# Name must be 5..40 chars long.

def _compute_serial(name: str, now: datetime.datetime = None) -> str:
    """
    Reconstructs the Key1 algorithm from the assembly source.
    
    SYSTEMTIME fields used:
      wYear       = now.year
      wMonth      = now.month
      wDayOfWeek  = now.weekday() mapped: Mon=1..Sun=0 (Python) vs Windows: Sun=0, Mon=1..Sat=6
      wDay        = now.day
    
    Assembly logic:
      eax = wYear
      ecx = eax + eax*4  = year * 5
      edx = wMonth
      eax = edx*8 - edx  = month * 7
      edx = eax + ecx*2  = month*7 + year*10
      ecx = wDayOfWeek + 1
      eax = edx / ecx    (signed integer division)
      ecx = eax          (quotient)
      ecx = ecx - wDay
      ecx = ecx * sLen   (sLen = length of name)
      eax = ecx + ecx*4  = ecx * 5
      => number = eax
      
      Temp = sprintf("%d", number)  => first_part string of digits
      
    Serial construction:
      - Take first 3 chars of Temp (first_part), append '-'
      - Append chars from NameBuffer starting at sStart for sFinish chars
          where sStart = (sLen >> 1) - 1  = sLen//2 - 1
                sFinish = (sLen * 0x55555556) >> 32  approx sLen//3
                (MASM imul edx trick for division by 3)
      - Append Temp[3:]  (rest of first_part after index 3)
      - Append '-'
      - Append full NameBuffer (name)
    """
    if now is None:
        now = datetime.datetime.now()

    sLen = len(name)
    if sLen < 5 or sLen > 40:
        return ""

    # Windows SYSTEMTIME
    wYear = now.year
    wMonth = now.month
    # Windows wDayOfWeek: Sunday=0, Monday=1, ..., Saturday=6
    # Python weekday(): Monday=0 ... Sunday=6
    py_weekday = now.weekday()  # 0=Mon ... 6=Sun
    wDayOfWeek = (py_weekday + 1) % 7  # Convert: Mon->1, Tue->2, ..., Sun->0
    wDay = now.day

    # Assembly computation
    year = wYear & 0xFFFF
    ecx = year + year * 4  # year * 5
    month = wMonth & 0xFFFF
    eax_m = month * 8 - month  # month * 7
    edx = eax_m + ecx * 2  # month*7 + year*10
    
    dow = wDayOfWeek & 0xFFFF
    ecx2 = dow + 1  # wDayOfWeek + 1
    
    # signed 32-bit division
    # treat edx as signed 32-bit
    edx_signed = ctypes.c_int32(edx).value
    ecx2_signed = ctypes.c_int32(ecx2).value
    
    # idiv: quotient
    if ecx2_signed == 0:
        return ""
    quotient = int(edx_signed / ecx2_signed)  # truncate toward zero
    
    ecx3 = quotient - wDay
    ecx3 = ecx3 * sLen
    
    # imul ecx,ebx then lea eax,[ecx+ecx*4]
    number = ctypes.c_int32(ecx3 + ecx3 * 4).value  # ecx3 * 5, 32-bit
    
    first_part = str(number)  # wsprintf %d
    
    # Build serial:
    # 1) First 3 chars of first_part + '-'
    serial = first_part[:3] + '-'
    
    # 2) Append name[sStart : sStart+sFinish]
    # sStart = (sLen >> 1) - 1  = sLen // 2 - 1
    sStart = (sLen >> 1) - 1
    
    # sFinish: assembly does  MOV EDX,55555556h; imul edx (signed); mov sFinish,edx
    # This is the high 32 bits of sLen * 0x55555556, treated as signed
    # For sLen in [5..40], this equals ceil(sLen/3) or floor(sLen/3)+1
    # ASSUMPTION: This is integer division by 3, rounded as per the magic number trick
    product = ctypes.c_int32(0x55555556).value * sLen  # signed 64-bit
    # High 32 bits (arithmetic right shift of 64-bit product)
    sFinish = (product >> 32) & 0xFFFFFFFF
    # Treat as signed 32-bit
    sFinish = ctypes.c_int32(sFinish).value
    # For positive sLen: sFinish = sLen // 3  (approximately)
    # Let's verify with the standard trick: result = (sLen * 0x55555556) >> 32
    # Actually for sLen=6: 6*0x55555556 = 0x200000014 >> 32 = 2, so sFinish=2
    # That matches sLen//3=2. Good.
    # But we need the actual 64-bit signed multiply high:
    import ctypes as ct
    val = ct.c_int32(0x55555556).value  # = 1431655766
    product64 = val * sLen  # Python big int
    sFinish = (product64 >> 32)
    
    name_part = name[sStart: sStart + sFinish]
    serial += name_part
    
    # 3) Append first_part[3:]
    serial += first_part[3:]
    
    # 4) Append '-'
    serial += '-'
    
    # 5) Append full name
    serial += name
    
    return serial


def verify(name: str, serial: str) -> bool:
    """
    The crackme verifies by comparing the displayed serial to what Key1 generates
    at the time of checking. Since Key1 uses current local time, the serial is
    time-dependent. We regenerate and compare.
    
    ASSUMPTION: The crackme checks the generated serial against user input.
    We check against current time (same minute precision).
    """
    if len(name) < 5 or len(name) > 40:
        return False
    expected = _compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name at the current local time.
    Note: serial is time-dependent!
    """
    if len(name) < 5 or len(name) > 40:
        raise ValueError(f"Name must be 5-40 chars, got {len(name)}")
    return _compute_serial(name)



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
