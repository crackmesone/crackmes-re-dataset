import struct
import ctypes

# Modified MD5 as described/reconstructed from the keygen source
# The keygen uses a 'completely modified MD5' per the author note.
# We reconstruct based on the visible constants and structure.

# Modified PADDING (non-standard)
PADDING = [
    0x0A, 0, 0, 0, 0, 0, 0, 0, 0, 0x0B, 0, 0, 0, 0, 0, 0,
    0, 0, 0x0C, 0, 0, 0, 0, 0, 0, 0, 0, 0x0D, 0, 0, 0, 0,
    0, 0, 0, 0, 0x0E, 0, 0, 0, 0, 0, 0, 0, 0, 0x0F, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x01
]

# The MD5Transform uses 6-element state instead of standard 4
# ASSUMPTION: state has 6 UINT4 values; we only see 4 used in FF/GG/HH/II macros
# ASSUMPTION: the initial state values are non-standard (modified MD5)
# ASSUMPTION: the transform rounds are similar to MD5 but with modified constants/order

def u32(x):
    return x & 0xFFFFFFFF

def rotate_left(x, n):
    return u32((x << n) | (x >> (32 - n)))

def F(x, y, z): return (x & y) | ((~x) & z)
def G(x, y, z): return (x & z) | (y & (~z))
def H(x, y, z): return x ^ y ^ z
def I(x, y, z): return y ^ (x | (~z))

def FF(a, b, c, d, x, s, ac):
    a = u32(a + u32(F(b, c, d)) + u32(x) + u32(ac))
    a = rotate_left(a, s)
    a = u32(a + b)
    return a

def GG(a, b, c, d, x, s, ac):
    a = u32(a + u32(G(b, c, d)) + u32(x) + u32(ac))
    a = rotate_left(a, s)
    a = u32(a + b)
    return a

def HH(a, b, c, d, x, s, ac):
    a = u32(a + u32(H(b, c, d)) + u32(x) + u32(ac))
    a = rotate_left(a, s)
    a = u32(a + b)
    return a

def II(a, b, c, d, x, s, ac):
    a = u32(a + u32(I(b, c, d)) + u32(x) + u32(ac))
    a = rotate_left(a, s)
    a = u32(a + b)
    return a

# ASSUMPTION: Standard MD5 initial state (modified MD5 may differ)
MD5_INIT = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]

# ASSUMPTION: The 6-element state array may include two extra words; unclear what they are
# We implement with 4-element state as only a,b,c,d are used in the visible macros

