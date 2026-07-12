import struct
import hashlib

# CRC32 table (standard)
import binascii

# Keys for base encoding
KEYS_24  = "ABCDEFGHJKLMNPQRSTUV2345"
KEYS_32  = "123456789ABCDEFGHJKLMNPQRSTUVXYZ"

KEYNO = "6014"

# S-Box
SBOX = [
    0xC4898C30, 0x6244C618, 0x3122630C, 0x18913186, 0xE9635679, 0x4EBD0F54,
    0xC43F5138, 0x621FA89C, 0x310FD44E, 0x1887EA27, 0x0C43F513, 0x0621FA89,
    0x0310FD44, 0x13EE6E3A, 0xD1478561, 0xB70760C0, 0x040B7EA2, 0x0205BF51,
    0x0102DFA8, 0x00816FD4, 0x04CDA65E, 0x40D845F5, 0x929602F8, 0x494B017C,
    0x24A580BE, 0x1252C05F, 0x0929602F, 0x0494B017, 0x024A580B, 0x0EE33C41,
    0x9C51F8A0, 0xFDC37B40, 0xBBFFA520, 0x5DFFD290, 0x2EFFE948, 0x177FF4A4,
    0xDF3F9416, 0xC5DA4F29, 0x00C2CD70, 0x006166B8, 0x0030B35C, 0x001859AE,
    0x000C2CD7, 0x0006166B, 0x00030B35, 0x0013C8D2, 0x00CFBC9D, 0x0E9B42F8,
    0x5088DC52, 0x28446E29, 0x14223714, 0x0A111B8A, 0x5FA2859F, 0x0B120BD5,
    0xF38D0438, 0x79C6821C, 0x3CE3410E, 0x1E71A087, 0x0F38D043, 0x079C6821,
    0x03CE3410, 0x18BC5268, 0x03B96144, 0x4308D6C8
]

MASK = 0xFFFFFFFF

def bsw(x):
    """Byte-swap a 32-bit integer."""
    x &= MASK
    return (((x & 0x000000FF) << 24) |
            ((x & 0x0000FF00) << 8)  |
            ((x & 0x00FF0000) >> 8)  |
            ((x & 0xFF000000) >> 24)) & MASK

def ror32(val, n):
    val &= MASK
    n &= 31
    return ((val >> n) | (val << (32 - n))) & MASK

def rol32(val, n):
    val &= MASK
    n &= 31
    return ((val << n) | (val >> (32 - n))) & MASK

def NOT(x):
    return (~x) & MASK

def hmx_encrypt_block(blk):
    """blk is a list of 8 uint32 values, modified in place."""
    for i in range(8):
        j = i * 8
        for _ in range(16):
            blk[i] = rol32((NOT(bsw(blk[i])) - SBOX[j+7] - 0xC0011337) & MASK, 5)
            blk[i] = ror32((bsw(NOT(blk[i])) + SBOX[j+6]) & MASK ^ 0xFEA71335, 3)
            blk[i] = ror32(((NOT(bsw(blk[i])) - SBOX[j+5]) & MASK + 0x11111111) & MASK, 3)
            blk[i] = (NOT(blk[i]) + SBOX[j+4] - 0x55555555) & MASK
            blk[i] = rol32((NOT(bsw(blk[i]) ^ 0x1337FEA7) + 0x9E3779B9) & MASK, 9)
            blk[i] = (blk[i] - SBOX[j+3]) & MASK
            blk[i] = ((NOT(bsw(blk[i]) ^ SBOX[j+2]) ^ 0xAFEC77ED) + 0x12345678) & MASK
            blk[i] = ror32(NOT(bsw(blk[i])) ^ 0xDEADC0DE, 12)
            blk[i] = (blk[i] + SBOX[j+1]) & MASK
            blk[i] = rol32(NOT(bsw(blk[i])), 6)
            blk[i] = bsw((blk[i] ^ SBOX[j]) - 0xC0FFE & MASK)
            blk[i] &= MASK
    return blk

