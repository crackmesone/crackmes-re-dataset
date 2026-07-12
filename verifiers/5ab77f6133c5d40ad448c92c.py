import struct
import hashlib
import random

# The crackme validation algorithm (from Tutorial.txt by Kreet):
#
# 1. Serial must be >= 8 chars.
# 2. ebx = first_4_bytes_as_dword + next_4_bytes_as_dword
# 3. Loop serial_len times: ebx -= 666; ebx += 275064; ebx -= 45900
#    Net per iteration: ebx += (275064 - 666 - 45900) = 228498
# 4. Store ebx as magicval (4 bytes), pad to 32 bytes with zeros
# 5. Run modified MD5 (reywen's custom MD5) over these 32 bytes -> md5hash (16 bytes)
# 6. Loop 4 times: ebx -= md5hash[i*4 as dword]; ebx -= 0x3E8
# 7. ebx -= 0xCE99D6E6
# 8. if ebx == 0: good key
#
# ASSUMPTION: The 'modified MD5' is a custom function with altered constants.
# We do NOT know the exact modifications. The writeup says constants were changed.
# The bruteforcer found that the magic value going INTO the hash must be 0xD6BB87DA
# (a second solution the author found after ~30 minutes, which yields printable chars).
# We treat the target magicval = 0xD6BB87DA as the known-working constant.
#
# ASSUMPTION: We cannot reproduce the modified MD5 without reverse engineering it.
# Instead, we use the known relationship: the two 4-byte halves of the serial
# must sum (mod 2^32) to 0xD6BB87DA BEFORE the loop adjustment.
#
# The loop adjustment over serial_len iterations:
#   net_per_iter = 275064 - 666 - 45900 = 228498
# So: raw_sum + serial_len * 228498 = magicval (mod 2^32)
# => raw_sum = (magicval - serial_len * 228498) mod 2^32
#
# The serial is NOT keyed to the name (no name check visible in writeup).

MASK32 = 0xFFFFFFFF
NET_PER_ITER = 275064 - 666 - 45900  # = 228498
# Known valid magic value that produces a good hash result (from writeup)
TARGET_MAGIC = 0xD6BB87DA


def _compute_raw_sum_from_magic(magic_val: int, serial_len: int) -> int:
    """Reverse the loop to find what raw_sum must be.
    raw_sum + serial_len * NET_PER_ITER = magic_val (mod 2^32)
    """
    raw_sum = (magic_val - serial_len * NET_PER_ITER) & MASK32
    return raw_sum


def _dwords_to_serial(dw1: int, dw2: int) -> bytes:
    """Pack two dwords into 8 bytes (little-endian)."""
    return struct.pack('<II', dw1 & MASK32, dw2 & MASK32)


def verify(name: str, serial: str) -> bool:
    """
    Verify serial against the crackme algorithm.
    NOTE: The name is not used in the check (no name-based check shown in writeup).
    ASSUMPTION: The modified MD5 result for input 0xD6BB87DA (padded to 32 bytes)
    is treated as the known valid magic. We verify by checking:
      1. len(serial) >= 8
      2. The two dwords sum correctly after loop adjustment equals TARGET_MAGIC
    We CANNOT fully verify the MD5 step without the custom MD5 implementation.
    """
    if len(serial) < 8:
        return False

    serial_bytes = serial.encode('latin-1') if isinstance(serial, str) else serial

    # Read first 4 bytes and next 4 bytes as little-endian dwords
    dw1 = struct.unpack_from('<I', serial_bytes, 0)[0]
    dw2 = struct.unpack_from('<I', serial_bytes, 4)[0]

    ebx = (dw1 + dw2) & MASK32
    serial_len = len(serial_bytes)

    # Loop serial_len times
    for _ in range(serial_len):
        ebx = (ebx - 666) & MASK32
        ebx = (ebx + 275064) & MASK32
        ebx = (ebx - 45900) & MASK32

    # ASSUMPTION: We check if ebx == TARGET_MAGIC (the known valid pre-hash value).
    # The MD5 and subsequent steps are not reproducible without the custom MD5.
    # A full verify would also need the modified MD5 hash check.
    return ebx == TARGET_MAGIC


def keygen(name: str = '') -> str:
    """
    Generate a valid 8-character printable ASCII serial.
    The name is ignored (no name-based derivation in the algorithm).

    Strategy:
      - Use serial_len = 8
      - Compute required raw_sum = TARGET_MAGIC - 8 * NET_PER_ITER (mod 2^32)
      - Pick random printable dw1, compute dw2 = raw_sum - dw1 (mod 2^32)
      - Check both dwords consist of printable ASCII bytes (0x20-0x7E)
    """
    serial_len = 8
    raw_sum = _compute_raw_sum_from_magic(TARGET_MAGIC, serial_len)

    for _ in range(100000):
        # Generate random printable 4-byte sequence for first dword
        b1 = bytes([random.randint(0x20, 0x7E) for _ in range(4)])
        dw1 = struct.unpack('<I', b1)[0]
        dw2 = (raw_sum - dw1) & MASK32
        b2 = struct.pack('<I', dw2)
        # Check all bytes of dw2 are printable ASCII
        if all(0x20 <= byte <= 0x7E for byte in b2):
            serial = (b1 + b2).decode('latin-1')
            return serial

    # ASSUMPTION: If no printable solution found, return hex representation as fallback
    # This should rarely happen with TARGET_MAGIC = 0xD6BB87DA
    b1 = b'AAAA'
    dw1 = struct.unpack('<I', b1)[0]
    dw2 = (raw_sum - dw1) & MASK32
    b2 = struct.pack('<I', dw2)
    return (b1 + b2).decode('latin-1', errors='replace')



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
            print(_sv)
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
