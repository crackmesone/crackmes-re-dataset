import struct
import hashlib

def md5_hash_custom(data: bytes) -> bytes:
    """Standard MD5 of data, but we'll apply the XOR tweak after."""
    return hashlib.md5(data).digest()

def verify(name: str, serial: str) -> bool:
    expected = keygen(name)
    if expected is None:
        return False
    return serial.upper() == expected.upper()

def keygen(name: str) -> str:
    """
    Algorithm from keygen.asm:
    1. Require name length >= 5
    2. Build a 64-byte buffer:
       - Copy name bytes into NameBuff (up to 32 bytes)
       - Fill remaining bytes (32 - len(name)) with 0xF6
       - The next 32 bytes are fixed data from .data section:
         dd 02020203Dh, 020202020h, 0A0D2020h, 06C500A0Dh
         dd 065736165h, 06E657320h, 06D652064h, 0206C6961h
    3. MD5 hash the 64-byte buffer
    4. XOR bytes 8-9 of the result with 0x3F17 (little-endian word)
    5. Convert 16 bytes to 32-char hex string using tostr:
       digits 0-9 -> '0'-'9', digits A-F -> 'A'-'F' (uppercase via +0x37)
    """
    if len(name) < 5:
        return None

    # Build the 64-byte buffer
    name_bytes = name.encode('ascii', errors='replace')

    # First 32 bytes: name + 0xF6 padding
    part1 = bytearray(32)
    copy_len = min(len(name_bytes), 32)
    for i in range(copy_len):
        part1[i] = name_bytes[i]
    # Fill remaining with 0xF6
    for i in range(copy_len, 32):
        part1[i] = 0xF6

    # Next 32 bytes: fixed data from .data section
    # dd 02020203Dh -> little-endian: 3D 20 20 20 02 -> wait, 0x2020203D
    # MASM stores dwords in little-endian
    # 02020203Dh = 0x2020203D
    # 020202020h = 0x20202020
    # 0A0D2020h  = 0x0A0D2020  -- but wait: 0A0D2020h = 0x0A0D2020
    # ASSUMPTION: the hex values as written in MASM .data are stored little-endian as dwords
    fixed_dwords = [
        0x2020203D,
        0x20202020,
        0x0A0D2020,
        0x0A0D6C50,  # 06C500A0Dh -> that's 5 hex digits, likely 0x06C500A0D is too big
        # ASSUMPTION: re-reading: 06C500A0Dh in MASM = 0x6C500A0D (leading 0 is octal? No, h suffix = hex)
        # Actually MASM hex: 06C500A0Dh means the leading 0 is just for MASM syntax (starts with digit)
        # So: 6C500A0D
        0x65736165,
        0x6E657320,
        0x6D652064,
        0x206C6961,
    ]
    # Re-pack correctly
    fixed_dwords_corrected = [
        0x2020203D,
        0x20202020,
        0x20200D0A,  # 0A0D2020h stored LE: bytes 20 20 0D 0A
        0x0D0A506C,  # 06C500A0Dh -> 0x6C500A0D stored LE: bytes 0D 0A 50 6C
        # ASSUMPTION: interpreting 06C500A0Dh as 0x6C500A0D
        0x65736165,
        0x6E657320,
        0x6D652064,
        0x206C6961,
    ]

    # ASSUMPTION: The fixed_dwords values are stored as little-endian dwords
    part2 = bytearray()
    fixed = [
        0x2020203D,
        0x20202020,
        0x20200D0A,
        0x6C500A0D,
        0x65736165,
        0x6E657320,
        0x6D652064,
        0x206C6961,
    ]
    for dw in fixed:
        part2 += struct.pack('<I', dw)

    buf = bytes(part1) + bytes(part2)
    assert len(buf) == 64

    # Compute MD5
    digest = bytearray(hashlib.md5(buf).digest())

    # XOR bytes 8-9 (word at offset 8) with 0x3F17
    # 'xor word ptr [stMD5Result+8], 03F17h'
    # This XORs the 16-bit little-endian word at offset 8
    w = digest[8] | (digest[9] << 8)
    w ^= 0x3F17
    digest[8] = w & 0xFF
    digest[9] = (w >> 8) & 0xFF

    # Convert to hex string using tostr:
    # high nibble then low nibble
    # 0-9 -> chr(nibble + 0x30)
    # A-F -> chr(nibble + 0x37)
    result = []
    for byte in digest:
        high = (byte >> 4) & 0xF
        low = byte & 0xF
        for nibble in [high, low]:
            if nibble <= 9:
                result.append(chr(nibble + 0x30))
            else:
                result.append(chr(nibble + 0x37))

    return ''.join(result)



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
