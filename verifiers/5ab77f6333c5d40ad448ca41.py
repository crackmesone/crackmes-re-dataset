import struct

def crc32_step(eax, byte_val):
    """Process one byte through the CRC32-like hash (subNameHash inner logic)."""
    al = eax & 0xFF
    al ^= byte_val
    eax = (eax & 0xFFFFFF00) | al
    for _ in range(8):
        carry = eax & 1
        eax = (eax >> 1) & 0x7FFFFFFF
        if carry:
            eax ^= 0xEDB88320
    return eax & 0xFFFFFFFF

def sub_name_hash(eax, data_bytes):
    """subNameHash: iterates over ecx bytes starting at edx, doing CRC32-like steps."""
    for b in data_bytes:
        eax = crc32_step(eax, b)
    return eax & 0xFFFFFFFF

def keygen(name):
    """
    Keygen for BlackEye's Unicorn crackme.

    Algorithm (from keygen.asm):
    1. Take name, append 0x0D, 0x0A, pad to 12 bytes total.
    2. Hash 12 bytes starting with initial value NOT(0x4B323321) = 0xB4CDCCDE
    3. For each of 4 serial bytes:
       - XOR low byte of current hash with magic constant
       - Store as serial byte
       - Feed that byte back into hash (1 byte) to get next hash value
    4. The last (4th) byte is just al (low byte) of hash after 3rd step, no XOR.
    5. bswap the 4-byte serial and format as 8 uppercase hex digits.
    """
    # Step 1: build 12-byte buffer: name bytes + 0x0D + 0x0A, zero-padded to 12
    name_bytes = name.encode('ascii', errors='replace')
    name_len = len(name_bytes)
    # The crackme appends CR LF after the name text (simulating console input)
    buf = bytearray(12)
    for i, b in enumerate(name_bytes[:10]):  # max name length is 10 to fit CR LF in 12
        buf[i] = b
    if name_len < 12:
        buf[name_len] = 0x0D
    if name_len + 1 < 12:
        buf[name_len + 1] = 0x0A

    # Step 2: Initial hash of 12 bytes
    initial = (~0x4B323321) & 0xFFFFFFFF  # NOT(0x4B323321) = 0xB4CDCCDE
    eax = sub_name_hash(initial, buf)

    # Step 3: Calculate 4 serial bytes
    magic = [0x8E, 0xBB, 0xD6]
    serial_bytes = bytearray(4)

    # Byte 0
    bl = (eax & 0xFF) ^ 0x8E
    serial_bytes[0] = bl
    eax = sub_name_hash(eax, bytes([bl]))

    # Byte 1
    bl = (eax & 0xFF) ^ 0xBB
    serial_bytes[1] = bl
    eax = sub_name_hash(eax, bytes([bl]))

    # Byte 2
    bl = (eax & 0xFF) ^ 0xD6
    serial_bytes[2] = bl
    eax = sub_name_hash(eax, bytes([bl]))

    # Byte 3: just low byte of eax, no XOR magic
    serial_bytes[3] = eax & 0xFF

    # Step 4: bswap and format
    # bswap reverses byte order
    val = (serial_bytes[0] << 24) | (serial_bytes[1] << 16) | (serial_bytes[2] << 8) | serial_bytes[3]
    # After bswap:
    bswapped = struct.unpack('>I', struct.pack('<I', val))[0]
    serial_str = '%08X' % bswapped
    return serial_str

def verify(name, serial):
    """Verify by generating the correct serial and comparing."""
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
