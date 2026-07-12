import struct
import hashlib

# MD4 implementation (standard RFC 1320)
def md4(data: bytes) -> bytes:
    """Standard MD4 hash as described in RFC 1320."""
    # Left rotate
    def lrot(x, n):
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    # MD4 auxiliary functions
    def F(x, y, z): return (x & y) | (~x & z)
    def G(x, y, z): return (x & y) | (x & z) | (y & z)
    def H(x, y, z): return x ^ y ^ z

    # Padding
    msg = bytearray(data)
    orig_len_bits = len(data) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)

    # Initial state
    A = 0x67452301
    B = 0xEFCDAB89
    C = 0x89ABCDEF
    D = 0x10325476

    # Process each 512-bit block
    for i in range(0, len(msg), 64):
        block = msg[i:i+64]
        X = list(struct.unpack('<16I', block))

        a, b, c, d = A, B, C, D

        # Round 1
        s1 = [3, 7, 11, 19]
        for j in range(16):
            k = j
            i2 = j % 4
            if i2 == 0:
                a = lrot((a + F(b, c, d) + X[k]) & 0xFFFFFFFF, s1[0])
            elif i2 == 1:
                d = lrot((d + F(a, b, c) + X[k]) & 0xFFFFFFFF, s1[1])
            elif i2 == 2:
                c = lrot((c + F(d, a, b) + X[k]) & 0xFFFFFFFF, s1[2])
            elif i2 == 3:
                b = lrot((b + F(c, d, a) + X[k]) & 0xFFFFFFFF, s1[3])

        # Round 2
        s2 = [3, 5, 9, 13]
        order2 = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
        for j in range(16):
            k = order2[j]
            i2 = j % 4
            if i2 == 0:
                a = lrot((a + G(b, c, d) + X[k] + 0x5A827999) & 0xFFFFFFFF, s2[0])
            elif i2 == 1:
                d = lrot((d + G(a, b, c) + X[k] + 0x5A827999) & 0xFFFFFFFF, s2[1])
            elif i2 == 2:
                c = lrot((c + G(d, a, b) + X[k] + 0x5A827999) & 0xFFFFFFFF, s2[2])
            elif i2 == 3:
                b = lrot((b + G(c, d, a) + X[k] + 0x5A827999) & 0xFFFFFFFF, s2[3])

        # Round 3
        s3 = [3, 9, 11, 15]
        order3 = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]
        for j in range(16):
            k = order3[j]
            i2 = j % 4
            if i2 == 0:
                a = lrot((a + H(b, c, d) + X[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s3[0])
            elif i2 == 1:
                d = lrot((d + H(a, b, c) + X[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s3[1])
            elif i2 == 2:
                c = lrot((c + H(d, a, b) + X[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s3[2])
            elif i2 == 3:
                b = lrot((b + H(c, d, a) + X[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s3[3])

        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D = (D + d) & 0xFFFFFFFF

    return struct.pack('<4I', A, B, C, D)


def tea_encrypt(v0: int, v1: int, key: list) -> tuple:
    """
    Standard TEA encrypt with 32 rounds.
    key is a list of 4 uint32 values.
    The delta is 0x9E3779B9, sum starts at 0.
    The crackme uses XTEA-like structure but the assembly shows standard TEA.
    From the assembly: decrement is by 0x9E3779B9, starts at 0xC6EF3720 (= 32*delta & mask) for decrypt.
    We need to ENCRYPT: start sum=0, increment by delta, 32 rounds.
    """
    DELTA = 0x9E3779B9
    MASK = 0xFFFFFFFF
    s = 0
    for _ in range(32):
        s = (s + DELTA) & MASK
        v0 = (v0 + (((v1 << 4) + key[0]) ^ (v1 + s) ^ ((v1 >> 5) + key[1]))) & MASK
        v1 = (v1 + (((v0 << 4) + key[2]) ^ (v0 + s) ^ ((v0 >> 5) + key[3]))) & MASK
    return v0, v1


def keygen(name: str) -> str:
    """
    Generate serial for a given name.
    Algorithm:
    1. Compute MD4 of the name (as bytes, using the name string encoded as latin-1/ASCII)
    2. Use the 16-byte MD4 digest as 4 uint32 little-endian key words for TEA
    3. TEA-encrypt the plaintext [0x78336368, 0x756E3A29] ('x3ch', 'un:)' in little-endian)
       Wait - the cmp in the disasm is: cmp esi, 'x3ch' and cmp edi, 'un:)'
       In x86 little-endian memory 'x3ch' = 0x78336368 and 'un:)' = 0x756E3A29
       The data values match what scarebyte's keygen sets:
         data[0] = 0x78336368, data[1] = 0x756E3A29
    4. Format the two resulting dwords as 8-char uppercase hex, concatenated = 16-char serial
    """
    # Step 1: MD4 of name
    digest = md4(name.encode('latin-1'))

    # Step 2: Extract key from MD4 digest (4 little-endian uint32)
    key = list(struct.unpack('<4I', digest))

    # Step 3: TEA encrypt
    # Plaintext as specified in scarebyte's keygen
    v0 = 0x78336368  # 'x3ch' in little-endian
    v1 = 0x756E3A29  # 'un:)' in little-endian

    r0, r1 = tea_encrypt(v0, v1, key)

    # Step 4: Format as 16-char hex string
    serial = f'{r0:08X}{r1:08X}'
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    Conditions from disassembly:
    - name length > 3 (>= 4 chars after cmp ebx,3 / jge)
    - serial length == 16
    - serial matches computed serial for name
    """
    if len(name) < 4:
        return False
    if len(serial) != 16:
        return False
    expected = keygen(name)
    return serial.upper() == expected.upper()



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
