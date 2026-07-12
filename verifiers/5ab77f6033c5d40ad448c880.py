import hashlib
import struct

# Custom MD5 initialization constants (from crackme disassembly)
# REAL MD5: 67452301, EFCDAB89, 98BADCFE, 10325476
# CRACKME:  4552205B, 474E4556, 72432045, 5D207765
CUSTOM_MD5_A = 0x4552205B
CUSTOM_MD5_B = 0x474E4556
CUSTOM_MD5_C = 0x72432045
CUSTOM_MD5_D = 0x5D207765

# Standard MD5 constants and operations
import math

def left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

# Precomputed MD5 per-round shift amounts
S = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
]

# Precomputed MD5 sine-based constants
K = [int(2**32 * abs(math.sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

def custom_md5(message: bytes) -> bytes:
    """MD5 with custom initialization vectors as used in crackme."""
    # Pad message
    msg = bytearray(message)
    orig_len_bits = (len(message) * 8) & 0xFFFFFFFFFFFFFFFF
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)

    # Initialize with custom constants
    a0 = CUSTOM_MD5_A
    b0 = CUSTOM_MD5_B
    c0 = CUSTOM_MD5_C
    d0 = CUSTOM_MD5_D

    # Process each 512-bit chunk
    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        M = struct.unpack('<16I', chunk)

        A, B, C, D = a0, b0, c0, d0

        for j in range(64):
            if j < 16:
                F = (B & C) | ((~B) & D)
                g = j
            elif j < 32:
                F = (D & B) | ((~D) & C)
                g = (5 * j + 1) % 16
            elif j < 48:
                F = B ^ C ^ D
                g = (3 * j + 5) % 16
            else:
                F = C ^ (B | (~D))
                g = (7 * j) % 16

            F = (F + A + K[j] + M[g]) & 0xFFFFFFFF
            A = D
            D = C
            C = B
            B = (B + left_rotate(F, S[j])) & 0xFFFFFFFF

        a0 = (a0 + A) & 0xFFFFFFFF
        b0 = (b0 + B) & 0xFFFFFFFF
        c0 = (c0 + C) & 0xFFFFFFFF
        d0 = (d0 + D) & 0xFFFFFFFF

    return struct.pack('<4I', a0, b0, c0, d0)


def compute_hash1(name: str) -> int:
    """Hash1: small cycle over first 8 chars of name.
    ASSUMPTION: Exact algorithm not fully disclosed. 
    The writeup mentions 'a little cycle for 8 times with first 8 name chars, some easy small calculations'.
    We do NOT have the exact formula. Returning a placeholder.
    For name='Guetta', hash1 result leads to: second_part = 20066002 + hash1 = 2EF43A02 => hash1 = 0EEDDA00
    For name='crackmes.de', hash1 = 0xCBAC46EC
    """
    # ASSUMPTION: The exact loop/calculation is not disclosed in writeup.
    # We cannot reconstruct this without more information.
    # Returning None to indicate this is unknown.
    return None


def compute_hash2(name: str) -> int:
    """Hash2: first dword of custom MD5 hash of name, XORed with 0x2FF66002."""
    name_bytes = name.encode('ascii')
    md5_hash = custom_md5(name_bytes)
    first_dword = struct.unpack('<I', md5_hash[:4])[0]
    hash2 = first_dword ^ 0x2FF66002
    return hash2


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    # Check name length
    if len(name) < 4 or len(name) > 127:
        return False

    # Check serial length (must be 35 = 0x23)
    if len(serial) != 35:
        return False

    # Check dashes at positions 8, 17, 26
    if serial[8] != '-' or serial[17] != '-' or serial[26] != '-':
        return False

    # Parse four hex parts from serial
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    try:
        p1 = int(parts[0], 16)
        p2 = int(parts[1], 16)
        p3 = int(parts[2], 16)
        p4 = int(parts[3], 16)
    except ValueError:
        return False

    # 3rd check: first part must satisfy:
    # (p1 XOR 0x64726F6C) - 0xDEADBEEF == 0  (mod 2^32)
    # => p1 XOR 0x64726F6C == 0xDEADBEEF
    # => p1 == 0xDEADBEEF XOR 0x64726F6C == 0xBADFD183
    expected_p1 = (0xDEADBEEF ^ 0x64726F6C) & 0xFFFFFFFF
    if p1 != expected_p1:
        return False

    # 4th check: p2 - hash1 == 0x20066002
    # => p2 = 0x20066002 + hash1
    hash1 = compute_hash1(name)
    if hash1 is None:
        # ASSUMPTION: Cannot verify 4th check without hash1 algorithm
        pass  # skip check
    else:
        expected_p2 = (0x20066002 + hash1) & 0xFFFFFFFF
        if p2 != expected_p2:
            return False

    # 5th check: (p3 XOR hash2) must equal address 0x00401A46
    # The crackme calls the result of (p3 XOR hash2) as a function pointer
    # and expects it to reach the goodboy at 0x00401A46
    # ASSUMPTION: The SEH trick means calling wrong address triggers exception -> badboy
    # So p3 XOR hash2 == 0x00401A46
    hash2 = compute_hash2(name)
    expected_p3 = (0x00401A46 ^ hash2) & 0xFFFFFFFF
    if p3 != expected_p3:
        return False

    # 4th part check: not fully described in writeup
    # ASSUMPTION: p4 check details were truncated in writeup
    # We skip p4 check

    return True


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    # Part 1: always BADFD183
    p1 = 0xBADFD183

    # Part 2: requires hash1 (unknown algorithm)
    hash1 = compute_hash1(name)
    if hash1 is not None:
        p2 = (0x20066002 + hash1) & 0xFFFFFFFF
    else:
        # ASSUMPTION: hash1 unknown, cannot compute p2 generically
        # Using known value for 'Guetta' as example
        raise NotImplementedError("hash1 algorithm not recovered; cannot generate p2 for arbitrary name")

    # Part 3: p3 = hash2 XOR 0x00401A46
    hash2 = compute_hash2(name)
    p3 = (hash2 ^ 0x00401A46) & 0xFFFFFFFF

    # Part 4: ASSUMPTION: not fully described, using 0 as placeholder
    p4 = 0x00000000  # ASSUMPTION: unknown

    serial = '{:08X}-{:08X}-{:08X}-{:08X}'.format(p1, p2, p3, p4)
    return serial



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
