import struct

# Custom MD5-like hash based on the solution writeup
# Key differences from standard MD5:
# 1. Custom initial state (IV)
# 2. Round 3 uses a modified PMOD macro instead of standard P
# 3. state[0] += A + 1, state[3] += D + 2 at the end
# 4. Custom padding starting with 0x6E instead of 0x80

MASK = 0xFFFFFFFF

def left_rotate(x, n):
    x &= MASK
    return ((x << n) | (x >> (32 - n))) & MASK

def md5_process(ctx_state, data):
    assert len(data) == 64
    X = list(struct.unpack('<16I', data))

    A, B, C, D = ctx_state

    # Round 1: F(x,y,z) = z ^ (x & (y ^ z))
    def F1(x, y, z):
        return (z ^ (x & (y ^ z))) & MASK

    def P(a, b, c, d, k, s, t):
        a = (a + F(b, c, d) + X[k] + t) & MASK
        a = (left_rotate(a, s) + b) & MASK
        return a

    F = F1
    A = P(A, B, C, D,  0,  7, 0xD76AA477)
    D = P(D, A, B, C,  1, 12, 0xE8C7B755)
    C = P(C, D, A, B,  2, 17, 0x242070DA)
    B = P(B, C, D, A,  3, 22, 0xC1BDCEED)
    A = P(A, B, C, D,  4,  7, 0xF57C0FAE)
    D = P(D, A, B, C,  5, 12, 0x4787C629)
    C = P(C, D, A, B,  6, 17, 0xA8304612)
    B = P(B, C, D, A,  7, 22, 0xFD469500)
    A = P(A, B, C, D,  8,  7, 0x698098D7)
    D = P(D, A, B, C,  9, 12, 0x8B44F7AE)
    C = P(C, D, A, B, 10, 17, 0xFFFF5BB0)
    B = P(B, C, D, A, 11, 22, 0x895CD7BD)
    A = P(A, B, C, D, 12,  7, 0x6B901121)
    D = P(D, A, B, C, 13, 12, 0xFD987192)
    C = P(C, D, A, B, 14, 17, 0xA679438E)
    B = P(B, C, D, A, 15, 22, 0x49B40821)

    # Round 2: F(x,y,z) = y ^ (z & (x ^ y))
    def F2(x, y, z):
        return (y ^ (z & (x ^ y))) & MASK

    F = F2
    A = P(A, B, C, D,  1,  5, 0xF61E2562)
    D = P(D, A, B, C,  6,  9, 0xC040B340)
    C = P(C, D, A, B, 11, 14, 0x265E5A51)
    B = P(B, C, D, A,  0, 20, 0xE9B6C7AA)
    A = P(A, B, C, D,  5,  5, 0xD62F105D)
    D = P(D, A, B, C, 10,  9, 0x02441453)
    C = P(C, D, A, B, 15, 14, 0xD8A1E681)
    B = P(B, C, D, A,  4, 20, 0xE7D3FBC8)
    A = P(A, B, C, D,  9,  5, 0x21E1CDE6)
    D = P(D, A, B, C, 14,  9, 0xC33707D6)
    C = P(C, D, A, B,  3, 14, 0xF4D50D87)
    B = P(B, C, D, A,  8, 20, 0x455A14ED)
    A = P(A, B, C, D, 13,  5, 0xA9E3E905)
    D = P(D, A, B, C,  2,  9, 0xFCEFA3F8)
    C = P(C, D, A, B,  7, 14, 0x676F02D9)
    B = P(B, C, D, A, 12, 20, 0x8D2A4C8A)

    # Round 3: PMOD macro
    # PMOD(a, b, c, d, k, s, t):
    #   a += ((d << b) ^ c ^ b) + X[k] + t
    #   a = (a << s) | (a << (32-s))   <- ASSUMPTION: likely intended as rotate
    #   a += b
    # Note: F(x,y,z) = (z << x) ^ y ^ x but PMOD doesn't use F directly
    def PMOD(a, b, c, d, k, s, t):
        # ASSUMPTION: (d << b) is 32-bit shift; the rotate in PMOD has a typo
        # (a << s) | (a << (32-s)) should be left_rotate(a, s)
        inner = (((d << b) & MASK) ^ c ^ b) & MASK
        a = (a + inner + X[k] + t) & MASK
        a = left_rotate(a, s)  # ASSUMPTION: typo in source; treat as left rotate
        a = (a + b) & MASK
        return a

    A = PMOD(A, B, C, D,  5,  4, 0xFFFA3942)
    D = PMOD(D, A, B, C,  8, 11, 0x8771F681)
    C = PMOD(C, D, A, B, 11, 16, 0x6D9D6122)
    B = PMOD(B, C, D, A, 14, 23, 0xFDE5380C)
    A = PMOD(A, B, C, D,  1,  4, 0xA4BEEA44)
    D = PMOD(D, A, B, C,  4, 11, 0x4BDECFA9)
    C = PMOD(C, D, A, B,  7, 16, 0xF6BB4B60)
    B = PMOD(B, C, D, A, 10, 23, 0xBEBFBC70)
    A = PMOD(A, B, C, D, 13,  4, 0x289B7EC6)
    D = PMOD(D, A, B, C,  0, 11, 0xEAA127FA)
    C = PMOD(C, D, A, B,  3, 16, 0xD4EF3085)
    B = PMOD(B, C, D, A,  6, 23, 0x04881D05)
    A = PMOD(A, B, C, D,  9,  4, 0xD9D4D039)
    D = PMOD(D, A, B, C, 12, 11, 0xE6DB99E5)
    C = PMOD(C, D, A, B, 15, 16, 0x1FA27CF8)
    B = PMOD(B, C, D, A,  2, 23, 0xC4AC5665)

    # Round 4: F(x,y,z) = y ^ (x | ~z)
    def F4(x, y, z):
        return (y ^ (x | (~z & MASK))) & MASK

    F = F4
    A = P(A, B, C, D,  0,  6, 0xF4292244)
    D = P(D, A, B, C,  7, 10, 0x432AFF97)
    C = P(C, D, A, B, 14, 15, 0xAB9423A7)
    B = P(B, C, D, A,  5, 21, 0xFC93A039)
    A = P(A, B, C, D, 12,  6, 0x655B59C3)
    D = P(D, A, B, C,  3, 10, 0x8F0CCC92)
    C = P(C, D, A, B, 10, 15, 0xFFEFF47D)
    B = P(B, C, D, A,  1, 21, 0x85845DD1)
    A = P(A, B, C, D,  8,  6, 0x6FA87E4F)
    D = P(D, A, B, C, 15, 10, 0xFE2CE6E0)
    C = P(C, D, A, B,  6, 15, 0xA3014314)
    B = P(B, C, D, A, 13, 21, 0x4E0811A1)
    A = P(A, B, C, D,  4,  6, 0xF7537E82)
    D = P(D, A, B, C, 11, 10, 0xBD3AF235)
    C = P(C, D, A, B,  2, 15, 0x2AD7D2BB)
    B = P(B, C, D, A,  9, 21, 0xEB86D391)

    # Custom addition: state[0] += A + 1, state[3] += D + 2
    new_state = [
        (ctx_state[0] + A + 1) & MASK,
        (ctx_state[1] + B) & MASK,
        (ctx_state[2] + C) & MASK,
        (ctx_state[3] + D + 2) & MASK,
    ]
    return new_state


