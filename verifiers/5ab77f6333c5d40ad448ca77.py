import struct
import hashlib
import ctypes

# ASSUMPTION: The MD5 used here has modified init constants ('BROK','EN-L','ANDS','HEHE')
# spelled out in the writeup. We attempt to replicate with standard MD5 since we don't
# have the exact modified constants. The keygen.c uses standard MD5 semantics but with
# changed init values. We'll use standard MD5 as a best-effort approximation.
# ASSUMPTION: CRC32 implementation matches standard CRC32.
# ASSUMPTION: RSA uses the exact constants from keygen.c.

DELTA = 0x9E3779B9  # X-TEA golden ratio

def xtea_encipher(num_rounds, v, k):
    v0 = ctypes.c_uint32(v[0]).value
    v1 = ctypes.c_uint32(v[1]).value
    s = ctypes.c_uint32(0).value
    for _ in range(num_rounds):
        v0 = ctypes.c_uint32(v0 + (((v1 << 4) ^ (v1 >> 5)) + v1) ^ (s + k[s & 3])).value
        s = ctypes.c_uint32(s + DELTA).value
        v1 = ctypes.c_uint32(v1 + (((v0 << 4) ^ (v0 >> 5)) + v0) ^ (s + k[(s >> 11) & 3])).value
    return [v0, v1]


def compute_crc32(data):
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF


def rsa_powmod(base, exp, mod):
    return pow(base, exp, mod)


# ASSUMPTION: MD5 uses modified init constants as hinted in writeup.
# We implement a modified MD5 with the constants inferred:
# 'BROK' = 0x4B4F5242, 'EN-L' = 0x4C2D4E45, 'ANDS' = 0x53444E41, 'HEHE' = 0x45484548
# The standard MD5 init is: A=0x67452301, B=0xefcdab89, C=0x98badcfe, D=0x10325476
# ASSUMPTION: We replace A,B,C,D with the four 'BROKEN LANDS' DWORDs.
# Since we can't fully verify, we provide both a standard MD5 path and note the assumption.

import struct as _struct

def _left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def modified_md5(message):
    # ASSUMPTION: Init constants replaced with BROK/EN-L/ANDS/HEHE
    A = 0x4B4F5242  # BROK
    B = 0x4C2D4E45  # EN-L
    C = 0x53444E41  # ANDS
    D = 0x45484548  # HEHE

    # Standard MD5 T table (derived from sin)
    import math
    T = [int(2**32 * abs(math.sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

    # Shifts per round
    S = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
        5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20,
        4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    ]

    # Pre-processing
    msg = bytearray(message)
    orig_len = len(message) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += _struct.pack('<Q', orig_len)

    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        M = _struct.unpack('<16I', chunk)
        a, b, c, d = A, B, C, D
        for j in range(64):
            if j < 16:
                F = (b & c) | (~b & d)
                g = j
            elif j < 32:
                F = (d & b) | (~d & c)
                g = (5 * j + 1) % 16
            elif j < 48:
                F = b ^ c ^ d
                g = (3 * j + 5) % 16
            else:
                F = c ^ (b | ~d)
                g = (7 * j) % 16
            F = (F + a + T[j] + M[g]) & 0xFFFFFFFF
            a, b, c, d = d, (b + _left_rotate(F, S[j])) & 0xFFFFFFFF, b, c
        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D = (D + d) & 0xFFFFFFFF

    digest = _struct.pack('<4I', A, B, C, D)
    return digest


def make_serial(name: str) -> str:
    name_bytes = name.encode('latin-1')
    nlen = len(name_bytes)

    if nlen < 2 or nlen > 20:
        raise ValueError("Name must be at least 2 and at most 20 characters!")

    # Compute xkey from name[2:6] (4 bytes, little-endian uint32)
    # name + 2 means skip first 2 chars, read next 4 bytes
    padded = name_bytes + b'\x00' * 6
    ecx = _struct.unpack_from('<I', padded, 2)[0]
    eax = ctypes.c_uint32(ecx * 8).value
    eax = ctypes.c_uint32(eax - ecx).value
    ebx = ctypes.c_uint32(eax * 3).value
    ebx = ebx ^ 0x4C
    xkey = ebx & 0xFF

    # Modified MD5 of name
    # ASSUMPTION: Using modified MD5 with BROKEN LANDS init constants
    digest = modified_md5(name_bytes)

    # XOR first 16 bytes of digest with xkey
    xored = bytearray(digest[:16])
    for i in range(16):
        xored[i] ^= xkey

    # Convert to hex string (lowercase)
    hash_str = ''.join('%02x' % b for b in xored)
    # hash_str is 32 chars, we use first 16 as hash[0..15]

    # Arithmetic loop over first 8 hex chars and chars at offset 8..15
    esi = 0
    edi = 0
    for i in range(8):
        char0 = ord(hash_str[i])
        char8 = ord(hash_str[i + 8])

        eax_val = ctypes.c_uint32(char0 + 0x26260).value
        eax_val = ctypes.c_uint32(eax_val * nlen).value
        edx_val = ctypes.c_uint32(eax_val * 5).value

        eax2 = ctypes.c_uint32(char8 + 0x5050).value
        eax2 = ctypes.c_uint32(eax2 * nlen * 5).value

        esi = ctypes.c_uint32(esi + edx_val * 8).value

        edx2 = ctypes.c_uint32(eax2 + edi).value
        edi = ctypes.c_uint32(edx2 + eax2 * 4).value

    # X-TEA encipher
    k = [0x4B4F5242, 0x4C2D4E45, 0x53444E41, 0x00000000]  # ASSUMPTION: k[3]=0
    v = [esi, edi]
    result = xtea_encipher(0x1E, v, k)
    part1 = '%08X%08X' % (result[0], result[1])

    # CRC32 of name
    crcname = compute_crc32(name_bytes)
    crc_str = '%08X' % crcname

    # RSA-211: S = CRC32^D mod N
    RSA_D = int('621AC3B1C7E782897C1B94A657A6BCE9BE9338991366B710C4B21', 16)
    RSA_N = int('7CB2EE4EA00A89C1A1BA69BEFFFCDFC0F5C6475A9694FD61309B1', 16)
    C_val = int(crc_str, 16)
    S_val = rsa_powmod(C_val, RSA_D, RSA_N)
    rsa_str = '%X' % S_val

    serial = part1 + '-' + rsa_str + '-BROKEN-LANDS'
    return serial


def verify(name: str, serial: str) -> bool:
    try:
        expected = make_serial(name)
        return serial.upper() == expected.upper()
    except Exception:
        return False


def keygen(name: str) -> str:
    return make_serial(name)



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