def md5_transform(state, block):
    """One block MD5 transform with modified structure."""
    # Decode 16 UINT4 from block
    X = list(struct.unpack('<16I', block))

    a, b, c, d = state[0], state[1], state[2], state[3]

    # ASSUMPTION: Round constants are standard MD5 T-table (may be modified)
    # Round 1
    a = FF(a, b, c, d, X[ 0],  7, 0xd76aa478)
    d = FF(d, a, b, c, X[ 1], 12, 0xe8c7b756)
    c = FF(c, d, a, b, X[ 2], 17, 0x242070db)
    b = FF(b, c, d, a, X[ 3], 22, 0xc1bdceee)
    a = FF(a, b, c, d, X[ 4],  7, 0xf57c0faf)
    d = FF(d, a, b, c, X[ 5], 12, 0x4787c62a)
    c = FF(c, d, a, b, X[ 6], 17, 0xa8304613)
    b = FF(b, c, d, a, X[ 7], 22, 0xfd469501)
    a = FF(a, b, c, d, X[ 8],  7, 0x698098d8)
    d = FF(d, a, b, c, X[ 9], 12, 0x8b44f7af)
    c = FF(c, d, a, b, X[10], 17, 0xffff5bb1)
    b = FF(b, c, d, a, X[11], 22, 0x895cd7be)
    a = FF(a, b, c, d, X[12],  7, 0x6b901122)
    d = FF(d, a, b, c, X[13], 12, 0xfd987193)
    c = FF(c, d, a, b, X[14], 17, 0xa679438e)
    b = FF(b, c, d, a, X[15], 22, 0x49b40821)
    # Round 2
    a = GG(a, b, c, d, X[ 1],  5, 0xf61e2562)
    d = GG(d, a, b, c, X[ 6],  9, 0xc040b340)
    c = GG(c, d, a, b, X[11], 14, 0x265e5a51)
    b = GG(b, c, d, a, X[ 0], 20, 0xe9b6c7aa)
    a = GG(a, b, c, d, X[ 5],  5, 0xd62f105d)
    d = GG(d, a, b, c, X[10],  9, 0x02441453)
    c = GG(c, d, a, b, X[15], 14, 0xd8a1e681)
    b = GG(b, c, d, a, X[ 4], 20, 0xe7d3fbc8)
    a = GG(a, b, c, d, X[ 9],  5, 0x21e1cde6)
    d = GG(d, a, b, c, X[14],  9, 0xc33707d6)
    c = GG(c, d, a, b, X[ 3], 14, 0xf4d50d87)
    b = GG(b, c, d, a, X[ 8], 20, 0x455a14ed)
    a = GG(a, b, c, d, X[13],  5, 0xa9e3e905)
    d = GG(d, a, b, c, X[ 2],  9, 0xfcefa3f8)
    c = GG(c, d, a, b, X[ 7], 14, 0x676f02d9)
    b = GG(b, c, d, a, X[12], 20, 0x8d2a4c8a)
    # Round 3
    a = HH(a, b, c, d, X[ 5],  4, 0xfffa3942)
    d = HH(d, a, b, c, X[ 8], 11, 0x8771f681)
    c = HH(c, d, a, b, X[11], 16, 0x6d9d6122)
    b = HH(b, c, d, a, X[14], 23, 0xfde5380c)
    a = HH(a, b, c, d, X[ 1],  4, 0xa4beea44)
    d = HH(d, a, b, c, X[ 4], 11, 0x4bdecfa9)
    c = HH(c, d, a, b, X[ 7], 16, 0xf6bb4b60)
    b = HH(b, c, d, a, X[10], 23, 0xbebfbc70)
    a = HH(a, b, c, d, X[13],  4, 0x289b7ec6)
    d = HH(d, a, b, c, X[ 0], 11, 0xeaa127fa)
    c = HH(c, d, a, b, X[ 3], 16, 0xd4ef3085)
    b = HH(b, c, d, a, X[ 6], 23, 0x04881d05)
    a = HH(a, b, c, d, X[ 9],  4, 0xd9d4d039)
    d = HH(d, a, b, c, X[12], 11, 0xe6db99e5)
    c = HH(c, d, a, b, X[15], 16, 0x1fa27cf8)
    b = HH(b, c, d, a, X[ 2], 23, 0xc4ac5665)
    # Round 4
    a = II(a, b, c, d, X[ 0],  6, 0xf4292244)
    d = II(d, a, b, c, X[ 7], 10, 0x432aff97)
    c = II(c, d, a, b, X[14], 15, 0xab9423a7)
    b = II(b, c, d, a, X[ 5], 21, 0xfc93a039)
    a = II(a, b, c, d, X[12],  6, 0x655b59c3)
    d = II(d, a, b, c, X[ 3], 10, 0x8f0ccc92)
    c = II(c, d, a, b, X[10], 15, 0xffeff47d)
    b = II(b, c, d, a, X[ 1], 21, 0x85845dd1)
    a = II(a, b, c, d, X[ 8],  6, 0x6fa87e4f)
    d = II(d, a, b, c, X[15], 10, 0xfe2ce6e0)
    c = II(c, d, a, b, X[ 6], 15, 0xa3014314)
    b = II(b, c, d, a, X[13], 21, 0x4e0811a1)
    a = II(a, b, c, d, X[ 4],  6, 0xf7537e82)
    d = II(d, a, b, c, X[11], 10, 0xbd3af235)
    c = II(c, d, a, b, X[ 2], 15, 0x2ad7d2bb)
    b = II(b, c, d, a, X[ 9], 21, 0xeb86d391)

    state[0] = u32(state[0] + a)
    state[1] = u32(state[1] + b)
    state[2] = u32(state[2] + c)
    state[3] = u32(state[3] + d)
    return state

def modified_md5(data):
    """Modified MD5 with custom PADDING."""
    state = list(MD5_INIT)  # ASSUMPTION: initial constants same as standard MD5

    msg = bytearray(data)
    orig_len_bits = len(data) * 8

    # Append modified padding instead of standard 0x80 padding
    # ASSUMPTION: padding scheme uses PADDING array but application method unknown
    # Standard MD5 appends 0x80 then zeros to reach 56 mod 64, then 8 bytes length
    # Modified version uses the custom PADDING array
    pad_len = 64 - ((len(msg) + 8) % 64)
    if pad_len == 0:
        pad_len = 64
    # ASSUMPTION: first pad_len bytes of PADDING are used
    msg += bytes(PADDING[:pad_len])
    # Append length as 64-bit little-endian
    msg += struct.pack('<Q', orig_len_bits)

    # Ensure multiple of 64
    for i in range(0, len(msg), 64):
        block = bytes(msg[i:i+64])
        state = md5_transform(state, block)

    return state

def crc32(data):
    """Standard CRC32 as implemented in the keygen (ISO-HDLC / PKZIP variant)."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return u32(~crc)

def compute_serial(name):
    """Compute serial from name.

    The serial format is 'HMX-XXXXXXXX' based on the prefix string in the source.
    ASSUMPTION: The hash result is formatted as hex after modified MD5.
    ASSUMPTION: The serial is derived from the first word(s) of the modified MD5 state.
    ASSUMPTION: Only the first state word is used for the serial number portion.
    """
    name_bytes = name.encode('ascii')
    state = modified_md5(name_bytes)
    # ASSUMPTION: serial number is hex of first state word, formatted as 8 hex digits
    serial_num = '%08X' % state[0]
    return 'HMX-' + serial_num

def verify(name, serial):
    """Verify name/serial pair."""
    if len(name) < 6:
        return False
    expected = compute_serial(name)
    return serial.upper() == expected.upper()

def keygen(name):
    """Generate serial for given name."""
    if len(name) < 6:
        raise ValueError('Name must be at least 6 chars!')
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
