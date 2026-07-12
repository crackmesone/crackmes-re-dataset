import struct
import ctypes

def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def bswap32(val):
    val &= 0xFFFFFFFF
    return struct.unpack('<I', struct.pack('>I', val))[0]

def u32(x):
    return x & 0xFFFFFFFF

# myCrypt is a variant of MD4/MD5-like hash
# From the code: initializes state to [0xFDABCDEF, 0xD9E0FA1B, 0xF5A6B7C8, 0xA1B2D3E4]
# then runs MD5-like rounds using those constants
# The constants seen are exactly MD5 T-table constants, so this IS MD5 but with custom IV
# and the input is the nameBuffer (padded MD5-style)

def md5_like(data, length):
    """MD5 with custom IV as described in myCrypt"""
    # Custom initial hash values
    A = 0xFDABCDEF
    B = 0xD9E0FA1B
    C = 0xF5A6B7C8
    D = 0xA1B2D3E4

    # MD5 padding
    msg = bytearray(data[:length])
    orig_len_bits = length * 8
    msg.append(0x80)
    # pad to 56 mod 64
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)

    # MD5 constants
    T = [
        0,
        0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
        0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
        0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
        0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
        0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
        0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
        0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
        0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
        0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
        0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
        0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
        0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
        0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
        0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
        0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
        0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391,
    ]

    S = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
        5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20,
        4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    ]

    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        M = struct.unpack('<16I', chunk)
        a, b, c, d = A, B, C, D
        for j in range(64):
            if j < 16:
                f = (b & c) | ((~b) & d)
                g = j
            elif j < 32:
                f = (d & b) | ((~d) & c)
                g = (5*j + 1) % 16
            elif j < 48:
                f = b ^ c ^ d
                g = (3*j + 5) % 16
            else:
                f = c ^ (b | (~d))
                g = (7*j) % 16
            f = u32(f)
            temp = u32(a + f + M[g] + T[j+1])
            temp = rol32(temp, S[j])
            temp = u32(temp + b)
            a, b, c, d = d, temp, b, c
        A = u32(A + a)
        B = u32(B + b)
        C = u32(C + c)
        D = u32(D + d)

    # Return output buffer as bytes (16 bytes)
    return struct.pack('<4I', A, B, C, D)


def compute_serial(name):
    if isinstance(name, str):
        name = name.encode('latin-1')

    name_len = len(name)
    if name_len < 4 or name_len > 32:
        return None

    # Work with a mutable buffer
    buf = bytearray(name) + bytearray(100)  # extra space

    al = name_len  # initial name size

    # InnerLoop_1: modify name buffer
    # ECX = 0..name_len-1
    # BL = buf[ECX] + AL (name_len)
    # EDX = DWORD at buf[0] XOR EBX
    # buf[ECX] = DL
    for ecx in range(al):
        bl = (buf[ecx] + al) & 0xFF
        edx = struct.unpack_from('<I', buf, 0)[0]
        ebx = bl  # EBX low byte = BL, but EBX was XOR'd: need to be careful
        # MOV BL, byte -> only BL changes; EBX upper bits from prior iteration
        # ASSUMPTION: EBX is 0 at start, so EBX = bl each time (BL set, upper=0 since XOR ECX,EBX at start)
        edx = edx ^ ebx
        buf[ecx] = edx & 0xFF

    # InnerLoop_2
    al = name_len
    ebx = 0x10101010
    output = bytearray(16)
    edx = 0  # EDX accumulator across loop

    for ecx in range(al):
        bl = buf[ecx] & 0xFF
        # MOV BL, byte -> EBX = (EBX & 0xFFFFFF00) | bl
        ebx = (ebx & 0xFFFFFF00) | bl
        ebx = rol32(ebx, 5)
        edx2 = u32(0x68F6B76C * al)
        ebx2 = u32(ebx * al)
        edx2 = u32(edx2 ^ ebx2)
        first_dword = struct.unpack_from('<I', buf, 0)[0]
        edx2 = u32(edx2 + first_dword)
        struct.pack_into('<I', buf, 0, edx2)

        # First myCrypt call
        out1 = myCrypt(buf, al)
        ebx_tmp = struct.unpack_from('<I', out1, 6)[0]
        edx2 = u32(edx2 ^ ebx_tmp)
        edx2 = rol32(edx2, 7)

        al2 = name_len
        # Second myCrypt call
        out2 = myCrypt(buf, al2)
        ebx_tmp = struct.unpack_from('<I', out2, 8)[0]
        edx2 = u32(edx2 ^ ebx_tmp)
        buf[ecx] = edx2 & 0xFF

        al2 = name_len
        # Third myCrypt call
        out3 = myCrypt(buf, al2)
        ebx_tmp = struct.unpack_from('<I', out3, 0xA)[0]
        edx2 = u32(edx2 ^ ebx_tmp)
        edx2 = rol32(edx2, 4)
        buf[ecx] = edx2 & 0xFF

        al2 = name_len
        # Fourth myCrypt call (result stored in output)
        out4 = myCrypt(buf, al2)
        output = bytearray(out4)

        al = name_len
        ebx = 0x10101010
        edx = edx2  # carry edx

    # Extract serial parts from output
    p0 = struct.unpack_from('<I', output, 0)[0]
    p1 = struct.unpack_from('<I', output, 4)[0]
    p2 = struct.unpack_from('<I', output, 8)[0]
    p3 = struct.unpack_from('<I', output, 12)[0]

    serial_hex = '%lX%lX%lX%lX' % (p0, p1, p2, p3)
    # Pad/truncate to 32 chars for SerialCreationLoop (loop runs ECX=0..0x1F)
    # ASSUMPTION: serial_hex may be shorter than 32; pad with zeros
    serial_hex = serial_hex.ljust(32, '0')[:32]
    serial_bytes = serial_hex.encode('latin-1')

    # SerialCreationLoop: 32 iterations
    result = bytearray(32)
    edx_loop = edx  # EDX from end of InnerLoop_2 (last edx2)
    for ecx in range(0x20):
        bl = serial_bytes[ecx] if ecx < len(serial_bytes) else 0
        ebx_l = bl
        ebx_l = rol32(ebx_l, 0x10)
        ebx_l = bswap32(ebx_l)
        ebx_l = u32(ebx_l + 0x1A2B3C4D)
        ebx_l = bswap32(ebx_l)
        ebx_l = u32(ebx_l ^ edx_loop)
        eax_l = ebx_l
        # CDQ + IDIV 0x19
        eax_signed = ctypes.c_int32(eax_l).value
        remainder = eax_signed % 0x19
        if remainder < 0:
            remainder += 0x19
        result[ecx] = (remainder + 0x41) & 0xFF

    return result.decode('latin-1')


def myCrypt(buf, name_size):
    """Wrapper calling md5_like on the buffer"""
    data = bytes(buf[:100] if len(buf) >= 100 else buf + bytes(100 - len(buf)))
    return md5_like(data, name_size)


def verify(name, serial):
    expected = compute_serial(name)
    if expected is None:
        return False
    return serial == expected


def keygen(name):
    result = compute_serial(name)
    return result



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
