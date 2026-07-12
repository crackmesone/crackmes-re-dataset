import struct

# Magic string used in calculation (from DS:[403ED2])
# ASSUMPTION: The magic string is '(:SEMKCARCECIN:(!@#$' based on writeup description
MAGIC = b'(:SEMKCARCECIN:(!@#$'

# isDebugger value - when NOT in debugger it is 0
IS_DEBUGGER = 0  # ASSUMPTION: 0 when running outside debugger


def compute_hash(name: bytes) -> int:
    """Compute the hash value (EDX) from the name bytes."""
    ecx = 0
    edx = 0
    name_len = len(name)
    
    for ecx in range(name_len):
        al = name[ecx] & 0xFF
        ebx = ecx >> 2  # SHR EBX, 2
        # XOR AL with magic number (cyclic index into MAGIC)
        al = al ^ (MAGIC[ebx % len(MAGIC)] & 0xFF)
        # ADD AL with IsDebuggerPresent return value
        al = (al + IS_DEBUGGER) & 0xFF
        
        # Inner loop: repeat 5 times
        # MOV EBX, 5
        # ADD DL, AL
        # ROL EDX, 4
        # DEC EBX
        # JNZ loop
        for _ in range(5):
            dl = (edx + al) & 0xFFFFFFFF
            # ROL EDX, 4
            edx = dl
            edx = ((edx << 4) | (edx >> 28)) & 0xFFFFFFFF
    
    return edx


def compute_serial_suffix(name: bytes) -> str:
    """Compute the 8-char hex suffix of the serial from the name."""
    edx = compute_hash(name)
    
    result = []
    eax = 0
    
    for i in range(8):
        ecx = 0
        ecx = ecx ^ edx  # XOR ECX, EDX
        ecx = ecx & 0x0F  # AND ECX, 0F
        cl = ecx & 0xFF
        if cl <= 9:
            cl = cl + 0x30  # '0'-'9'
        else:
            cl = cl + 0x37  # 'A'-'F'
        result.append(chr(cl))
        # ROR EDX, 4
        edx = ((edx >> 4) | (edx << 28)) & 0xFFFFFFFF
    
    return ''.join(result)


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    name_bytes = name.encode('ascii', errors='replace')
    serial_bytes = serial.encode('ascii', errors='replace')
    
    # Check name length: 2 <= len <= 32
    name_len = len(name_bytes)
    if name_len < 2 or name_len > 0x20:
        return False
    
    # Check serial length >= 6
    serial_len = len(serial_bytes)
    if serial_len < 6:
        return False
    
    # Length check: serial length must be 12
    # From writeup: BL = name_len - cl + 0Ch, ROL EBX,0Ch, ROR EAX,14h, CMP EBX,EAX
    # cl here is 0 (XOR CL,CL before? Actually cl comes from earlier code)
    # ASSUMPTION: cl=0 at that point, so BL = name_len + 12 = name_len + 0Ch
    # Then ROL EBX,0Ch and ROR EAX,14h must be equal
    # This means EBX == EAX, i.e., ROL(name_len+12, 12) == ROR(serial_len, 20)
    # ROR(x,20) == ROL(x,12), so ROL(name_len+12,12) == ROL(serial_len,12)
    # => name_len + 12 == serial_len
    # ASSUMPTION: serial length = name_len + 12 ... but writeup says 12 chars total
    # Actually writeup says serial length shall be 0Ch (12). Let's use 12 fixed:
    # From writeup: 'step over it we knew that the number of SN shall be 0Ch (12)'
    if serial_len != 12:
        return False
    
    # Check 4th char is '-'
    if serial_bytes[3:4] != b'-':
        return False
    
    # Check sum of first 3 chars == 0xA8
    s = (serial_bytes[0] + serial_bytes[1] + serial_bytes[2]) & 0xFF
    if s != 0xA8:
        return False
    
    # Compute expected suffix (8 chars after the '-')
    expected_suffix = compute_serial_suffix(name_bytes)
    actual_suffix = serial[4:12]
    
    # The check is XOR BYTE PTR DS:[EAX+403816], CL then JNZ badboy
    # 403816 is szSerial+4 (the chars after the dash)
    # So serial[4+i] XOR expected_char[i] must == 0, i.e. they must be equal
    if actual_suffix != expected_suffix:
        return False
    
    return True


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    name_bytes = name.encode('ascii', errors='replace')
    name_len = len(name_bytes)
    
    if name_len < 2 or name_len > 32:
        raise ValueError('Name length must be between 2 and 32 characters')
    
    # Build prefix: 3 chars that sum to 0xA8 = 168
    # Simple choice: '11F' = 0x31+0x31+0x46 = 49+49+70 = 168
    prefix = '11F'
    assert (ord('1') + ord('1') + ord('F')) == 0xA8
    
    suffix = compute_serial_suffix(name_bytes)
    
    serial = prefix + '-' + suffix
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
