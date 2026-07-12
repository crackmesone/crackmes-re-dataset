# Reverse-engineered keygen for mopy's advanced_math_keygenme
# Based on the partial writeup by s3Ri0us (crackmes.de)
# The crackme uses an AES-like shuffle/XOR structure over a 0x70-byte state array 'h'
# The full shuffle() S-box table (at 0x40F160) and complete loop logic are truncated in the writeup.
# We reconstruct as much as possible; gaps are marked with # ASSUMPTION:

import hashlib
import struct

# ASSUMPTION: The S-box at 0x40F160 is the standard AES S-box (very common in such crackmes)
AES_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

def shuffle(h):
    """
    ASSUMPTION: shuffle() is an AES-like round function operating on the 0x70-byte state.
    From the disassembly:
      h[32..47] = h[16..31] XOR h[0..15]  (XOR of two 16-byte blocks)
      Then a byte-by-byte loop using the S-box over h[0x28..] and h[0x48..]
    The full loop body is truncated. We implement what we know:
    """
    h = bytearray(h)
    # Step 1: h[32..47] = h[16..31] XOR h[0..15]
    for i in range(16):
        h[32 + i] = h[16 + i] ^ h[i]
    # ASSUMPTION: The loop from 0x401726 processes bytes using S-box similarly to AES SubBytes
    # The loop variable edi goes from -0x18 to some end, indexing h[0x28+edi] and h[0x48+edi]
    # We assume it iterates 16 times (one AES block)
    edx = h[0x3f]  # initial edx from disassembly
    for i in range(16):
        idx = i  # edi offset relative to base
        ecx = h[0x28 + idx] if (0x28 + idx) < len(h) else 0
        eax = h[0x48 + idx] if (0x48 + idx) < len(h) else 0
        edx = (edx ^ ecx) & 0xff
        ebx = AES_SBOX[edx]
        eax = (eax ^ ebx) & 0xff
        if (0x48 + idx) < len(h):
            h[0x48 + idx] = eax
    return bytes(h)


def copy_name_and_preshuffle(name):
    """
    Implements copy_name() + pre_shuffle() as described in the writeup.
    h is 0x70 bytes, initialized to zeros.
    h[0..15]  = initial key material (ASSUMPTION: zeros)
    h[16..31] = name block area
    h[32..47] = XOR result
    h[48..63] = output of shuffle
    h[0x44]   = counter (offset 0x44 = 68, within 0..0x6f)
    """
    # ASSUMPTION: h is zero-initialized
    h = bytearray(0x70)
    # h[0x44] is at offset 68
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    ebx = len(name_bytes)
    name_pos = 0

    while ebx != 0:
        v_410764 = h[0x44]  # current fill offset within the 16-byte block
        edx = min(ebx, 16 - v_410764)
        # memcpy(&h[16 + v_410764], name+name_pos, edx)
        for i in range(edx):
            h[16 + v_410764 + i] = name_bytes[name_pos + i]
        name_pos += edx
        ebx -= edx
        v_410764 += edx
        if v_410764 == 16:
            h = bytearray(shuffle(bytes(h)))
            h[0x44] = 0
        else:
            h[0x44] = v_410764

    # pre_shuffle:
    # pad h[16 + h[0x44] ..16+15] with value (16 - h[0x44]) & 0xff
    v = h[0x44]
    pad_val = (16 - v) & 0xff
    pad_len = pad_val
    for i in range(pad_len):
        h[16 + v + i] = pad_val
    h = bytearray(shuffle(bytes(h)))
    # memcpy(&h[16], &h[48], 16)
    for i in range(16):
        h[16 + i] = h[48 + i]
    h = bytearray(shuffle(bytes(h)))
    return bytes(h)


def derive_serial(h):
    """
    ASSUMPTION: The serial is derived from the first 16 bytes of the shuffled state,
    formatted as 4 groups of 4 hex bytes (big-endian 32-bit words), dash-separated.
    The exact serial format is not shown in the truncated writeup.
    """
    # Take first 16 bytes (or h[0..15]) as the key digest
    words = struct.unpack('>4I', h[:16])
    serial = '-'.join(f'{w:08X}' for w in words)
    return serial


def keygen(name):
    h = copy_name_and_preshuffle(name)
    return derive_serial(h)


def verify(name, serial):
    """
    ASSUMPTION: verification recomputes the serial from the name and compares.
    The actual comparison in the crackme binary is not shown in the writeup.
    """
    expected = keygen(name)
    # Normalize for comparison (case-insensitive, ignore dashes vs other separators)
    def normalize(s):
        return s.upper().replace('-','').replace(' ','')
    return normalize(expected) == normalize(serial)



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
