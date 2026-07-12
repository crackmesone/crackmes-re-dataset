import struct

def calc_hash(name: str) -> int:
    """Replicates the CalcHash / GetMagicNameHash assembly routine."""
    # name must be > 5 chars (length check is >= 6)
    name_bytes = name.encode('latin-1')

    # eax = pointer to name buffer
    # The assembly uses [eax] as a 4-byte DWORD from the start of the name,
    # and [eax+4] onwards as the bytes to sum.
    # [eax] = first 4 bytes as little-endian DWORD
    if len(name_bytes) < 4:
        first_dword = 0
        for i, b in enumerate(name_bytes):
            first_dword |= b << (i * 8)
    else:
        first_dword = struct.unpack_from('<I', name_bytes, 0)[0]

    # Sum bytes starting at offset 4, stop before null terminator
    # (name_bytes[4:])
    dl = 0
    for b in name_bytes[4:]:
        dl = (dl + b) & 0xFF

    # Build ecx from dl
    ecx = 0
    ecx = (ecx & ~0xFF) | (dl & 0xFF)           # mov cl, dl
    ecx = (ecx & ~0xFF00) | ((dl & 0xFF) << 8)  # mov ch, dl
    # bswap ecx
    ecx = ecx & 0xFFFFFFFF
    ecx = struct.unpack('<I', struct.pack('>I', ecx))[0]
    ecx = (ecx & ~0xFF) | (dl & 0xFF)           # mov cl, dl
    ecx = (ecx & ~0xFF00) | ((dl & 0xFF) << 8)  # mov ch, dl

    eax = first_dword

    # xor ecx, eax
    ecx = (ecx ^ eax) & 0xFFFFFFFF

    def bswap(v):
        v = v & 0xFFFFFFFF
        return struct.unpack('<I', struct.pack('>I', v))[0]

    ecx = bswap(ecx)
    ecx = (ecx + 0x3022006) & 0xFFFFFFFF
    ecx = bswap(ecx)
    ecx = (ecx - 0xDEADC0DE) & 0xFFFFFFFF
    ecx = bswap(ecx)

    # inc cl, inc ch
    cl = (ecx & 0xFF)
    ch = (ecx >> 8) & 0xFF
    cl = (cl + 1) & 0xFF
    ch = (ch + 1) & 0xFF
    ecx = (ecx & 0xFFFF0000) | (ch << 8) | cl

    ecx = bswap(ecx)

    # dec cl, dec ch
    cl = (ecx & 0xFF)
    ch = (ecx >> 8) & 0xFF
    cl = (cl - 1) & 0xFF
    ch = (ch - 1) & 0xFF
    ecx = (ecx & 0xFFFF0000) | (ch << 8) | cl

    ecx = bswap(ecx)

    ecx = (ecx ^ 0xEDB88320) & 0xFFFFFFFF
    ecx = bswap(ecx)
    ecx = (ecx + 0xD76AA478) & 0xFFFFFFFF
    ecx = bswap(ecx)
    ecx = (ecx - 0xB00BFACE) & 0xFFFFFFFF
    ecx = bswap(ecx)
    ecx = (ecx + 0x0BADBEEF) & 0xFFFFFFFF
    ecx = bswap(ecx)

    # inc ecx
    ecx = (ecx + 1) & 0xFFFFFFFF
    ecx = bswap(ecx)
    # dec ecx
    ecx = (ecx - 1) & 0xFFFFFFFF
    ecx = bswap(ecx)

    # add ecx, eax
    ecx = (ecx + eax) & 0xFFFFFFFF
    ecx = bswap(ecx)

    # inc cx
    cx = (ecx & 0xFFFF)
    cx = (cx + 1) & 0xFFFF
    ecx = (ecx & 0xFFFF0000) | cx
    ecx = bswap(ecx)

    # inc cx
    cx = (ecx & 0xFFFF)
    cx = (cx + 1) & 0xFFFF
    ecx = (ecx & 0xFFFF0000) | cx
    ecx = bswap(ecx)

    # bswap ecx (two consecutive bswaps cancel out, but the asm has them)
    ecx = bswap(ecx)

    # Store ecx as the temp value
    tmp = ecx & 0xFFFFFFFF

    # Now the per-byte transformation section
    # Byte 0 (lowest byte of tmp)
    b0 = tmp & 0xFF
    b0 = (b0 - 0xEF) & 0xFF
    b0 = (b0 ^ 0xCD) & 0xFF

    # Byte 1
    b1 = (tmp >> 8) & 0xFF
    b1 = (b1 - 0xAB) & 0xFF
    b1 = (b1 ^ 0x90) & 0xFF

    # Byte 2
    b2 = (tmp >> 16) & 0xFF
    b2 = (b2 - 0x78) & 0xFF
    b2 = (b2 ^ 0x56) & 0xFF

    # Byte 3
    b3 = (tmp >> 24) & 0xFF
    b3 = (b3 - 0x34) & 0xFF
    b3 = (b3 ^ 0x12) & 0xFF

    # edx is built as: edx = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3,
    # then bswap edx => result = b0 | (b1<<8) | (b2<<16) | (b3<<24)
    # Let's trace the asm carefully:
    # edx = b0; edx <<= 8
    # edx += b1; edx <<= 8
    # edx += b2; edx <<= 8
    # edx += b3
    # => edx = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
    # bswap edx => byte-reverse => b3 | (b2 << 8) | (b1 << 16) | (b0 << 24)
    edx = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
    edx = bswap(edx)

    return edx & 0xFFFFFFFF


def verify(name: str, serial: str) -> bool:
    if len(name) <= 5:
        return False
    expected = 'STH-' + format(calc_hash(name), '08X').upper()
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    if len(name) <= 5:
        raise ValueError('Name must be longer than 5 characters')
    return 'STH-' + format(calc_hash(name), '08X').upper()



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
