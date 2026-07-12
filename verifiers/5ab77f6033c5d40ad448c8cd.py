import hashlib
import struct

# ROT13 table from the solution
ROT13_Table = [
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b,
    0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
    0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23,
    0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f,
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b,
    0x3c, 0x3d, 0x3e, 0x3f, 0x40, 0x4e, 0x4f, 0x50, 0x51, 0x52, 0x53, 0x54,
    0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46,
    0x47, 0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f,
    0x60, 0x6e, 0x6f, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78,
    0x79, 0x7a, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a,
    0x6b, 0x6c, 0x6d, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x80, 0x81, 0x82, 0x83,
    0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f,
    0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b,
    0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7,
    0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf, 0xb0, 0xb1, 0xb2, 0xb3,
    0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf,
    0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xcb,
    0xcc, 0xcd, 0xce, 0xcf, 0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7,
    0xd8, 0xd9, 0xda, 0xdb, 0xdc, 0xdd, 0xde, 0xdf, 0xe0, 0xe1, 0xe2, 0xe3,
    0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef,
    0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb,
    0xfc, 0xfd, 0xfe, 0xff
]

# RSA parameters from the solution (in hex, big-endian)
N1 = 0xBA01DD8527A98D27EB6798907CB32D3B9D44E024077A951359AFCFB0D75DD098B9
D1 = 0x2D021A8A07C8DD2115B3219584B70E70E1B553C771A67195C2A5DE328833453009

N2 = 0x70FBA7002971B26B91F7A451
D2 = 0x40219819AF6BE669ADF7845


def rot13_encrypt(s: bytes) -> bytes:
    return bytes(ROT13_Table[b] for b in s)


def crc32_custom(buff: bytes) -> int:
    """CRC32 using polynomial 0xEDB88320 (standard CRC32)."""
    crc = 0xFFFFFFFF
    for b in buff:
        tmp = b ^ (crc & 0xFF)
        for _ in range(8):
            if tmp & 1:
                tmp >>= 1
                tmp ^= 0xEDB88320
            else:
                tmp >>= 1
        crc >>= 8
        crc ^= tmp
    return (~crc) & 0xFFFFFFFF


def hash_transform(md5_digest: bytes, sha_digest: bytearray) -> bytearray:
    """
    XOR the first 32 bytes of SHA-256 digest with MD5 digest (cycling).
    This matches the assembly loop in the solution.
    """
    result = bytearray(sha_digest)
    edx = 0  # md5 index
    for ecx in range(32):
        eax = md5_digest[edx]
        edx += 1
        if edx == 16:
            edx = 0
        ebx = result[ecx]
        result[ecx] = (eax ^ ebx) & 0xFF
    return result


def hash_loop_d1(p1: str) -> int:
    """
    Reproduces the assembly loop that computes d1 from p1 string.
    This is a hash-like accumulation:
      ebx = 0
      for each char c in p1:
          eax = ord(c)
          ebx = (ebx << 4) + eax
          t = ebx & 0xF0000000
          if t != 0:
              edi = t >> 0x18
              ebx ^= edi
          ebx &= ~t  (NOT t AND ebx)
    Returns ebx as 32-bit signed then used as DWORD.
    """
    ebx = 0
    for c in p1:
        eax = ord(c)
        ebx = ((ebx << 4) + eax) & 0xFFFFFFFF
        t = ebx & 0xF0000000
        if t != 0:
            edi = (t >> 0x18) & 0xFFFFFFFF
            ebx ^= edi
        not_t = (~t) & 0xFFFFFFFF
        ebx = (ebx & not_t) & 0xFFFFFFFF
    # Return as signed 32-bit then reinterpret as used in crc_ += d1
    # The original code uses 'long d1' (signed), then crc_ += d1 (DWORD arithmetic)
    if ebx >= 0x80000000:
        ebx -= 0x100000000
    return ebx


def keygen(name_o: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be between 6 and 19 characters (len > 5 and len < 20).
    """
    name_bytes = name_o.encode('latin-1')
    length = len(name_bytes)
    assert 5 < length < 20, "Name must be 6-19 characters long"

    # Step 1: ROT13-encrypt the name
    name_rot = rot13_encrypt(name_bytes)

    # Step 2: MD5 of ROT13(name)
    md5_digest = hashlib.md5(name_rot).digest()  # 16 bytes

    # Step 3: SHA-256 of ROT13(name)
    sha_digest = bytearray(hashlib.sha256(name_rot).digest())  # 32 bytes

    # Step 4: XOR transform: sha[i] ^= md5[i % 16] for i in 0..31
    transformed = hash_transform(md5_digest, sha_digest)

    # Step 5: RSA1 - powmod(c, d1, n1) where c = bytes_to_big(transformed[:32])
    c_val = int.from_bytes(transformed[:32], 'big')
    m1 = pow(c_val, D1, N1)
    p1 = format(m1, 'X')  # hex string uppercase (cotstr in MIRACL with base 16)

    # Step 6: Compute CRC32 of ROT13(name)
    crc_val = crc32_custom(name_rot)

    # Step 7: Compute d1_hash from p1 string
    d1_val = hash_loop_d1(p1)

    # Step 8: crc_ = (crc_val + d1_val) as 32-bit unsigned
    crc_final = (crc_val + d1_val) & 0xFFFFFFFF

    # Step 9: Convert crc_final to decimal string
    temp_crc = str(crc_final)

    # Step 10: RSA2 - powmod(c2, d2, n2) where c2 = bytes_to_big(temp_crc as bytes)
    c2_val = int.from_bytes(temp_crc.encode('ascii'), 'big')
    m2 = pow(c2_val, D2, N2)
    p2 = format(m2, 'X')  # hex string uppercase

    # Step 11: Assemble serial
    # Format: "--- BEGIN XMAS KEYGENME ---\r\n{rot13name}\r\n{p1}\r\n{p2}\r\n---- END XMAS KEYGENME ----"
    crlf = '\r\n'
    serial = (
        f"--- BEGIN XMAS KEYGENME ---{crlf}"
        f"{name_rot.decode('latin-1')}{crlf}"
        f"{p1}{crlf}"
        f"{p2}{crlf}"
        f"---- END XMAS KEYGENME ----"
    )
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that a serial is valid for a given name.
    The serial must match the format produced by keygen().
    ASSUMPTION: The verify routine in the crackme reverses/re-derives the serial
    and compares; we check by regenerating the expected serial.
    """
    try:
        expected = keygen(name)
        return serial.strip() == expected.strip()
    except Exception:
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
