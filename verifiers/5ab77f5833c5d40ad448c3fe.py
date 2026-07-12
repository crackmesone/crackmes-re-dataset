def keygen(name: str) -> bytes:
    """
    Generates the key file content for a given name/signature.
    The key file is 0x100 (256) bytes long.
    Layout:
      - name (null-terminated)
      - buffer2 (computed bytes, null-terminated)
      - buffer3 (computed bytes, null-terminated)
      - ... padding ...
      - byte 0x90 at offset 255
    
    Algorithm (from the assembly in the keygen source):
    For each index i (0-based) in the name (length n):
      ah = name[i]
      al = 0x30 + i
      cl = n - i  (ecx counts down from n to 1)
      ah = ah - cl
      ah = ah XOR al
      al = ROL(al, cl & 0x1F)
      ah = ROR(ah, cl & 0x1F)
      buffer2[i] = ah
      buffer3[i] = al
    """
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters")
    if len(name) > 85:
        raise ValueError("Name must be at most 85 characters")

    n = len(name)
    buffer2 = bytearray()
    buffer3 = bytearray()

    for i in range(n):
        cl = n - i  # ecx counts down
        # All ops on 8-bit values
        ah = name[i] if isinstance(name[i], int) else ord(name[i])
        al = (0x30 + i) & 0xFF
        # ah = ah - cl
        ah = (ah - cl) & 0xFF
        # ah = ah XOR al
        ah = (ah ^ al) & 0xFF
        # al = ROL(al, cl & 0x1F)
        rot = cl & 0x1F
        al = ((al << rot) | (al >> (8 - rot))) & 0xFF
        # ah = ROR(ah, cl & 0x1F)
        ah = ((ah >> rot) | (ah << (8 - rot))) & 0xFF
        buffer2.append(ah)
        buffer3.append(al)

    # Build the 256-byte key file
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    filebuf = bytearray(0x100)
    pos = 0
    # Write name (null-terminated)
    for b in name_bytes:
        filebuf[pos] = b
        pos += 1
    pos += 1  # null terminator (already 0)
    # The assembly does: after name copy, inc edi; mov dword ptr [edi], 0
    # So there's an extra null dword written after the null terminator
    # Then buffer2 is appended
    # ASSUMPTION: the exact gap between name and buffer2 may vary by alignment/edi increment
    # Based on the ASM: after name movsb, edi points past the null, then inc edi, then dword 0 written
    # So there's 1 extra null byte, then 4 null bytes from the dword = effectively a gap
    # For simplicity: name\0\0[4 null bytes]buffer2\0buffer3\0...0x90 at [255]
    pos += 4  # for the dword ptr [edi]=0 written after the extra inc edi
    # Write buffer2 (null-terminated)
    for b in buffer2:
        if pos < 255:
            filebuf[pos] = b
            pos += 1
    pos += 1  # null terminator
    # Write buffer3 (null-terminated)
    for b in buffer3:
        if pos < 255:
            filebuf[pos] = b
            pos += 1
    pos += 1  # null terminator
    # Set last byte to 0x90
    filebuf[255] = 0x90
    return bytes(filebuf)


def verify(name: str, serial: bytes) -> bool:
    """
    Verifies a key file against a name.
    The key file must be exactly 0x100 bytes, last byte must be 0x90,
    and must contain the computed buffer2 and buffer3 values.
    """
    # ASSUMPTION: The crackme reads the key file, checks size <= 0x100,
    # then checks last byte == 0x90, then verifies computed values.
    # We reconstruct the expected key file and compare.
    if len(serial) != 0x100:
        return False
    if serial[255] != 0x90:
        return False
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
