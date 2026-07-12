# Imagination by kratorius - serial validation algorithm
# Based on solution writeups from crackmes.de
#
# The crackme uses a BMP file (ohmygod.bmp) as the "serial".
# The BMP must have specific properties, and name/serial data is embedded in pixel bytes.
#
# From Solution 1 (TaGaDaPaF), the core algorithm is:
#   bmpData[54 + 4*i] = name[i]          (for i in 0..len(name))
#   bmpData[90 + 4*i] = name[i]-1 if name[i] else ord('x')
#
# The crackme reads these bytes back from the BMP, reconstructs what the name/serial
# should be, and compares with lstrcmpA.
#
# From Solution 2 (Pumqara/kao), the serial decryption:
#   The serial is 5 dwords read from the BMP at offset (FileStart + 36h) near end of Name.
#   Each character of the serial is: char - 1 (decrement by 1, 5 chars total).
#   The name decryption reads 9 dwords from offset 36h, splits each dword's bytes.
#
# ASSUMPTION: The 'serial' in this context is actually the ohmygod.bmp file content.
# We model verify() as checking the pixel data rules, and keygen() as producing
# the correct pixel bytes (not a real BMP file, but the embedded data).
#
# BMP requirements (from writeups):
#   - Magic: 'BM'
#   - 24-bit color (BPP = 24)
#   - File size: 0x160AA = 90282 bytes
#   - Width: 412 pixels, Height: 73 pixels
#   - Compression: 0 (none)
#   - Header size: 40 (Windows 3.x)
#   - Planes: 1
# Image data starts at offset 54 (0x36)
#
# Name constraint: len(name) <= 9

import struct

BMP_FILE_SIZE = 90282  # 0x160AA
BMP_WIDTH = 412
BMP_HEIGHT = 73
BMP_BPP = 24
BMP_COMPRESSION = 0
BMP_HEADER_SIZE = 40
BMP_DATA_OFFSET = 54  # 0x36
BMP_TOTAL = BMP_FILE_SIZE


def build_bmp_header():
    """Build a minimal valid BMP header for a 412x73 24-bit image."""
    # BMP file header (14 bytes)
    bfType = b'BM'
    bfSize = BMP_FILE_SIZE
    bfReserved1 = 0
    bfReserved2 = 0
    bfOffBits = BMP_DATA_OFFSET  # 54 = 14 + 40
    file_header = struct.pack('<2sIHHI', bfType, bfSize, bfReserved1, bfReserved2, bfOffBits)
    
    # DIB header (BITMAPINFOHEADER, 40 bytes)
    biSize = BMP_HEADER_SIZE
    biWidth = BMP_WIDTH
    biHeight = BMP_HEIGHT
    biPlanes = 1
    biBitCount = BMP_BPP
    biCompression = BMP_COMPRESSION
    biSizeImage = BMP_FILE_SIZE - BMP_DATA_OFFSET
    biXPelsPerMeter = 0
    biYPelsPerMeter = 0
    biClrUsed = 0
    biClrImportant = 0
    dib_header = struct.pack('<IiiHHIIiiII',
        biSize, biWidth, biHeight, biPlanes, biBitCount,
        biCompression, biSizeImage,
        biXPelsPerMeter, biYPelsPerMeter,
        biClrUsed, biClrImportant)
    return file_header + dib_header


def keygen(name):
    """
    Generate the ohmygod.bmp file content (as bytes) for the given name.
    The 'serial' is the BMP file itself.
    
    Rules (from Solution 1):
      bmpData[54 + 4*i] = name[i]  for i in 0..len(name) (including null terminator)
      bmpData[90 + 4*i] = name[i]-1 if name[i] != 0 else ord('x')
    
    Returns bytes of the BMP file, or None if name is too long.
    """
    if len(name) > 9:
        return None  # Name too long
    
    header = build_bmp_header()
    # Pixel data: all zeros (black), total size = BMP_FILE_SIZE - 54
    pixel_data = bytearray(BMP_FILE_SIZE - BMP_DATA_OFFSET)
    
    # Embed name into pixel data
    # offset within pixel_data = (54 + 4*i) - 54 = 4*i
    # offset within pixel_data for second check = (90 + 4*i) - 54 = 36 + 4*i
    name_bytes = name.encode('ascii') + b'\x00'  # null-terminated
    
    for i, ch in enumerate(name_bytes):
        idx1 = 4 * i  # bmpData[54 + 4*i] -> pixel_data offset
        idx2 = 36 + 4 * i  # bmpData[90 + 4*i] -> pixel_data offset
        if idx1 < len(pixel_data):
            pixel_data[idx1] = ch
        if idx2 < len(pixel_data):
            # ASSUMPTION: 'x' is lowercase x (0x78) based on writeup analysis
            pixel_data[idx2] = (ch - 1) if ch != 0 else ord('x')
    
    return bytes(header) + bytes(pixel_data)


def verify(name, serial):
    """
    Verify that the given serial (BMP file as bytes) is valid for the name.
    
    serial: bytes object representing the BMP file content
    Returns True if valid, False otherwise.
    """
    if len(name) > 9:
        return False
    
    bmp = serial
    if len(bmp) < BMP_FILE_SIZE:
        return False
    
    # Check BMP magic
    if bmp[0:2] != b'BM':
        return False
    
    # Check file size (at offset 2, dword)
    file_size = struct.unpack_from('<I', bmp, 2)[0]
    if file_size != BMP_FILE_SIZE:
        return False
    
    # Check bits per pixel at offset 0x1C (28)
    bpp = struct.unpack_from('<H', bmp, 28)[0]
    if bpp != 24:
        return False
    
    # Check compression at offset 0x1E (30)
    compression = struct.unpack_from('<I', bmp, 30)[0]
    if compression != 0:
        return False
    
    # Check width (offset 18) and height (offset 22)
    width = struct.unpack_from('<I', bmp, 18)[0]
    height = struct.unpack_from('<I', bmp, 22)[0]
    if width != BMP_WIDTH or height != BMP_HEIGHT:
        return False
    
    # Check pixel data encodes the name correctly
    # bmpData[54 + 4*i] should equal name[i] (with null terminator)
    name_bytes = name.encode('ascii') + b'\x00'
    
    for i, ch in enumerate(name_bytes):
        idx1 = BMP_DATA_OFFSET + 4 * i
        idx2 = 90 + 4 * i  # 0x5A
        if idx1 >= len(bmp) or idx2 >= len(bmp):
            return False
        if bmp[idx1] != ch:
            return False
        expected2 = (ch - 1) if ch != 0 else ord('x')
        if bmp[idx2] != expected2:
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
