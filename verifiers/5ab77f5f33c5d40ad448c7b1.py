import struct
import ctypes

# CRC32-like function (Sub401315)
def sub401315(data: bytes) -> int:
    edx = 0xFFFFFFFF
    for byte in data:
        al = byte ^ (edx & 0xFF)
        ebx = al & 0xFF
        for _ in range(8):
            if ebx & 1:
                ebx >>= 1
                ebx ^= 0xEDB88320
            else:
                ebx >>= 1
        edx = (edx >> 8) ^ ebx
    result = (~edx) & 0xFFFFFFFF
    return result


def rol32(val, count):
    val &= 0xFFFFFFFF
    count %= 32
    return ((val << count) | (val >> (32 - count))) & 0xFFFFFFFF


# Sub40126A: fills buffer1 with 4 DWORDs (16 bytes)
def sub40126A(pName: bytes, name_length: int) -> list:
    """Returns list of 4 DWORDs (buffer1 as bytes, 16 bytes total)"""
    buffer1 = []
    esi_offset = 0
    ecx = 0
    ebx_len = name_length
    while ecx != 4:
        data = pName[esi_offset:]
        crc = sub401315(data[:ebx_len])
        val = (crc ^ ebx_len) & 0xFFFFFFFF
        val = rol32(val, 3)
        buffer1.append(val)
        esi_offset += 1
        ecx += 1
        ebx_len -= 1
    return buffer1  # list of 4 DWORDs


def get_dword(buf2: int, buf1_byte: int, name_length: int) -> int:
    """
    buf2: DWORD
    buf1_byte: one byte from buffer1 (movzx ebx, byte ptr [esi])
    name_length: int
    """
    eax = buf2 ^ buf1_byte
    eax &= 0xFFFFFFFF
    # bswap
    eax = struct.unpack('<I', struct.pack('>I', eax))[0]
    # rol 4
    eax = rol32(eax, 4)
    eax = (eax + name_length) & 0xFFFFFFFF
    eax = eax ^ buf2
    eax &= 0xFFFFFFFF
    return eax


def zero_pad(s: str, length: int) -> str:
    """Pad string with leading zeros until len == length"""
    while len(s) != length:
        s = '0' + s
    return s


def keygen(name: str) -> str:
    name_bytes = name.encode('ascii')
    name_length = len(name_bytes)

    # Validate
    if name_length < 4:
        raise ValueError("Name too short (min 4 chars)")
    if name_length > 0x28:
        raise ValueError("Name too long (max 40 chars)")

    # First part: compute buffer2
    # namebuf = first 4 bytes of name as DWORD (little-endian)
    orig = struct.unpack('<I', name_bytes[:4])[0]
    namebuf = orig

    # First loop iteration (esi=1, edi=1):
    # while esi != 0: invoke Sub401315 on namebuf (1 byte), add to namebuf; dec esi
    # Since esi starts at 1, we do exactly one iteration:
    nb_bytes = struct.pack('<I', namebuf)[:1]  # 1 byte
    crc = sub401315(nb_bytes)
    namebuf = (namebuf + crc) & 0xFFFFFFFF
    eax_after_while = crc

    # .if edi == 1 branch:
    #   esi = eax & 0xFFFFFF - 0xF0000; dec edi; jmp begin
    esi = (eax_after_while & 0xFFFFFF) - 0xF0000
    esi &= 0xFFFFFFFF  # treat as unsigned 32-bit (could be negative, becomes large)

    # Second outer iteration (edi==0 now):
    # while esi != 0: Sub401315 on namebuf (1 byte), add to namebuf; dec esi
    # This loops esi times
    # ASSUMPTION: esi is treated as unsigned 32-bit; if it wrapped negative it could be huge.
    # We treat esi as a signed 32-bit integer to handle negative case (0 iterations).
    esi_signed = ctypes.c_int32(esi).value
    if esi_signed < 0:
        esi = 0  # loop doesn't execute if esi is negative (0 treated as stop)
    # Actually in x86, .while esi != 0 checks zero flag; if esi was computed negative (as 32-bit)
    # it would still be != 0, so we keep as unsigned and loop esi times mod 2^32... 
    # ASSUMPTION: In practice for short names esi will be a small positive number; trust it.
    # Re-check: esi = (crc & 0xFFFFFF) - 0xF0000. Max crc & 0xFFFFFF = 0xFFFFFF.
    # So max esi = 0xFFFFFF - 0xF0000 = 0xFFFFF (about 1M). Min = 0 - 0xF0000 (negative -> wrap)
    # ASSUMPTION: we run the loop esi_unsigned times with namebuf updated each iteration.
    esi_unsigned = esi & 0xFFFFFFFF
    last_crc = eax_after_while
    for _ in range(esi_unsigned):
        nb_bytes = struct.pack('<I', namebuf)[:1]
        crc = sub401315(nb_bytes)
        namebuf = (namebuf + crc) & 0xFFFFFFFF
        last_crc = crc

    # After loops, eax = last crc from inner loop (or eax_after_while if esi_unsigned==0)
    # Actually re-reading: after the .while, eax is not reassigned before mov buffer2,eax
    # The last eax from Sub401315 call inside the while is stored.
    # If esi_unsigned == 0, the while doesn't execute, eax stays as set after .if edi==1 block.
    # After .if block, control goes back to begin: then .while esi != 0 with esi now 0 -> skip.
    # Then eax = last Sub401315 result. But if loop didn't run, eax is still eax_after_while.
    buffer2 = last_crc

    # Reset namebuf to orig for Sub40126A
    # Sub40126A uses pName (the actual name bytes) and name_length
    buffer1_dwords = sub40126A(name_bytes, name_length)

    # Build serial: iterate 4 times (ecx += 4 each time, stops at 16)
    # Each iteration takes one byte from buffer1 (byte ptr [esi], esi increments each time)
    # So we use bytes 0..3 of buffer1 (the 4 DWORDs = 16 bytes, but only 4 bytes used?)
    # ASSUMPTION: ecx goes 0,4,8,12 -> 4 iterations; esi increments by 1 each time (byte ptr)
    # So we use bytes 0,1,2,3 from buffer1 (first 4 bytes of the 16-byte buffer)
    buffer1_bytes = b''
    for dw in buffer1_dwords:
        buffer1_bytes += struct.pack('<I', dw)
    # buffer1_bytes is 16 bytes; esi starts at buffer1[0] and increments by 1 each iteration
    # ecx starts at 0, increments by 4, stops when ecx==16 -> 4 iterations
    # So indices: 0, 1, 2, 3

    serial = ''
    for i in range(4):
        b1_byte = buffer1_bytes[i]
        val = get_dword(buffer2, b1_byte, name_length)
        hex_str = format(val, 'X')  # uppercase hex
        if len(hex_str) < 8:
            hex_str = zero_pad(hex_str, 8)
        serial += hex_str

    return serial


def verify(name: str, serial: str) -> bool:
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
    except Exception:
        return False



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
