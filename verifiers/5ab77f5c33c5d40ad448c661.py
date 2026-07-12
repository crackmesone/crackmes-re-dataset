import struct

MAGIC = b'Obscurity is not security!'


def compute_serial(name: str) -> bytes:
    """Compute the serial/regkey by XORing name bytes with the magic string."""
    name_bytes = name.encode('latin-1')
    serial = bytearray()
    for i, b in enumerate(name_bytes):
        serial.append(b ^ MAGIC[i % len(MAGIC)])
    return bytes(serial)


def verify(name: str, serial: str) -> bool:
    """
    The crackme reads name and serial from a bitmap using steganography.
    The validation algorithm (independent of the bitmap) is:
      serial XOR magic == name
    i.e., for each byte i: serial[i] ^ MAGIC[i] == name[i]

    verify() checks that the provided serial matches the expected one for name.
    Both name and serial are treated as latin-1 strings.
    """
    name_bytes = name.encode('latin-1')
    try:
        serial_bytes = serial.encode('latin-1')
    except (UnicodeEncodeError, AttributeError):
        return False

    if len(serial_bytes) != len(name_bytes):
        return False

    expected = compute_serial(name)
    return serial_bytes == expected


def keygen(name: str) -> str:
    """Generate the correct serial for a given name."""
    serial_bytes = compute_serial(name)
    return serial_bytes.decode('latin-1')


def read_bits_from_bmp(data: bytes, bmp_pixel_start: int, bpp: int, width: int, height: int, num_bytes: int) -> bytearray:
    """
    Read steganographically-encoded bytes from bitmap pixel data.
    For each pixel (3 bytes for 24-bit), extract bit = (prev ^ curr ^ next) & 1,
    accumulate 8 bits into one byte.
    # ASSUMPTION: Only 24-bit uncompressed BMPs are handled here.
    # ASSUMPTION: Row stride is width*bpp + 2 (as used in pc_stega.c: pos+=(2+width*delta))
    """
    delta = bpp // 8
    stride = width * delta + 2
    result = bytearray()
    bit_count = 0
    current_byte = 0
    pos = bmp_pixel_start
    # pos++ as in pc_stega.c
    pos += 1

    for row in range(height):
        for col in range(0, width * delta, delta):
            idx = pos + col
            if idx - 1 < 0 or idx + 1 >= len(data):
                continue
            prev_b = data[idx - 1]
            curr_b = data[idx]
            next_b = data[idx + 1]
            bit = (prev_b ^ curr_b ^ next_b) & 1
            current_byte = (current_byte << 1) | bit
            bit_count += 1
            if bit_count == 8:
                result.append(current_byte & 0xFF)
                current_byte = 0
                bit_count = 0
                if len(result) >= num_bytes:
                    return result
        pos += stride
    return result


def parse_bmp_pixel_start(data: bytes):
    """
    Parse BMP header to find pixel data start offset.
    Returns (pixel_start, bpp, width, height)
    # ASSUMPTION: Only handles Windows BITMAPINFOHEADER (size=40) uncompressed BMPs.
    """
    if data[0:2] != b'BM':
        raise ValueError('Not a BMP file')
    ih_offset = 14  # start of info header
    ih_size = struct.unpack_from('<I', data, ih_offset)[0]
    if ih_size != 40:
        raise ValueError(f'Unsupported info header size: {ih_size}')
    width = struct.unpack_from('<I', data, ih_offset + 4)[0]
    height = struct.unpack_from('<I', data, ih_offset + 8)[0]
    bpp = struct.unpack_from('<H', data, ih_offset + 14)[0]
    compression = struct.unpack_from('<I', data, ih_offset + 16)[0]
    clr_used = struct.unpack_from('<I', data, ih_offset + 32)[0]
    if compression != 0:
        raise ValueError('Compressed BMPs not supported')
    if clr_used != 0:
        edx = clr_used * 4
    elif bpp <= 8:
        edx = (1 << bpp) * 4
    else:
        edx = 0
    pixel_start = ih_offset + ih_size + edx
    return pixel_start, bpp, width, height


def verify_bmp(bmp_path: str) -> bool:
    """
    Read name and serial from BMP steganographic encoding and verify.
    This replicates what the crackme does: extract bytes from BMP,
    split at null terminator to get name and serial,
    then check serial ^ magic == name.
    """
    with open(bmp_path, 'rb') as f:
        data = bytearray(f.read())

    pixel_start, bpp, width, height = parse_bmp_pixel_start(bytes(data))
    # Read up to 100 bytes (as per the C code)
    raw = read_bits_from_bmp(bytes(data), pixel_start, bpp, width, height, 100)

    # Split at first null to get name, then at next null for serial
    if b'\x00' not in raw:
        return False
    null_idx = raw.index(0)
    name_bytes = raw[:null_idx]
    rest = raw[null_idx + 1:]
    if b'\x00' not in rest:
        return False
    null_idx2 = rest.index(0)
    serial_bytes = rest[:null_idx2]

    if len(serial_bytes) != len(name_bytes):
        return False

    # Check: serial[i] ^ magic[i] == name[i]
    for i in range(len(name_bytes)):
        if serial_bytes[i] ^ MAGIC[i % len(MAGIC)] != name_bytes[i]:
            return False
    return True



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
