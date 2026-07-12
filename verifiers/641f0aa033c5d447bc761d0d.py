import hashlib


def _md2(data: bytes) -> str:
    """Compute MD2 hash and return lowercase hex string."""
    # Python's hashlib supports md2 on some systems; fall back to manual impl if not.
    try:
        h = hashlib.new('md2', data)
        return h.hexdigest().lower()
    except ValueError:
        # Manual MD2 implementation
        # RFC 1319
        PI_SUBST = [
            41, 46, 67, 201, 162, 216, 124, 1, 61, 54, 84, 161, 236, 240, 6,
            19, 98, 167, 5, 243, 192, 199, 115, 140, 152, 147, 43, 217, 188,
            76, 130, 202, 30, 155, 87, 60, 253, 212, 224, 22, 103, 66, 111, 24,
            138, 23, 229, 18, 190, 78, 196, 214, 218, 158, 222, 73, 160, 251,
            245, 142, 187, 47, 238, 122, 169, 104, 121, 145, 21, 178, 7, 63,
            148, 194, 16, 137, 11, 34, 95, 33, 128, 127, 93, 154, 90, 144, 50,
            39, 53, 62, 204, 231, 191, 247, 151, 3, 255, 25, 48, 179, 72, 165,
            181, 209, 215, 94, 146, 42, 172, 86, 170, 198, 79, 184, 56, 210,
            150, 164, 125, 182, 118, 252, 107, 226, 156, 116, 4, 241, 69, 157,
            112, 89, 100, 113, 135, 32, 134, 91, 207, 101, 230, 45, 168, 2, 27,
            96, 37, 173, 174, 176, 185, 246, 28, 70, 97, 105, 52, 64, 126, 15,
            85, 71, 163, 35, 221, 81, 175, 58, 195, 92, 249, 206, 186, 197,
            234, 38, 44, 83, 13, 110, 133, 40, 132, 9, 211, 223, 205, 244, 65,
            129, 77, 82, 106, 220, 55, 200, 108, 193, 171, 250, 36, 225, 123,
            8, 12, 189, 177, 74, 120, 136, 149, 139, 227, 99, 232, 109, 233,
            203, 213, 254, 59, 0, 29, 57, 242, 239, 183, 14, 102, 88, 208, 228,
            166, 119, 114, 248, 235, 117, 75, 10, 49, 68, 80, 180, 143, 237,
            31, 26, 219, 153, 141, 51, 159, 17, 131, 20
        ]
        msg = bytearray(data)
        # Step 1: Append padding bytes
        pad_len = 16 - (len(msg) % 16)
        msg += bytearray([pad_len] * pad_len)
        # Step 2: Append checksum
        C = bytearray(16)
        L = 0
        for i in range(len(msg) // 16):
            for j in range(16):
                c = msg[i * 16 + j]
                C[j] ^= PI_SUBST[c ^ L]
                L = C[j]
        msg += C
        # Step 3: Initialize MD buffer
        X = bytearray(48)
        for i in range(len(msg) // 16):
            for j in range(16):
                X[16 + j] = msg[i * 16 + j]
                X[32 + j] = X[16 + j] ^ X[j]
            t = 0
            for j in range(18):
                for k in range(48):
                    t = X[k] ^ PI_SUBST[t]
                    X[k] = t
                t = (t + j) % 256
        return ''.join('%02x' % b for b in X[:16])


def _md4(data: bytes) -> str:
    """Compute MD4 hash and return lowercase hex string."""
    import struct

    def left_rotate(x, n):
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    def F(x, y, z): return (x & y) | (~x & z)
    def G(x, y, z): return (x & y) | (x & z) | (y & z)
    def H(x, y, z): return x ^ y ^ z

    msg = bytearray(data)
    orig_len = len(data) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0)
    msg += struct.pack('<Q', orig_len)

    a0, b0, c0, d0 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476

    for i in range(len(msg) // 64):
        block = msg[i*64:(i+1)*64]
        M = struct.unpack('<16I', block)
        a, b, c, d = a0, b0, c0, d0

        # Round 1
        s1 = [3, 7, 11, 19]
        for j in [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]:
            k = j
            a = left_rotate((a + F(b,c,d) + M[k]) & 0xFFFFFFFF, s1[j%4])
            a, b, c, d = d, a, b, c

        # Round 2
        s2 = [3, 5, 9, 13]
        for j, k in enumerate([0,4,8,12,1,5,9,13,2,6,10,14,3,7,11,15]):
            a = left_rotate((a + G(b,c,d) + M[k] + 0x5A827999) & 0xFFFFFFFF, s2[j%4])
            a, b, c, d = d, a, b, c

        # Round 3
        s3 = [3, 9, 11, 15]
        for j, k in enumerate([0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15]):
            a = left_rotate((a + H(b,c,d) + M[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s3[j%4])
            a, b, c, d = d, a, b, c

        a0 = (a0 + a) & 0xFFFFFFFF
        b0 = (b0 + b) & 0xFFFFFFFF
        c0 = (c0 + c) & 0xFFFFFFFF
        d0 = (d0 + d) & 0xFFFFFFFF

    return struct.pack('<4I', a0, b0, c0, d0).hex()


def _md5(data: bytes) -> str:
    h = hashlib.md5(data)
    return h.hexdigest().lower()


def keygen(name: str) -> str:
    """
    Algorithm (from writeup / AutoIt keygen):
      1. Compute MD2(name.encode())  -> hex string, lowercase
      2. Compute MD4(step1.encode()) -> hex string, lowercase
      3. Compute MD5(step2.encode()) -> hex string, lowercase
      The result of step 3 is the valid password.

    Note: The AutoIt keygen uses _Crypt_HashData which returns a '0x'-prefixed string,
    then uses StringMid(..., 3) to strip the '0x' prefix before passing to next hash.
    The hashes are taken of the ASCII/UTF-8 encoding of the hex string.
    """
    # Step 1: MD2 of username bytes
    step1 = _md2(name.encode('utf-8'))  # lowercase hex string, no prefix
    # Step 2: MD4 of the lowercase MD2 hex string
    step2 = _md4(step1.encode('utf-8'))  # lowercase hex string
    # Step 3: MD5 of the lowercase MD4 hex string
    password = _md5(step2.encode('utf-8'))  # lowercase hex string
    return password


def verify(name: str, serial: str) -> bool:
    """
    Returns True if serial matches the expected password for name.
    Both name and serial must be non-empty (the program checks for empty fields).
    """
    if not name or not serial:
        return False
    expected = keygen(name)
    return serial.lower() == expected.lower()



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
