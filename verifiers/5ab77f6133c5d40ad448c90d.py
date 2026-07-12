import ctypes
import struct

# ============================================================
# keygen for malfunction's crackme #5 "Digital Arithmetic"
# Reconstructed from andrewl's keygen source (2/2009)
# ============================================================

# Global RNG state
g_CurrentRandomValue = 0


def _srand_from_8dwords(data32: list):
    """Seed the RNG by summing 8 DWORDs."""
    global g_CurrentRandomValue
    g_CurrentRandomValue = 0
    for d in data32[:8]:
        g_CurrentRandomValue = (g_CurrentRandomValue + d) & 0xFFFFFFFF


def _rand() -> int:
    """LCG RNG matching the assembly."""
    global g_CurrentRandomValue
    ecx = (g_CurrentRandomValue * 0x343FD + 0x269EC3) & 0xFFFFFFFF
    g_CurrentRandomValue = ecx
    return (ecx >> 16) & 0x7FFF


def _swap_random_8bytes(arr: bytearray):
    """Randomly swap two bytes in an 8-byte array."""
    a = _rand() & 7
    b = _rand() & 7
    if a != b:
        arr[a], arr[b] = arr[b], arr[a]


def _pad_name(name_bytes: bytes) -> bytearray:
    """
    PadName: pads/repeats name bytes into a 0x20-byte (32-byte) buffer.
    Mirrors the assembly loop:
      - copies bytes from name cyclically into positions [len..0x1F]
    """
    buf = bytearray(0x20)
    length = len(name_bytes)
    # Copy the original name into the start of the buffer
    for i in range(min(length, 0x20)):
        buf[i] = name_bytes[i]
    # Fill remaining bytes cyclically from the existing content
    edi = length
    esi = length
    while edi < 0x20:
        esi -= 1
        if esi < 0:
            esi = length - 1  # ASSUMPTION: wraps to end of original name region
        buf[edi] = buf[esi]
        edi += 1
    return buf


def _make_8byte_hash(name32: bytearray) -> bytearray:
    """
    Make8ByteHash: processes the 32-byte padded name and produces an 8-byte hash.
    Assembly logic:
      esi = name32 + 0x1F  (start from the end)
      ecx = 0x20 (32 iterations)
      edx = 0xAC (initial)
      edi = hash_buf + 7  (fill hash from end)
      loop:
        al = name32[esi]
        edx (dl) += al
        swap dl, dh
        if ecx <= 8: hash[edi] = dl; edi--
        name32[esi] = dl
        esi--; ecx--
    """
    buf = bytearray(name32)  # work on a copy
    hash_buf = bytearray(8)
    esi = 0x1F
    ecx = 0x20
    edx = 0xAC  # only low 16 bits matter (dl/dh)
    dl = edx & 0xFF
    dh = (edx >> 8) & 0xFF
    edi = 7  # index into hash_buf

    while ecx > 0:
        al = buf[esi]
        dl = (dl + al) & 0xFF
        dl, dh = dh, dl  # xchg dl, dh
        if ecx <= 8:
            hash_buf[edi] = dl
            edi -= 1
        buf[esi] = dl
        esi -= 1
        ecx -= 1

    return hash_buf


def _make_random_array_20h(seed_data: bytearray) -> bytearray:
    """
    MakeRandomArray20h: generates a 0x20-byte array using the RNG.
    ASSUMPTION: fills array with rand() bytes and does random swaps.
    The full function was truncated in the writeup; this is a best-effort reconstruction.
    """
    arr = bytearray(0x20)
    for i in range(0x20):
        arr[i] = _rand() & 0xFF
    # ASSUMPTION: performs some number of random swaps (truncated in source)
    for _ in range(0x20):
        _swap_random_8bytes(arr)
    return arr


def _process_name(name: str):
    """
    Main name processing:
    1. Pad name to 32 bytes
    2. Make 8-byte hash
    3. Interpret hash as 2 DWORDs to seed RNG
    4. Generate random array
    Returns the 8-byte hash and the random array.
    """
    name_bytes = name.encode('ascii', errors='replace')
    padded = _pad_name(name_bytes)
    hash8 = _make_8byte_hash(padded)

    # Seed RNG from hash: treat hash as 2 DWORDs, replicate across 8 slots
    # ASSUMPTION: the 8-dword seed is constructed by repeating the 2 DWORDs from the hash
    dw0 = struct.unpack_from('<I', hash8, 0)[0]
    dw1 = struct.unpack_from('<I', hash8, 4)[0]
    seed_dwords = [dw0, dw1, dw0, dw1, dw0, dw1, dw0, dw1]
    _srand_from_8dwords(seed_dwords)

    rand_arr = _make_random_array_20h(hash8)
    return hash8, rand_arr


# ============================================================
# ASSUMPTION: The serial validation compares a serial derived
# from the name hash and/or random array. The exact serial
# format (digits, separators, length) was truncated in the
# writeup. The keygen below produces a hex representation of
# the 8-byte hash as a best-effort serial.
# ============================================================

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: serial is the hex encoding of the 8-byte name hash.
    The actual serial format was not fully described in the writeup.
    """
    hash8, rand_arr = _process_name(name)
    # ASSUMPTION: serial format unknown; returning hex of hash as placeholder
    serial = hash8.hex().upper()
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    ASSUMPTION: serial matches the hex of the 8-byte name hash.
    """
    expected = keygen(name)
    # Normalize comparison
    return serial.strip().upper() == expected.upper()



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