def crc32_custom(data):
    """Standard CRC32 (same as binascii.crc32 with 0xFFFFFFFF init)."""
    crc = 0xFFFFFFFF
    for byte in data:
        if isinstance(byte, int):
            b = byte
        else:
            b = ord(byte)
        tmp = b ^ crc
        crc >>= 8
        # Use Python's built-in CRC32 table via binascii for a single byte trick
        # Actually reimplement directly
        crc ^= _crc32_table[tmp & 0xFF]
    return (~crc) & MASK

# Build CRC32 table
def _build_crc32_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            if c & 1:
                c = 0xEDB88320 ^ (c >> 1)
            else:
                c >>= 1
        table.append(c)
    return table

_crc32_table = _build_crc32_table()

def base_encrypt(a, mode):
    """Encode integer a in base 'mode' using the appropriate key alphabet."""
    if mode == 24:
        alphabet = KEYS_24
    else:
        alphabet = KEYS_32
    result = []
    s = mode
    while a:
        result.append(alphabet[a % s])
        a //= s
    result.reverse()
    return ''.join(result)

def md5_bytes(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    return hashlib.md5(data).digest()

# ASSUMPTION: The full keygen involves:
# 1. CRC32 of name
# 2. MD5 of name+0xFF+keyno ("6014") 
# 3. RC4-like mixing with hwcode
# 4. hmxEncrypt of a block derived from name/md5/crc
# 5. BaseEncrypt of resulting DWORDs
# The writeup was truncated, so parts 3-5 details are assumptions.

def verify(name, serial):
    """
    Attempt to verify by regenerating the serial for the given name and comparing.
    Since we don't have hwcode and the writeup was truncated, this is partial.
    """
    # ASSUMPTION: No hwcode required for basic name-only serial
    try:
        expected = keygen(name)
        return serial.upper().replace('-','') == expected.upper().replace('-','')
    except Exception:
        return False

def keygen(name):
    """
    Generate serial for name.
    ASSUMPTION: hwcode is empty string (not provided in basic mode).
    ASSUMPTION: The serial is formed from hmxEncrypt of an 8-DWORD block
    where the block is initialized from md5(name+0xFF+keyno) and crc32(name),
    then formatted with BaseEncrypt in base 32.
    The exact RC4 mixing with hwcode and final formatting are partially reconstructed.
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    
    # Step 1: CRC32 of name
    crc_val = crc32_custom(name_bytes)
    
    # Step 2: Build nameWork = name + 0xFF + "6014"
    name_work = name_bytes + bytes([0xFF]) + b'6014'
    
    # Step 3: MD5 of nameWork
    md5_digest = md5_bytes(name_work)  # 16 bytes
    
    # Step 4: Build 8-DWORD block from md5 (16 bytes = 4 DWORDs) + crc repeated
    # ASSUMPTION: block is formed from MD5 digest as 4 DWORDs, padded with crc_val
    block = []
    for i in range(4):
        dw = struct.unpack_from('<I', md5_digest, i*4)[0]
        block.append(dw)
    # Pad remaining 4 DWORDs with crc_val variations
    # ASSUMPTION: remaining slots filled with crc_val and its derivatives
    block.append(crc_val)
    block.append(bsw(crc_val))
    block.append(NOT(crc_val))
    block.append(rol32(crc_val, 8))
    
    # Step 5: hmxEncrypt the block
    enc_block = list(block)
    hmx_encrypt_block(enc_block)
    
    # Step 6: Encode each DWORD using base 32 encoding
    # ASSUMPTION: serial is formed by encoding pairs of DWORDs and joining with '-'
    parts = []
    for dw in enc_block:
        part = base_encrypt(dw & MASK, 32)
        if not part:
            part = KEYS_32[0]
        parts.append(part)
    
    # ASSUMPTION: serial is first 4 parts joined with '-', truncated/padded to typical length
    serial = '-'.join(parts[:4])
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
