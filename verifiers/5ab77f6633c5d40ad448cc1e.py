import struct

def compute_serial():
    """
    The crackme uses LEA (not MOV), so it operates on the fixed memory
    ADDRESSES of the Name and Company buffers, not the actual string contents.
    Fixed addresses:
      Name    -> 0x0040323E
      Company -> 0x00403242
    The computation is entirely address-based, so the serial is constant
    regardless of what is typed into the Name/Company fields.
    """
    # Fixed memory addresses used by the crackme
    name_addr    = 0x0040323E
    company_addr = 0x00403242

    # Simulate x86 32-bit arithmetic (truncate to 32 bits)
    MASK32 = 0xFFFFFFFF

    eax = name_addr
    ebx = company_addr

    # xor eax, 45
    eax = (eax ^ 0x45) & MASK32
    # mov ecx, 00007612 ; mul ecx  (EAX = EAX * ECX, lower 32 bits)
    ecx = 0x00007612
    eax = (eax * ecx) & MASK32

    # xor ebx, 45
    ebx = (ebx ^ 0x45) & MASK32
    # push eax  (save eax)
    saved_eax = eax
    # mov eax, ebx
    eax = ebx
    # xor ecx, ecx ; mov ecx, 00007357 ; mul ecx
    ecx = 0x00007357
    eax = (eax * ecx) & MASK32
    # mov ebx, eax
    ebx = eax
    # pop eax
    eax = saved_eax

    # xor eax, 0000029A
    eax = (eax ^ 0x0000029A) & MASK32
    # xor ebx, 0000029A
    ebx = (ebx ^ 0x0000029A) & MASK32

    # mov edx, 00000045 ; mul edx  (EAX = EAX * 0x45)
    edx = 0x00000045
    eax = (eax * edx) & MASK32
    # push eax
    saved_eax2 = eax

    # xor edx, edx ; mov edx, 00000666
    edx = 0x00000666
    # mov eax, ebx ; mul edx
    eax = (ebx * edx) & MASK32
    # mov ebx, eax
    ebx = eax
    # pop eax
    eax = saved_eax2

    # add eax, ebx
    eax = (eax + ebx) & MASK32

    # xor eax, 03
    eax = (eax ^ 0x03) & MASK32

    # mov dword ptr [00403246], eax
    # The value stored at 00403246 is eax (4 bytes)
    # Next: mov dl, byte ptr [00403247]  <- byte 1 of the stored dword
    # xor dl, 03
    # mov byte ptr [00403247], dl
    # xor dword ptr [00403246], 02

    # Decompose eax into 4 bytes (little-endian)
    dword_bytes = list(struct.pack('<I', eax))

    # byte at offset [00403247] is byte index 1 (00403247 - 00403246 = 1)
    dword_bytes[1] ^= 0x03

    # Reassemble
    eax = struct.unpack('<I', bytes(dword_bytes))[0]

    # xor dword ptr [00403246], 02
    eax = (eax ^ 0x02) & MASK32

    return eax


COMPUTED_SERIAL = compute_serial()


def verify(name: str, serial: str) -> bool:
    """
    The crackme compares the first 4 bytes of the entered Serial string
    (interpreted as a little-endian 32-bit integer from raw bytes) against
    the computed constant value.

    The serial is stored as raw bytes in the dialog; the comparison is
    'cmp dword ptr [00403246], edx' where EDX = first 4 bytes of entered serial.

    We accept the serial either as:
      - A 4-byte raw string whose bytes match the DWORD, or
      - The hex string representation of the DWORD (e.g. '2F0F74DF' or 'DF740F2F').
    """
    # Try raw bytes comparison (the actual crackme approach)
    raw = serial.encode('latin-1') if isinstance(serial, str) else serial
    if len(raw) >= 4:
        edx = struct.unpack('<I', raw[:4])[0]
        if edx == COMPUTED_SERIAL:
            return True

    # Also accept the hex string of the little-endian bytes
    serial_hex = serial.strip().replace(' ', '').upper()
    expected_le_hex = ''.join(f'{b:02X}' for b in struct.pack('<I', COMPUTED_SERIAL))
    expected_be_hex = ''.join(f'{b:02X}' for b in struct.pack('>I', COMPUTED_SERIAL))
    if serial_hex in (expected_le_hex, expected_be_hex):
        return True

    return False


def keygen(name: str) -> str:
    """
    The serial is constant regardless of name/company.
    Returns the serial as a hex string of the 4 bytes (little-endian, as stored).
    The crackme author noted the correct serial bytes are: 2F 0F 74 DF
    """
    le_bytes = struct.pack('<I', COMPUTED_SERIAL)
    return ' '.join(f'{b:02X}' for b in le_bytes)



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
