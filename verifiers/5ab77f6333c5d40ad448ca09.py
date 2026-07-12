import struct
from functools import reduce

# ---- constants from the writeup ----

v = bytes([
    0x11, 0xC5, 0x26, 0x27, 0x66, 0x5B, 0x48, 0x33,
    0x0B, 0x7B, 0x13, 0x35, 0xE9, 0x8A, 0x69, 0x9F
])

# Mb is 128 rows x 16 bytes (GF(2) matrix or GF(2^8) matrix used in the check)
# Only a portion was shown; we embed what was given and note the truncation.
# ASSUMPTION: Mb is used as a linear map over GF(2^8) bytes:
#   output[i] = XOR over j of (Mb[row*16+j] * input[j])  in GF(2^8) -- but
#   looking at the values (multiples of 2), it may be a binary matrix (bits).
# ASSUMPTION: The crackme uses 'v' as a target vector and Mb as a matrix;
#   the serial encodes coefficients x such that Mb * x = v  (or similar).
# ASSUMPTION: The name is hashed / processed to produce part of the input.
# ASSUMPTION: The full Mb table (128*16 bytes) was truncated in the writeup.
#   We embed the visible portion and mark the rest as unknown.

# Because the full Mb was truncated we cannot implement the real check.
# We implement the structure we can infer.

Mb_partial = bytes([
    0x0C,0x52,0x96,0xC8,0xB0,0xB0,0x0C,0x0C,0x96,0x52,0x0C,0xC8,0x96,0x0C,0x2A,0xB0,
    0x74,0xEE,0x52,0xC8,0xC8,0xC8,0xB0,0xB0,0xC8,0x96,0xEE,0xB0,0xEE,0x2A,0x96,0x52,
    0x1C,0x10,0xA0,0xAC,0xD4,0x1C,0x10,0xD8,0x3A,0x68,0x86,0xD4,0xD4,0x42,0x10,0x86,
    0xFE,0x4E,0x86,0x36,0x8A,0x1C,0xD4,0x42,0x1C,0xF2,0x64,0x8A,0x10,0xD8,0x4E,0x86,
    0x5E,0x78,0xBC,0x9A,0x5E,0x00,0xBC,0xE2,0x26,0xC4,0xC4,0x26,0xE2,0x78,0x00,0x9A,
    0xD4,0xD8,0x68,0x64,0x1C,0xD4,0xD8,0x10,0xF2,0xA0,0x4E,0x1C,0x1C,0x8A,0xD8,0x4E,
    0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,0xC8,
    0x36,0x86,0x4E,0xFE,0x42,0xD4,0x1C,0x8A,0xD4,0x3A,0xAC,0x42,0xD8,0x10,0x86,0x4E,
])

# GF(2^8) multiplication with poly 0x11b (AES poly)
def gf_mul(a, b):
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p

def mat_vec_mul(matrix_rows, vec):
    """Multiply a list of 16-byte rows by a 16-byte vector in GF(2^8)."""
    out = []
    for row in matrix_rows:
        acc = 0
        for j in range(16):
            acc ^= gf_mul(row[j], vec[j])
        out.append(acc)
    return bytes(out)

def get_mb_row(i):
    """Return row i (16 bytes) of Mb. ASSUMPTION: rows repeat with period 8
       based on the visible pattern in the writeup (cyclic shifts observed)."""
    # ASSUMPTION: We only have 8 full rows; rest is unknown.
    if i * 16 + 16 <= len(Mb_partial):
        return Mb_partial[i*16:(i+1)*16]
    # ASSUMPTION: pattern cycles every 8 rows
    return get_mb_row(i % 8)

# ASSUMPTION: The crackme processes the name into a 16-byte block (e.g. MD5 or
#   simple hashing), then checks that some matrix equation holds for the serial.

def name_to_block(name):
    """ASSUMPTION: name is encoded to UTF-16LE bytes, padded/truncated to 16 bytes."""
    nb = name.encode('utf-16-le')
    block = bytearray(16)
    for i, b in enumerate(nb[:16]):
        block[i] = b
    return bytes(block)

def serial_to_bytes(serial):
    """ASSUMPTION: serial is a hex string of 32 hex chars = 16 bytes."""
    try:
        return bytes.fromhex(serial.replace('-', '').replace(' ', ''))
    except Exception:
        return None

def verify(name, serial):
    """
    ASSUMPTION: The crackme:
      1. Converts name to a 16-byte block (name_block).
      2. Converts serial to a 16-byte block (serial_block).
      3. Computes result = Mb (first 16 rows) * serial_block  in GF(2^8).
      4. XORs result with name_block.
      5. Checks that the output equals v.
    This is a partial reconstruction; the real algorithm may differ.
    """
    sb = serial_to_bytes(serial)
    if sb is None or len(sb) != 16:
        return False
    nb = name_to_block(name)
    rows = [get_mb_row(i) for i in range(16)]
    result = mat_vec_mul(rows, sb)
    check = bytes(result[i] ^ nb[i] for i in range(16))
    return check == v


# --- Keygen ---
# To generate a valid serial we need to solve: Mb16 * serial = v XOR name_block
# in GF(2^8). This requires the full Mb matrix and Gaussian elimination.
# ASSUMPTION: We attempt a brute-force approach for demonstration only.
# In practice the real algorithm needs the full Mb.

def keygen(name):
    """
    ASSUMPTION: Returns a serial (hex string) satisfying verify(name, serial).
    Without the full Mb matrix this cannot be correctly implemented.
    Raises NotImplementedError.
    """
    # ASSUMPTION: If we had the full invertible 16x16 Mb matrix we would compute
    #   serial = Mb^-1 * (v XOR name_block)
    raise NotImplementedError(
        "Cannot generate valid serial: full Mb matrix was truncated in writeup. "
        "Algorithm partially recovered only."
    )



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
