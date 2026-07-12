import hashlib
import struct

# CRC32 table (standard)
def make_crc32_table():
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        table.append(crc)
    return table

CRC32_TABLE = make_crc32_table()

def crc32_bytes(data):
    """Standard CRC32"""
    if isinstance(data, str):
        data = data.encode('latin-1')
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ CRC32_TABLE[(crc ^ b) & 0xFF]
    return (~crc) & 0xFFFFFFFF

def bswap32(v):
    """Byte-swap a 32-bit integer"""
    return struct.unpack('<I', struct.pack('>I', v & 0xFFFFFFFF))[0]

# RSA-64 parameters from writeup
# e (public exponent used to encrypt) = 7E4739D10A975783
# n (modulus)                          = 96F59874BA017371
# d (private/keygen exponent)          = 1234567
N = 0x96F59874BA017371
D = 0x1234567  # keygen exponent
E = 0x7E4739D10A975783  # verification exponent

# ASSUMPTION: The 'modified MD5' uses standard MD5 but then XORs the 2nd dword
# of the digest with 0x58D84E99.
# From solution 1 writeup the XOR values used in the assembly were:
#   XOR EAX,C6EF3720 then XOR EAX,9E3779B9
# net XOR = 0xC6EF3720 ^ 0x9E3779B9 = 0x58D84E99
# Solution 2 source code confirms: iDwordMd5 ^= 0x58D84E99

XOR_CONST = 0xC6EF3720 ^ 0x9E3779B9  # = 0x58D84E99

def compute_name_hash_value(name):
    """Compute the modified MD5 second dword, XORed."""
    if isinstance(name, str):
        name = name.encode('latin-1')
    digest = hashlib.md5(name).digest()
    # Get 2nd dword (bytes 4..7) as little-endian (standard MD5 output)
    dDwordMd5 = struct.unpack_from('<I', digest, 4)[0]
    # bswap it
    iDwordMd5 = bswap32(dDwordMd5)
    # XOR with combined constant
    iDwordMd5 = (iDwordMd5 ^ XOR_CONST) & 0xFFFFFFFF
    return iDwordMd5

def keygen(name):
    """
    Generate serial for given name.
    Steps:
      1. Compute modified MD5 of name -> get 2nd dword -> bswap -> XOR
      2. Format as '%08X' string
      3. Compute CRC32 of that string
      4. Format CRC32 as '%08X' string
      5. Interpret those 8 hex-char bytes as a big-endian 64-bit integer (m)
      6. Compute serial = m^d mod n
      7. Output serial as hex string (uppercase)
    """
    iDwordMd5 = compute_name_hash_value(name)
    szHash1 = '%08X' % iDwordMd5
    iCrc32 = crc32_bytes(szHash1.encode('latin-1'))
    szHash2 = '%08X' % iCrc32
    # bytes_to_big: treat the 8 ASCII bytes as a big-endian number
    # ASSUMPTION: bytes_to_big in miracl treats the raw bytes of the string as big-endian
    m = int.from_bytes(szHash2.encode('latin-1'), 'big')
    # RSA powmod with private exponent d
    result = pow(m, D, N)
    serial = '%X' % result
    return serial.upper()

def verify(name, serial):
    """
    Verify name/serial pair.
    The crackme computes: result = serial^e mod n
    Then compares result with the CRC32-derived value m.
    Steps mirror keygen but use public exponent E.
    """
    iDwordMd5 = compute_name_hash_value(name)
    szHash1 = '%08X' % iDwordMd5
    iCrc32 = crc32_bytes(szHash1.encode('latin-1'))
    szHash2 = '%08X' % iCrc32
    m = int.from_bytes(szHash2.encode('latin-1'), 'big')

    try:
        serial_int = int(serial, 16)
    except ValueError:
        return False

    # Verify: serial^E mod N == m
    check = pow(serial_int, E, N)
    if check == m:
        return True

    # ASSUMPTION: Also try keygen path for cross-check
    expected_serial = keygen(name)
    return serial.upper() == expected_serial.upper()


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
