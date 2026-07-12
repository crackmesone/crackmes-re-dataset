import socket
import struct

def get_computer_name():
    """Get the computer name (hostname) as used by Windows GetComputerName."""
    return socket.gethostname().upper()

def compute_computer_hash(computer_name):
    """
    Replicates the ComputerName proc in the keygen:
    Iterates over pairs of bytes from the computer name string.
    For each pair (al = byte[i], dl = byte[i+1]):
      ror al, 4
      not dl
      add al, dl  (8-bit addition)
      add ebx, eax  (eax = zero-extended al result)
      imul edx, eax (edx = edx * eax, 32-bit)
      add ecx, edx
      xchg edx, ebx
      advance esi by 2
    Then: bswap ebx; add ebx, ecx; return ebx
    """
    name_bytes = computer_name.encode('ascii') + b'\x00'  # null-terminated
    
    eax = 0
    edx = 0
    ebx = 0
    ecx = 0
    
    i = 0
    # Loop while word ptr [esi] != 0 (i.e., at least one of the two bytes is non-zero)
    while i + 1 < len(name_bytes):
        w = (name_bytes[i+1] << 8) | name_bytes[i]
        if w == 0:
            break
        
        al = name_bytes[i] & 0xFF
        dl = name_bytes[i+1] & 0xFF
        
        # ror al, 4
        al = ((al >> 4) | (al << 4)) & 0xFF
        # not dl
        dl = (~dl) & 0xFF
        # add al, dl (8-bit)
        al = (al + dl) & 0xFF
        # eax = zero-extended al
        eax = al
        # add ebx, eax
        ebx = (ebx + eax) & 0xFFFFFFFF
        # imul edx, eax  (edx = edx * eax, truncated to 32 bits)
        edx = (edx * eax) & 0xFFFFFFFF
        # add ecx, edx
        ecx = (ecx + edx) & 0xFFFFFFFF
        # xchg edx, ebx
        edx, ebx = ebx, edx
        
        i += 2
    
    # bswap ebx
    ebx_bytes = struct.pack('<I', ebx)
    ebx = struct.unpack('>I', ebx_bytes)[0]
    # add ebx, ecx
    ebx = (ebx + ecx) & 0xFFFFFFFF
    return ebx

def ror32(val, count):
    val &= 0xFFFFFFFF
    count &= 31
    return ((val >> count) | (val << (32 - count))) & 0xFFFFFFFF

def rol32(val, count):
    val &= 0xFFFFFFFF
    count &= 31
    return ((val << count) | (val >> (32 - count))) & 0xFFFFFFFF

def bswap32(val):
    val &= 0xFFFFFFFF
    return struct.unpack('<I', struct.pack('>I', val))[0]

def calculate_serial(name, computer_name=None):
    """
    Replicates CalculateSerialPart1.
    Returns the serial string.
    """
    if computer_name is None:
        computer_name = get_computer_name()
    
    dw_compu_hash = compute_computer_hash(computer_name)
    
    # 2nd part: iterate over name characters
    name_bytes = name.encode('ascii') + b'\x00'
    
    ebx = 0
    edx = 0
    ecx = 0x7FFF
    
    i = 0
    while i < len(name_bytes) and name_bytes[i] != 0:
        # mov bx, word ptr [esi]  => lower 16 bits of ebx = word at esi
        # But ebx is 32-bit; only bx (lower 16) is set by 'mov bx, ...'
        # The upper 16 bits of ebx remain from previous; but ebx is xor'd to 0 initially
        w = 0
        if i < len(name_bytes):
            w = name_bytes[i] & 0xFF
        if i + 1 < len(name_bytes):
            w |= (name_bytes[i+1] & 0xFF) << 8
        # mov bx, word ptr [esi]: sets lower 16 bits, clears upper 16 via movzx semantics?
        # Actually in x86, 'mov bx, ...' only updates the lower 16 bits of ebx.
        # But since ebx starts at 0 and after first iter we do operations below:
        # After each iteration, ebx could have upper bits set.
        # Let's track ebx carefully:
        # ebx upper 16 bits are preserved when doing 'mov bx, ...'
        # However, since the loop does: shl ebx,8 first which shifts ALL 32 bits,
        # the pattern is: ebx = (ebx & 0xFFFF0000) | w, then shl ebx,8
        # But initially ebx=0, so first iter: ebx = w, shl -> ebx = w<<8
        # Second iter: ebx's upper 16 come from prev; mov bx sets lower 16.
        # ASSUMPTION: upper 16 bits of ebx are not cleared between iterations.
        # We track the full 32-bit ebx.
        ebx = (ebx & 0xFFFF0000) | (w & 0xFFFF)
        # shl ebx, 8
        ebx = (ebx << 8) & 0xFFFFFFFF
        
        # mov eax, dwCompuHash; and eax, 0f8f800h
        eax = dw_compu_hash & 0xF8F800
        
        # xor ebx, eax
        ebx ^= eax
        ebx &= 0xFFFFFFFF
        
        # add ebx, 06c6f6ch
        ebx = (ebx + 0x6C6F6C) & 0xFFFFFFFF
        
        # xor ebx, 010101010h
        ebx ^= 0x10101010
        ebx &= 0xFFFFFFFF
        
        # add edx, ebx
        edx = (edx + ebx) & 0xFFFFFFFF
        
        # add ecx, ebx
        ecx = (ecx + ebx) & 0xFFFFFFFF
        
        # sub ecx, 02d3d2dh
        ecx = (ecx - 0x2D3D2D) & 0xFFFFFFFF
        
        # imul ecx, ecx, 8
        ecx = (ecx * 8) & 0xFFFFFFFF
        
        # add ecx, eax
        ecx = (ecx + eax) & 0xFFFFFFFF
        
        i += 1
    
    # 3rd part
    ebx2 = 0  # edi
    esi2 = 0  # esi (local)
    eax2 = 0x10  # 16 iterations
    edi = 0
    esi3 = 0
    
    count = 0x10
    edi = 0
    esi3 = 0
    
    for _ in range(count):
        # add edi, ecx
        edi = (edi + ecx) & 0xFFFFFFFF
        # add esi, edx
        esi3 = (esi3 + edx) & 0xFFFFFFFF
        # bswap edi
        edi = bswap32(edi)
        # bswap esi
        esi3 = bswap32(esi3)
        # rol edi, 10h
        edi = rol32(edi, 0x10)
        # ror esi, 10h
        esi3 = ror32(esi3, 0x10)
    
    # wsprintf with format "%08X-%08X-%08X-%08X", ecx, edx, edi, esi
    serial = "%08X-%08X-%08X-%08X" % (ecx & 0xFFFFFFFF, edx & 0xFFFFFFFF, edi & 0xFFFFFFFF, esi3 & 0xFFFFFFFF)
    return serial

def verify(name, serial, computer_name=None):
    """Verify a name/serial pair. Note: serial is machine-dependent."""
    expected = calculate_serial(name, computer_name)
    return serial.upper() == expected.upper()

def keygen(name, computer_name=None):
    """Generate a valid serial for the given name on this machine."""
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")
    if len(name) > 30:
        raise ValueError("Name must be at most 30 characters")
    return calculate_serial(name, computer_name)


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
