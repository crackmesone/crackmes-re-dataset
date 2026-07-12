import hashlib
import struct

# This crackme uses a modified MD5 with custom initialization constants.
# The standard MD5 init uses:
#   0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
# But this crackme uses:
#   state[0] = 0x41524554  ('TERA')
#   state[1] = 0x554B205A  ('Z KU')
#   state[2] = 0x20415752  ('RWA ')
#   state[3] = 0x2121594D  ('MY!!')
# Everything else appears to be standard MD5 logic.

# We implement the custom MD5 using Python's struct + manual MD5 transform.
# Since Python's hashlib doesn't allow custom IV, we implement it manually.

def _left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

# Precomputed MD5 table T (standard)
import math
T = [int(2**32 * abs(math.sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

S = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
]

def _md5_compress(state, block):
    """Process a 64-byte block with the given state (4 x uint32)."""
    a, b, c, d = state
    M = struct.unpack('<16I', block)
    
    for i in range(64):
        if i < 16:
            f = (b & c) | (~b & d)
            g = i
        elif i < 32:
            f = (d & b) | (~d & c)
            g = (5 * i + 1) % 16
        elif i < 48:
            f = b ^ c ^ d
            g = (3 * i + 5) % 16
        else:
            f = c ^ (b | ~d)
            g = (7 * i) % 16
        
        f = (f + a + T[i] + M[g]) & 0xFFFFFFFF
        a = d
        d = c
        c = b
        b = (b + _left_rotate(f, S[i])) & 0xFFFFFFFF
    
    return [
        (state[0] + a) & 0xFFFFFFFF,
        (state[1] + b) & 0xFFFFFFFF,
        (state[2] + c) & 0xFFFFFFFF,
        (state[3] + d) & 0xFFFFFFFF,
    ]

def custom_md5(data: bytes) -> bytes:
    """MD5 with custom initialization constants from the crackme source."""
    # Custom IV from crackme source (MD5Init)
    state = [0x41524554, 0x554B205A, 0x20415752, 0x2121594D]
    
    # Padding (standard MD5 padding)
    msg = bytearray(data)
    orig_len_bits = len(data) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<Q', orig_len_bits)
    
    # Process blocks
    for i in range(0, len(msg), 64):
        state = _md5_compress(state, bytes(msg[i:i+64]))
    
    return struct.pack('<4I', *state)

def custom_md5_hex(data: bytes) -> str:
    return custom_md5(data).hex()

# ASSUMPTION: The serial is derived from the custom MD5 hash of the name.
# The exact format of the serial (hex string, subset of bytes, formatted with dashes, etc.)
# is not fully described in the writeup. We assume the serial is the full hex digest
# of the name bytes (encoded as ASCII/latin-1), possibly formatted in groups.
# ASSUMPTION: The name is encoded as bytes using latin-1/ASCII before hashing.
# ASSUMPTION: The serial comparison is case-insensitive hex.

def _compute_serial(name: str) -> str:
    """Compute the expected serial for a given name."""
    name_bytes = name.encode('ascii', errors='replace')
    digest = custom_md5(name_bytes)
    # Return as uppercase hex string
    # ASSUMPTION: serial is the 32-char hex string of the 16-byte digest
    return digest.hex().upper()

def verify(name: str, serial: str) -> bool:
    """Verify if the serial is valid for the given name."""
    if not name or not serial:
        return False
    expected = _compute_serial(name)
    # Normalize serial: remove dashes/spaces, uppercase
    normalized = serial.replace('-', '').replace(' ', '').upper()
    return normalized == expected

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    return _compute_serial(name)


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
