import struct
import hashlib

# MD2 PI_SUBST table (from keygen/MD2.inc)
PI_SUBST = [
    41, 46, 67,201,162,216,124,  1, 61, 54, 84,161,236,240,  6, 19,
    98,167,  5,243,192,199,115,140,152,147, 43,217,188, 76,130,202,
    30,155, 87, 60,253,212,224, 22,103, 66,111, 24,138, 23,229, 18,
   190, 78,196,214,218,158,222, 73,160,251,245,142,187, 47,238,122,
   169,104,121,145, 21,178,  7, 63,148,194, 16,137, 11, 34, 95, 33,
   128,127, 93,154, 90,144, 50, 39, 53, 62,204,231,191,247,151,  3,
   255, 25, 48,179, 72,165,181,209,215, 94,146, 42,172, 86,170,198,
    79,184, 56,210,150,164,125,182,118,252,107,226,156,116,  4,241,
    69,157,112, 89,100,113,135, 32,134, 91,207,101,230, 45,168,  2,
    27, 96, 37,173,174,176,185,246, 28, 70, 97,105, 52, 64,126, 15,
    85, 71,163, 35,221, 81,175, 58,195, 92,249,206,186,197,234, 38,
    44, 83, 13,110,133, 40,132,  9,211,223,205,244, 65,129, 77, 82,
   106,220, 55,200,108,193,171,250, 36,225,123,  8, 12,189,177, 74,
   120,136,149,139,227, 99,232,109,233,203,213,254, 59,  0, 29, 57,
   242,239,183, 14,102, 88,208,228,166,119,114,248,235,117, 75, 10,
    49, 68, 80,180,143,237, 31, 26,219,153,141, 51,159, 17,131, 20
]

def md2(data: bytes) -> bytes:
    """MD2 hash implementation based on the assembly in keygen/MD2.inc"""
    if isinstance(data, str):
        data = data.encode('ascii')
    
    # MD2 state: 48 bytes X (split as hash_0..11 in 32-bit words, 3 groups of 16)
    # Actually in the assembly: _hash_0 .. _hash_11 are 12 dwords = 48 bytes
    # They form the X array in standard MD2: X[0..47]
    X = bytearray(48)
    checksum = bytearray(16)
    
    def process_block(block16: bytes):
        # block16 must be exactly 16 bytes
        # Copy block into X[16..31]
        for i in range(16):
            X[16 + i] = block16[i]
        # X[32..47] = X[0..15] XOR block
        for i in range(16):
            X[32 + i] = X[i] ^ block16[i]
        # 18 rounds
        t = 0
        for j in range(18):
            for k in range(48):
                t = X[k] ^ PI_SUBST[t]
                X[k] = t
            t = (t + j) & 0xFF
    
    def update_checksum(block16: bytes):
        L = checksum[15]
        for i in range(16):
            c = block16[i]
            L = PI_SUBST[L ^ c] ^ checksum[i]
            checksum[i] = L
    
    # Process full 16-byte blocks
    length = len(data)
    n_full = length // 16
    remainder = length % 16
    
    offset = 0
    for _ in range(n_full):
        block = data[offset:offset+16]
        process_block(block)
        update_checksum(block)
        offset += 16
    
    # Padding
    pad_len = 16 - remainder
    pad_block = data[offset:] + bytes([pad_len] * pad_len)
    process_block(pad_block)
    update_checksum(pad_block)
    
    # Checksum block
    process_block(bytes(checksum))
    
    return bytes(X[:16])


def md5(data: bytes) -> bytes:
    """Standard MD5"""
    if isinstance(data, str):
        data = data.encode('ascii')
    return hashlib.md5(data).digest()


def bytes_to_hex_upper(b: bytes) -> str:
    return b.hex().upper()


# ASSUMPTION: The crackme uses MD2 and MD5 hashes of the name to produce a serial.
# The exact combination and formatting is not fully described in the truncated writeup.
# Based on the keygen source having both MD2 and MD5 implementations and a serial field,
# a common pattern is: serial = some_hash(name) formatted in groups.
# The assembly keygen likely computes MD2(name) or MD5(name) and formats it.

# ASSUMPTION: The serial is derived from MD5(name) formatted as uppercase hex groups
# separated by dashes, OR from MD2(name). Without the full keygen main logic we cannot
# be certain. We implement both and a best-guess verify.

def _format_serial_from_hash(digest: bytes) -> str:
    """Format 16-byte digest as 4 groups of 8 hex chars separated by '-'"""
    h = digest.hex().upper()
    # Groups of 8 characters (4 bytes each)
    return '-'.join(h[i:i+8] for i in range(0, 32, 8))


def _serial_from_md2(name: str) -> str:
    digest = md2(name.encode('ascii') if isinstance(name, str) else name)
    return _format_serial_from_hash(digest)


def _serial_from_md5(name: str) -> str:
    digest = md5(name.encode('ascii') if isinstance(name, str) else name)
    return _format_serial_from_hash(digest)


def keygen(name: str) -> str:
    # ASSUMPTION: The keygen uses MD5 of the name as the serial.
    # If that doesn't work, try MD2.
    return _serial_from_md5(name)


def verify(name: str, serial: str) -> bool:
    # ASSUMPTION: Compare serial against MD5(name) and MD2(name) formatted versions.
    serial_clean = serial.strip().upper().replace('-', '').replace(' ', '')
    
    md5_digest = md5(name.encode('ascii') if isinstance(name, str) else name)
    md5_hex = md5_digest.hex().upper()
    
    md2_digest = md2(name.encode('ascii') if isinstance(name, str) else name)
    md2_hex = md2_digest.hex().upper()
    
    if serial_clean == md5_hex:
        return True
    if serial_clean == md2_hex:
        return True
    
    # Also try with dashes
    formatted_md5 = _format_serial_from_hash(md5_digest).replace('-', '')
    formatted_md2 = _format_serial_from_hash(md2_digest).replace('-', '')
    
    if serial_clean == formatted_md5:
        return True
    if serial_clean == formatted_md2:
        return True
    
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