def custom_md5(data: bytes) -> bytes:
    """Custom MD5 with modified IV, round 3, and final addition."""
    # Custom initial state
    state = [0xABCBBBBD, 0xAEEEEEF2, 0xAEEEEEF1, 0xAFE00000]

    # Custom padding: first byte is 0x6E instead of 0x80
    total_len = len(data)
    msg = bytearray(data)

    # Append custom padding byte 0x6E
    msg.append(0x6E)
    # Pad with zeros until length % 64 == 56
    while len(msg) % 64 != 56:
        msg.append(0x00)

    # Append length in bits as 64-bit little-endian
    bit_len = total_len * 8
    msg += struct.pack('<Q', bit_len)

    # Process each 64-byte block
    for i in range(0, len(msg), 64):
        block = bytes(msg[i:i+64])
        state = md5_process(state, block)

    return struct.pack('<4I', *state)


def compute_serial_from_hash(digest: bytes) -> str:
    """Convert 16-byte digest to serial string.
    ASSUMPTION: The serial is the hex string of the digest (uppercase or lowercase).
    The writeup was truncated so we don't know the exact serial format.
    """
    # ASSUMPTION: serial is uppercase hex of the 16-byte digest
    return digest.hex().upper()


def keygen(name: str) -> str:
    """Generate a serial for the given name."""
    # ASSUMPTION: the name is encoded as ASCII/Latin-1 and hashed directly
    data = name.encode('latin-1')
    digest = custom_md5(data)
    return compute_serial_from_hash(digest)


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    expected = keygen(name)
    # ASSUMPTION: comparison is case-insensitive
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
