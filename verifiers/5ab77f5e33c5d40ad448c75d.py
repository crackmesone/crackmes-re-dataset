# Reverse-engineered from the NH.ASM keygen for the 'cycle' crackme by cW
# The keygen reads the name, tiles it into a 256-byte buffer at nm+100h,
# then computes parts of the key from those bytes.
#
# Key layout (17 bytes as ASCII hex string + '$' sentinel):
#   s[0..3]  = eax = nm100[0..3] XOR 0x030C1501  (first 4 bytes of tiled name)
#   s[4..7]  = ebx = nm100[4..7] XOR 0x04000000  (next 4 bytes of tiled name)
#   s[8..11] = 'xxxx'  # ASSUMPTION: not computed in the keygen snippet shown
#   s[12..15]= eax = (nm100[8..11] XOR nm100[12..15] XOR 0xFEDCBAA6)
#                     OR  0x40404040
#                     AND 0x77777777
#                     XOR 0x34333231
# The key is printed as the hex string of those dwords.
#
# NOTE: The 'Shitproc' (Shit) and 'Recursive' procedures mentioned in the
# text-mode writeup describe the *validation* side which we only partially
# understand. The keygen side is clearer from NH.ASM.

import struct

def _tile_name(name: str) -> bytes:
    """Replicate the name into a 256-byte buffer as the asm does:
       rep movsb cx times, 16 times over, starting at offset 0 in the buffer.
       The asm uses nm+100h as destination, nm+2 as source, count = len(name).
    """
    buf = bytearray(256)
    name_bytes = name.encode('ascii', errors='replace')
    n = len(name_bytes)
    if n == 0:
        return bytes(buf)
    pos = 0
    for _ in range(16):
        for b in name_bytes:
            if pos >= 256:
                break
            buf[pos] = b
            pos += 1
        if pos >= 256:
            break
    return bytes(buf)


def keygen(name: str) -> str:
    if len(name) < 2:
        raise ValueError("Name too short (need at least 2 chars)")

    buf = _tile_name(name)

    # s[0..3]: eax = nm100[0..3] XOR 0x030C1501
    eax = struct.unpack_from('<I', buf, 0)[0]
    eax ^= 0x030C1501
    eax &= 0xFFFFFFFF

    # s[4..7]: ebx = nm100[4..7] XOR 0x04000000
    ebx = struct.unpack_from('<I', buf, 4)[0]
    ebx ^= 0x04000000
    ebx &= 0xFFFFFFFF

    # s[8..11]: not computed in the keygen snippet; the asm leaves 'xxxx' there
    # ASSUMPTION: this part of the key is literal 'xxxx' or zeros — unknown
    s8_11 = 'xxxx'

    # s[12..15]: complex expression
    v1 = struct.unpack_from('<I', buf, 8)[0]
    v2 = struct.unpack_from('<I', buf, 12)[0]
    eax2 = (v1 ^ v2 ^ 0xFEDCBAA6) & 0xFFFFFFFF
    eax2 = (eax2 | 0x40404040) & 0xFFFFFFFF
    eax2 = (eax2 & 0x77777777) & 0xFFFFFFFF
    eax2 = (eax2 ^ 0x34333231) & 0xFFFFFFFF

    # Format: each dword as 8 hex chars (little-endian bytes printed as hex)
    def dword_to_hexstr(val):
        # Store as little-endian bytes, then hex-encode
        b = struct.pack('<I', val)
        return b.hex().upper()

    part1 = dword_to_hexstr(eax)    # s[0..3]
    part2 = dword_to_hexstr(ebx)    # s[4..7]
    part3 = s8_11                   # s[8..11] ASSUMPTION: literal
    part4 = dword_to_hexstr(eax2)   # s[12..15]

    return part1 + part2 + part3 + part4


def verify(name: str, serial: str) -> bool:
    """Verify by regenerating the key and comparing.
    ASSUMPTION: The crackme checks the serial against the generated key;
    the exact validation path (Recursive + Shitproc) is only partially
    described. We compare against the keygen output.
    """
    if len(name) < 2:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
    # Compare ignoring the 'xxxx' unknown section (bytes 8-11 of key = chars 16-19)
    # ASSUMPTION: compare only the known parts
    if len(serial) < 32 or len(expected) < 32:
        return serial.upper() == expected.upper()
    known_parts = expected[:16] + expected[24:32]
    serial_parts = serial.upper()[:16] + serial.upper()[24:32]
    return serial_parts == known_parts



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
