import struct

def _rol32(value, count):
    """Rotate left 32-bit value by count bits."""
    value &= 0xFFFFFFFF
    return ((value << count) | (value >> (32 - count))) & 0xFFFFFFFF

def _compute_serial(name):
    """
    Reconstruct the serial from the name.

    Step 1 (loop, ecx = 0..3):
      For ecx in 0..3:
        eax = DWORD at name[ecx]   (little-endian)
        ebx = DWORD at name[ecx+1] (little-endian)
        temp = rol32(eax XOR ebx, 2)
        store temp as DWORD at buf1[ecx*4]  (buf1 is 4*4 = 16 bytes)

    Step 2 (loop, ecx = 0..0x10 exclusive i.e. 0..16):
      For ecx in 0..16:
        al = buf1[ecx]
        bl = buf1[ecx+1]
        buf1[ecx] = al XOR bl XOR 0x07
      (ecx == 0x11 = 17 stops, so 0..16 inclusive => indices 0-16, 17 bytes processed)

    Step 3 (permutation):
      edi points to buf1 (0-indexed as edi[0..16])
      esi points to output buffer
      A series of byte copies: esi[n] = edi[m]
      Then some bytes are overwritten with fixed values:
        esi[0x20] = 0x43 ('C')
        esi[0x1D] = 0x75 ('u')  (but later overwritten? check order)
        esi[0x1F] = 0x54 ('T')
        esi[0x1E] = 0x65 ('e')
    """
    # Pad name to at least 17 bytes for safety
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    # Pad to at least 17 bytes
    nb = bytearray(name_bytes.ljust(20, b'\x00'))

    # Step 1: 4 iterations, build buf1 (raw 16 bytes from 4 DWORDs)
    buf1 = bytearray(20)  # needs at least 17+1 bytes for step 2
    for ecx in range(4):
        eax = struct.unpack_from('<I', nb, ecx)[0]
        ebx = struct.unpack_from('<I', nb, ecx + 1)[0]
        val = _rol32(eax ^ ebx, 2)
        struct.pack_into('<I', buf1, ecx * 4, val)

    # Step 2: xor adjacent bytes XOR 0x07, for ecx in 0..16 (17 iterations)
    # Note: modifies buf1 in-place, each byte = buf1[ecx] XOR buf1[ecx+1] XOR 0x07
    for ecx in range(17):  # 0x00 to 0x10 inclusive
        al = buf1[ecx]
        bl = buf1[ecx + 1]
        buf1[ecx] = (al ^ bl ^ 0x07) & 0xFF

    # Step 3: permutation
    # edi = buf1 (1-indexed in asm as edi+1 .. edi+0xF)
    # esi = output (1-indexed in asm as esi+1 .. esi+0x20)
    # Both esi and edi are decremented by 1 before use, so effectively:
    # out[n-1] = buf1[m-1]  where the asm says esi+n = edi+m
    # We'll use 0-based indexing: out[n] = buf1[m]

    out = bytearray(0x21 + 1)  # needs up to index 0x20 = 32

    # Permutation table from disassembly (edi offset -> esi offset, 1-based in asm)
    # We subtract 1 from both since esi and edi are pre-decremented
    perm = [
        (0x01, 0x02),
        (0x02, 0x03),
        (0x0F, 0x01),
        (0x03, 0x0F),
        (0x07, 0x09),
        (0x04, 0x07),
        (0x06, 0x05),
        (0x09, 0x04),
        (0x0A, 0x06),
        (0x05, 0x0C),
        (0x08, 0x0A),
        (0x0B, 0x08),
        (0x0D, 0x0B),
        (0x0C, 0x0D),
        (0x0E, 0x0E),
        (0x02, 0x11),
        (0x03, 0x10),
        (0x06, 0x15),
        (0x05, 0x19),
        (0x07, 0x13),
        (0x01, 0x16),
        (0x04, 0x12),
        (0x0A, 0x17),
        (0x0B, 0x14),
        (0x08, 0x1A),
        (0x09, 0x18),
        (0x0E, 0x1B),
        (0x0F, 0x1D),
        (0x0C, 0x0F),
        # ASSUMPTION: 0x0D -> 0x1C from asm at 00401298
        (0x0D, 0x1C),
    ]

    # Apply permutation: out[esi_offset - 1] = buf1[edi_offset - 1]
    # Both esi and edi are pre-decremented by 1 in asm (dec esi; dec edi)
    # So asm edi+1 = buf1[0], asm esi+1 = out[0]
    for (edi_off, esi_off) in perm:
        out[esi_off - 1] = buf1[edi_off - 1]

    # Fixed bytes from asm (esi+offset, esi is pre-decremented so esi+n -> out[n-1])
    # :0040129E C6462043   mov [esi+20], 43  -> out[0x1F] = 0x43 'C'
    # :004012A2 C6461D75   mov [esi+1D], 75  -> out[0x1C] = 0x75 'u'
    # :004012A6 C6461F54   mov [esi+1F], 54  -> out[0x1E] = 0x54 'T'
    # :004012AA C6461E65   mov [esi+1E], 65  -> out[0x1D] = 0x65 'e'
    # ASSUMPTION: esi was pre-decremented by 1, so esi+0x20 = out[0x1F], etc.
    out[0x1F] = 0x43  # 'C'
    out[0x1C] = 0x75  # 'u'
    out[0x1E] = 0x54  # 'T'
    out[0x1D] = 0x65  # 'e'

    # The serial appears to be 0x21 bytes (indices 0..0x20), null-terminated at 0x20
    # From the example the serial ends with 'C' at position 0x1F (0-based) and
    # the known serial for HackeRMaN ends with 'ueTC'
    # Trim to valid bytes
    serial_bytes = bytes(out[:0x20])
    return serial_bytes


def keygen(name):
    """Generate serial for given name."""
    raw = _compute_serial(name)
    # Return as latin-1 string (may contain non-printable bytes)
    return raw.decode('latin-1').rstrip('\x00')


def verify(name, serial):
    """
    Verify serial against name.
    The crackme computes the correct serial from the name and compares it
    to what the user entered using lstrlenA + loop comparison.
    """
    expected = keygen(name)
    return serial == expected



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
