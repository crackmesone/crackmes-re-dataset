#!/usr/bin/env python3
"""
KeygenMe 8 by qptj

Algorithm (from solution writeups):
1. Compute MD2 hash of the username (16 bytes)
2. Take the first 8 bytes as two 32-bit little-endian integers, combine into a 64-bit value b:
   b = (a[0] << 32) | a[1]
   where a[0] and a[1] are the first two 4-byte chunks of the MD2 hash (little-endian)
3. Use a table tbl512 (512 bytes, not provided - ASSUMPTION below) of 64-bit values
4. For each 8-byte entry e in tbl512 (as 64-bit int), compute bar(e & b)
   where bar(x) = parity of the 64-bit value x (XOR of all bits)
5. The serial is the 64-bit integer formed by using each parity bit as a bit,
   bits ordered from bit 63 down to bit 0:
   serial = sum(parity_bit << position for position, parity_bit in zip(range(63,-1,-1), parities))

NOTE: tbl512 is a 512-byte table (64 entries of 8 bytes each) embedded in the crackme binary
at address around 0x401749 area. It is NOT provided in the writeup.
"""

import hashlib
import struct

# MD2 implementation (RFC 1319)
_S = [
     41,  46,  67, 201, 162, 216, 124,   1,  61,  54,  84, 161, 236, 240,   6,  19,
     98, 167,   5, 243, 192, 199, 115, 140, 152, 147,  43, 217, 188,  76, 130, 202,
     30, 155,  87,  60, 253, 212, 224,  22, 103,  66, 111,  24, 138,  23, 229,  18,
    190,  78, 196, 214, 218, 158, 222,  73, 160, 251, 245, 142, 187,  47, 238, 122,
    169, 104, 121, 145,  21, 178,   7,  63, 148, 194,  16, 137,  11,  34,  95,  33,
    128, 127,  93, 154,  90, 144,  50,  39,  53,  62, 204, 231, 191, 247, 151,   3,
    255,  25,  48, 179,  72, 165, 181, 209, 215,  94, 146,  42, 172,  86, 170, 198,
     79, 184,  56, 210, 150, 164, 125, 182, 118, 252, 107, 226, 156, 116,   4, 241,
     69, 157, 112,  89, 100, 113, 135,  32, 134,  91, 207, 101, 230,  45, 168,   2,
     27,  96,  37, 173, 174, 176, 185, 246,  28,  70,  97, 105,  52,  64, 126,  15,
     85,  71, 163,  35, 221,  81, 175,  58, 195,  92, 249, 206, 186, 197, 234,  38,
     44,  83,  13, 110, 133,  40, 132,   9, 211, 223, 205, 244,  65, 129,  77,  82,
    106, 220,  55, 200, 108, 193, 171, 250,  36, 225, 123,   8,  12, 189, 177,  74,
    120, 136, 149, 139, 227,  99, 232, 109, 233, 203, 213, 254,  59,   0,  29,  57,
    242, 239, 183,  14, 102,  88, 208, 228, 166, 119, 114, 248, 235, 117,  75,  10,
     49,  68,  80, 180, 143, 237,  31,  26, 219, 153, 141,  51, 159,  17, 131,  20
]

def _md2(message):
    """Compute MD2 digest, return list of 16 ints."""
    if isinstance(message, str):
        buf = [ord(c) for c in message]
    else:
        buf = list(message)
    
    # Padding
    n = 16 - (len(buf) % 16)
    buf += [n] * n
    
    # Checksum
    c = [0] * 16
    l = 0
    for i in range(0, len(buf), 16):
        block = buf[i:i+16]
        for j in range(16):
            l = _S[block[j] ^ l] ^ c[j]
            c[j] = l
    
    # Message digest
    d = [0] * 48
    for i in range(0, len(buf), 16):
        block = buf[i:i+16]
        for j in range(16):
            d[j+16] = block[j]
            d[j+32] = block[j] ^ d[j]
        t = 0
        for rnd in range(18):
            for j in range(48):
                t = d[j] ^ _S[t]
                d[j] = t
            t = (t + rnd) & 0xff
    
    # Final pass with checksum
    for j in range(16):
        d[j+16] = c[j]
        d[j+32] = c[j] ^ d[j]
    t = 0
    for rnd in range(18):
        for j in range(48):
            t = d[j] ^ _S[t]
            d[j] = t
        t = (t + rnd) & 0xff
    
    return d[0:16]

def _foo(a, b):
    """Combine b bytes from list a into a little-endian integer."""
    r = 0
    for i in range(b):
        r |= (a[i] << (i * 8))
    return r

def _fooz(a, b):
    """Split byte list a into chunks of b bytes, each converted to little-endian int."""
    return [_foo(a[i:i+b], b) for i in range(0, len(a), b)]

def _bar(a):
    """Compute parity of 64-bit value a (XOR of all bits)."""
    result = 0
    for i in range(64):
        result ^= (1 if (a & (1 << i)) else 0)
    return result

# ASSUMPTION: tbl512 is a 512-byte (64 x 8-byte) table from the crackme binary.
# The actual values are not provided in the writeup. We use a placeholder of zeros.
# To use this correctly, extract tbl512 from the binary at the appropriate address.
# The keygen.py solution imports it from 'tblz' module which is not provided.
TBL512 = [0] * 512  # ASSUMPTION: placeholder - real values unknown without binary

def _compute_serial_from_md2(md2_bytes):
    """Core algorithm given MD2 hash bytes (list of 16 ints)."""
    a = _fooz(md2_bytes, 4)  # 4 x 4-byte little-endian ints
    b = (a[0] << 32) | a[1]  # 64-bit combination of first 8 bytes
    
    c = _fooz(TBL512, 8)  # 64 x 8-byte little-endian ints
    
    # For each 64-bit entry in c, compute parity of (entry & b)
    parities = [_bar(e & b) for e in c]
    
    # Combine parities into 64-bit serial: bit 63 is parities[0], bit 0 is parities[63]
    serial = sum(parities[i] << (63 - i) for i in range(64))
    return serial

def keygen(name):
    """Generate serial for given username."""
    if isinstance(name, bytes):
        name = name.decode('latin-1')
    md2_bytes = _md2(name)
    serial = _compute_serial_from_md2(md2_bytes)
    return '%016X' % serial

def verify(name, serial):
    """Verify name/serial combination."""
    expected = keygen(name)
    if isinstance(serial, str):
        return serial.upper() == expected.upper()
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
