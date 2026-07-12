import struct

def _bswap(x):
    """Emulate x86 BSWAP on a 32-bit value."""
    x &= 0xFFFFFFFF
    return struct.unpack('<I', struct.pack('>I', x))[0]

def _u32(x):
    return x & 0xFFFFFFFF

def compute_serial(name: str) -> str:
    """
    Compute the serial for a given name.
    Name must be at least 5 characters.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters.")

    name_bytes = name.encode('latin-1')

    # EAX = first 4 bytes of name as little-endian DWORD
    # Pad to at least 4 bytes
    padded = name_bytes + b'\x00' * 4
    eax = struct.unpack_from('<I', padded, 0)[0]

    # Sum bytes from name[4] onwards until null (i.e., name[4:])
    dl = 0
    for b in name_bytes[4:]:
        dl = (dl + b) & 0xFF

    # Build ECX from DL
    ecx = 0
    # xor ecx, ecx
    ecx = 0
    # mov cl, dl
    ecx = (ecx & 0xFFFFFF00) | dl
    # mov ch, dl
    ecx = (ecx & 0xFFFF00FF) | (dl << 8)
    # bswap ecx
    ecx = _bswap(ecx)
    # mov cl, dl
    ecx = (ecx & 0xFFFFFF00) | dl
    # mov ch, dl
    ecx = (ecx & 0xFFFF00FF) | (dl << 8)

    # xor ecx, eax
    ecx = _u32(ecx ^ eax)
    # bswap ecx
    ecx = _bswap(ecx)
    # add ecx, 03022006h
    ecx = _u32(ecx + 0x03022006)
    # bswap ecx
    ecx = _bswap(ecx)
    # sub ecx, DEADC0DEh
    ecx = _u32(ecx - 0xDEADC0DE)
    # bswap ecx
    ecx = _bswap(ecx)
    # inc cl
    cl = (ecx & 0xFF)
    cl = (cl + 1) & 0xFF
    ecx = (ecx & 0xFFFFFF00) | cl
    # inc ch
    ch = (ecx >> 8) & 0xFF
    ch = (ch + 1) & 0xFF
    ecx = (ecx & 0xFFFF00FF) | (ch << 8)
    # bswap ecx
    ecx = _bswap(ecx)
    # dec cl
    cl = ecx & 0xFF
    cl = (cl - 1) & 0xFF
    ecx = (ecx & 0xFFFFFF00) | cl
    # dec ch
    ch = (ecx >> 8) & 0xFF
    ch = (ch - 1) & 0xFF
    ecx = (ecx & 0xFFFF00FF) | (ch << 8)
    # bswap ecx
    ecx = _bswap(ecx)
    # xor ecx, EDB88320h
    ecx = _u32(ecx ^ 0xEDB88320)
    # bswap ecx
    ecx = _bswap(ecx)
    # add ecx, D76AA478h
    ecx = _u32(ecx + 0xD76AA478)
    # bswap ecx
    ecx = _bswap(ecx)
    # sub ecx, B00BFACEh
    ecx = _u32(ecx - 0xB00BFACE)
    # bswap ecx
    ecx = _bswap(ecx)
    # add ecx, BADBEEFh
    ecx = _u32(ecx + 0x0BADBEEF)
    # bswap ecx
    ecx = _bswap(ecx)
    # inc ecx
    ecx = _u32(ecx + 1)
    # bswap ecx
    ecx = _bswap(ecx)
    # dec ecx
    ecx = _u32(ecx - 1)
    # bswap ecx
    ecx = _bswap(ecx)
    # add ecx, eax
    ecx = _u32(ecx + eax)
    # bswap ecx
    ecx = _bswap(ecx)
    # inc cx  (16-bit increment)
    cx = (ecx & 0xFFFF)
    cx = (cx + 1) & 0xFFFF
    ecx = (ecx & 0xFFFF0000) | cx
    # bswap ecx
    ecx = _bswap(ecx)
    # inc cx
    cx = (ecx & 0xFFFF)
    cx = (cx + 1) & 0xFFFF
    ecx = (ecx & 0xFFFF0000) | cx
    # bswap ecx
    ecx = _bswap(ecx)
    # bswap ecx  (double bswap = no-op net effect, but done twice in source)
    ecx = _bswap(ecx)

    sum1 = ecx

    # Now apply the per-byte transformation to produce the serial
    # Byte 0 (lowest byte of sum1): sub 0xEF, xor 0xCD
    b0 = sum1 & 0xFF
    b0 = _u8(b0 - 0xEF)
    b0 = b0 ^ 0xCD

    # Byte 1 (bits 8-15): sub 0xAB, xor 0x90
    b1 = (sum1 >> 8) & 0xFF
    b1 = _u8(b1 - 0xAB)
    b1 = b1 ^ 0x90

    # Byte 2 (bits 16-23): sub 0x78, xor 0x56
    b2 = (sum1 >> 16) & 0xFF
    b2 = _u8(b2 - 0x78)
    b2 = b2 ^ 0x56

    # Byte 3 (bits 24-31): sub 0x34, xor 0x12
    b3 = (sum1 >> 24) & 0xFF
    b3 = _u8(b3 - 0x34)
    b3 = b3 ^ 0x12

    # Build EDX: b0 placed first (shl edx,8 chain), then bswap edx
    # From the keygen.c and MASM source:
    # edx = b0; shl edx,8; add edx, b1; shl edx,8; add edx, b2; shl edx,8; add edx, b3
    # Then bswap edx
    edx = b0
    edx = (edx << 8) & 0xFFFFFFFF
    edx = _u32(edx + b1)
    edx = (edx << 8) & 0xFFFFFFFF
    edx = _u32(edx + b2)
    edx = (edx << 8) & 0xFFFFFFFF
    edx = _u32(edx + b3)
    edx = _bswap(edx)

    return '%08X' % edx


def _u8(x):
    return x & 0xFF


def verify(name: str, serial: str) -> bool:
    if len(name) < 5:
        return False
    if len(serial) != 8:
        return False
    # serial must be valid hex
    try:
        int(serial, 16)
    except ValueError:
        return False
    expected = compute_serial(name)
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    return compute_serial(name)



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
