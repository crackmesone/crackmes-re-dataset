import struct
import hashlib

# We need RIPEMD-128. Python's hashlib may or may not support it.
# We'll try hashlib first, then fall back to a pure-Python implementation stub.

def ripemd128(data: bytes) -> bytes:
    """Compute RIPEMD-128 hash of data."""
    try:
        h = hashlib.new('ripemd128')
        h.update(data)
        return h.digest()
    except ValueError:
        # ASSUMPTION: If ripemd128 is not available in hashlib, we cannot proceed.
        # Some Python builds (e.g. OpenSSL 3.x) drop RIPEMD.
        raise NotImplementedError("RIPEMD-128 not available in hashlib on this platform.")


def compute_namehash(name: str) -> bytes:
    """Compute RIPEMD-128 of the name string (as used by the real KeyCheck)."""
    return ripemd128(name.encode('latin-1'))


def transform_namehash(raw: bytes) -> list:
    """
    The KeyCheck routine does:
      - For ecx in 0..6: shr byte namehash[ecx*2], 1  (shift-right even-indexed bytes)
      - For ecx in 0..6: set byte namehash[ecx*2+1] = 0 (zero odd-indexed bytes)
    So we get 7 'short' (word) values, each = (even_byte >> 1) with the odd byte zeroed.
    The FPU loop uses 'fild word ptr ds:namehash[ebx]' with ebx incrementing by 2,
    so it reads 7 signed 16-bit words.
    """
    arr = bytearray(raw)  # 16 bytes for RIPEMD-128
    for i in range(7):
        arr[i * 2] = arr[i * 2] >> 1
        arr[i * 2 + 1] = 0
    # Read as 7 signed 16-bit little-endian words
    words = []
    for i in range(7):
        w = struct.unpack_from('<h', arr, i * 2)[0]
        words.append(w)
    return words


def subtract_loop(serial_bytes: bytearray) -> bytearray:
    """
    subtract_loop: subtracts 17-20 from usrSerial bytes in a cycle.
    cl starts at 17, increments to 20, then resets to 17.
    Applied to all 64 bytes.
    """
    result = bytearray(serial_bytes)
    cl = 17
    for ebx in range(64):
        result[ebx] = (result[ebx] - cl) & 0xFF
        cl += 1
        if cl == 21:
            cl = 17
    return result


def mult_asc2hex(serial_bytes: bytearray, ebx_start: int, count: int = 2) -> int:
    """
    MultAsc2Hex: converts ASCII hex nibbles from serial into an integer.
    The writeup shows calls with ebx=1,2,3,4,4,5,6 as starting offsets (1-based)
    and the destination is 8 bytes each (magic1..magic7).
    ASSUMPTION: MultAsc2Hex reads 'count' pairs of hex chars from usrSerial
    starting at offset (ebx_start-1)*some_stride and converts them.
    The exact stride/count per call is not fully given in the truncated writeup.
    We assume each call reads 2 hex-ASCII chars (= 1 byte) from position
    based on ebx index, producing a word-sized value stored in the magic slot.
    ASSUMPTION: The exact indexing into usrSerial for MultAsc2Hex is not fully
    described. We assume it reads consecutive pairs of hex chars.
    """
    # ASSUMPTION: each magic slot corresponds to reading 2 hex chars from
    # serial_bytes at position (ebx_start-1)*2
    offset = (ebx_start - 1) * 2
    hi = serial_bytes[offset] & 0xFF
    lo = serial_bytes[offset + 1] & 0xFF
    return (hi << 8) | lo


def fpu_power7(val: int) -> float:
    """Raise val to the 7th power (as done by the FPU exp_loop)."""
    result = float(val)
    for _ in range(6):  # fimul 6 more times = total 7th power
        result *= val
    return result


def keycheck(name: str, serial: str) -> bool:
    """
    Implements the real KeyCheck algorithm as described in the writeup.
    WARNING: The writeup is truncated; the comparison logic at the end
    (what the magic values are compared against) is not fully given.
    This implements what IS described.
    """
    if len(serial) != 64:
        return False
    if not name:
        return False

    # Step 1: Compute RIPEMD-128 of name
    raw_hash = compute_namehash(name)

    # Step 2: Transform namehash (shr even bytes, zero odd bytes)
    words = transform_namehash(raw_hash)
    # words[0..6] are the 7 name-hash words used in FPU loop

    # Step 3: Apply subtract_loop to serial bytes
    serial_bytes = bytearray(serial.encode('latin-1'))
    modified_serial = subtract_loop(serial_bytes)

    # Step 4: MultAsc2Hex - convert serial to magic values
    # ASSUMPTION: ebx values 1-7 index into modified_serial to extract magic values
    magic = []
    for ebx in range(1, 8):
        magic.append(mult_asc2hex(modified_serial, ebx))

    # Step 5: FPU loop - raise each word to the 7th power
    powered = [fpu_power7(w) for w in words]

    # Step 6: ASSUMPTION: The comparison checks that magic[i] == powered[i] (or some
    # derived comparison). The writeup is truncated and does not show the full
    # comparison logic. We cannot implement the exact final check.
    # ASSUMPTION: comparison is magic[i] == int(powered[i]) for i in 0..6
    for i in range(7):
        if magic[i] != int(powered[i]):
            return False
    return True


def verify(name: str, serial: str) -> bool:
    """Main verify function."""
    try:
        return keycheck(name, serial)
    except NotImplementedError:
        raise


def keygen(name: str) -> str:
    """
    Keygen: given a name, compute the serial.
    Algorithm (reverse of KeyCheck):
      1. Compute RIPEMD-128 of name -> transform -> 7 words
      2. Raise each word to 7th power -> magic values
      3. ASSUMPTION: Encode magic values back into serial hex-ASCII pairs
      4. Reverse the subtract_loop to recover original serial bytes
    ASSUMPTION: The exact encoding of magic values into the 64-char serial
    is not fully described in the (truncated) writeup.
    """
    # Step 1
    raw_hash = compute_namehash(name)
    words = transform_namehash(raw_hash)

    # Step 2: raise to 7th power
    powered = [int(fpu_power7(w)) for w in words]

    # Step 3: ASSUMPTION: Build a 64-byte serial from powered values
    # We need 64 bytes total. We have 7 values.
    # ASSUMPTION: Each powered value is encoded as a 16-char hex string,
    # but that gives 7*16=112 > 64. Use 4-char hex per value for 7 values = 28 chars,
    # pad the rest with zeros. This is highly speculative.
    serial_bytes = bytearray(64)
    for i, val in enumerate(powered):
        # ASSUMPTION: store low 16 bits as 2 bytes at offset (i+1-1)*2
        lo = val & 0xFFFF
        serial_bytes[(i) * 2] = (lo >> 8) & 0xFF
        serial_bytes[(i) * 2 + 1] = lo & 0xFF

    # Step 4: Reverse subtract_loop
    # subtract_loop: result[ebx] = (original[ebx] - cl) & 0xFF
    # So: original[ebx] = (result[ebx] + cl) & 0xFF
    cl = 17
    original_serial = bytearray(64)
    for ebx in range(64):
        original_serial[ebx] = (serial_bytes[ebx] + cl) & 0xFF
        cl += 1
        if cl == 21:
            cl = 17

    # Convert to string, keeping printable chars
    try:
        return original_serial.decode('latin-1')
    except Exception:
        return original_serial.hex()



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
