# Reconstructed keygen for ReWrit's Crackme #10
# Based on the assembly source provided in the solution writeup

MAX_PATH = 260

# Data tables from the .data section
numString = b"-+xX0123456789abcdef0123456789ABCDEF-+xX0123456789abcdefABCDEF"
magString = b"bDhd0UqQRV4X8"


def lstrlen(s: bytes) -> int:
    """Return length of null-terminated byte string."""
    try:
        return s.index(0)
    except ValueError:
        return len(s)


def to_buf(s: str, size: int = MAX_PATH) -> bytearray:
    """Convert string to a zero-padded bytearray of given size."""
    b = bytearray(size)
    enc = s.encode('ascii', errors='replace')
    for i, c in enumerate(enc[:size]):
        b[i] = c
    return b


def CalculateSeed(pString: bytearray) -> int:
    """
    Calculates a seed value from the name string.
    """
    length = lstrlen(pString)
    counter = length

    # d = len * 5 * 10 = len * 50... let's trace carefully:
    # eax = len
    # eax = len*4 + len = len*5
    # d = len*5 * (1 + 16) ... wait, let's retrace:
    #
    # eax = len
    # eax <<= 2  => len*4
    # eax += ebx (ebx=len) => len*5
    # ebx = eax = len*5
    # eax <<= 4  => len*5*16 = len*80
    # eax += ebx => len*80 + len*5 = len*85
    # d = len*85
    #
    # seed:
    # ebx = d = len*85
    # eax = d*8 = len*680
    # eax -= ebx => len*680 - len*85 = len*595
    # eax <<= 1  => len*1190
    # seed = len * 1190

    d = length * 85
    seed = length * 1190

    multiplier = 0
    edi = 0  # index into pString

    for i in range(counter):
        ebx = multiplier * d
        char_val = pString[edi] & 0xFF
        edi += 1
        multiplier = (char_val + ebx) & 0xFFFFFFFF
        d = (d * seed) & 0xFFFFFFFF

    result = multiplier & 0x7FFFFFFF
    return result


def CalculateString(dwSeed: int, numSeed_buf: bytearray) -> None:
    """
    Fills numSeed_buf (from back) with digit characters derived from dwSeed.
    Uses 0xCCCCCCCD trick for fast division by 10.
    numString offset +4 gives the digit characters.
    """
    # The numString is used: numstring+4 is index into it
    # The remainder gives the digit index into numString[4:]
    # numString = b"-+xX0123456789abcdef..."
    # numString[4:] = b"0123456789abcdef..."
    # So remainder maps to numString[4 + remainder*2] (shl eax,1 before indexing)
    # Wait: 'lea eax, [edx+edx*4]' => eax = edx*5
    # 'shl eax, 1' => eax = edx*10
    # Then index = eax = remainder*10
    # mov eax, [ecx+edi+4] => byte at numString[4 + remainder*10]
    # But we take 'al' (byte), so single byte

    ecx = dwSeed
    # ebx = pString + MAX_PATH - 1  (pointer to end of numSeed buffer)
    # We write from position MAX_PATH-2 down to some position
    # We'll track the position as an index (from end)
    pos = MAX_PATH - 2  # 0-indexed position in numSeed_buf

    # ASSUMPTION: The loop writes digits from high to low into numSeed_buf
    # from position MAX_PATH-1 backward, and stops when edx==0
    # The first iteration always writes at least one digit.

    while True:
        # Fast division by 10 using 0xCCCCCCCD
        eax = ecx
        # mul esi (esi = 0xCCCCCCCD), 64-bit result
        product = (eax * 0xCCCCCCCD) & 0xFFFFFFFFFFFFFFFF
        edx = (product >> 32) & 0xFFFFFFFF
        edx = edx >> 3  # shr edx, 3 => edx = floor(eax / 10)

        # remainder = eax - edx*10
        remainder = ecx - edx * 10

        # index into numString: remainder*10 (from shl eax,1 after lea eax,[edx+edx*4])
        # ASSUMPTION: index = remainder * 10, then take byte from numString[4 + index]
        idx = remainder * 10
        digit_byte = numString[4 + idx]  # single byte

        numSeed_buf[pos] = digit_byte
        pos -= 1

        ecx = edx  # seed = quotient
        if edx == 0:
            break


def GetNumStringSizeReverse(numSeed_buf: bytearray) -> int:
    """
    Scans from position MAX_PATH-1 backward to find non-zero bytes.
    Moves the found bytes to the front of the buffer.
    Returns the count.
    """
    # Find the start of non-zero content from the end
    esi = MAX_PATH - 1
    count = 0
    while esi >= 0 and numSeed_buf[esi] == 0:
        esi -= 1
    # Now esi points to the last non-zero byte
    # Count from esi backward until we hit a zero
    end = esi
    while esi >= 0 and numSeed_buf[esi] != 0:
        esi -= 1
        count += 1
    esi += 1  # inc esi to point to first non-zero

    # Move bytes from esi..end to front
    for i in range(count):
        numSeed_buf[i] = numSeed_buf[esi + i]

    return count


def AddNumString(numSeed_buf: bytearray, size: int) -> int:
    """
    Sums bytes in the buffer and adds 0x30000.
    Returns eax = 0x30000 + sum of bytes.
    """
    # ASSUMPTION: The return value is used but the crackme only uses 'eax'
    # from this call for... actually looking at main: the result is unused (pop eax discards it)
    # The 'push eax / pop eax' around AddNumString means eax (size) is preserved.
    # AddNumString doesn't change the external state that matters here.
    acc = 0x30000
    for i in range(size):
        acc = (acc + numSeed_buf[i]) & 0xFFFFFFFF
    return acc


def CalculateSerial(numSeed_buf: bytearray, dwSize: int, xxxSeed_buf: bytearray) -> None:
    """
    Builds the serial string in xxxSeed_buf.
    """
    edi = 0  # index into xxxSeed_buf
    ecx = 0
    while ecx < dwSize:
        cl = ecx & 0xFF
        eax_idx = ecx
        if cl in (2, 4, 6, 8, 10):
            eax_idx = ecx + 3

        al = numSeed_buf[eax_idx] if eax_idx < len(numSeed_buf) else 0

        if al != 0:
            al = al - 0x30  # subtract '0'
        else:
            al = 0

        # ASSUMPTION: al is now an index (0-based digit) into magString
        mag_idx = al % len(magString)
        mapped = magString[mag_idx]

        xxxSeed_buf[edi] = mapped
        idi_save = edi
        edi += 1

        ecx += 1


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    Name must be at least 3 chars, no spaces.
    """
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters long")
    if ' ' in name:
        raise ValueError("No spaces allowed in name")

    numSeed_buf = bytearray(MAX_PATH)
    xxxSeed_buf = bytearray(MAX_PATH)
    pString = to_buf(name)

    seed = CalculateSeed(pString)
    CalculateString(seed, numSeed_buf)
    size = GetNumStringSizeReverse(numSeed_buf)
    AddNumString(numSeed_buf, size)
    CalculateSerial(numSeed_buf, size, xxxSeed_buf)

    # Extract the serial as null-terminated string
    result = bytearray()
    for b in xxxSeed_buf:
        if b == 0:
            break
        result.append(b)
    return result.decode('ascii', errors='replace')


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair by generating the expected serial and comparing.
    """
    try:
        expected = keygen(name)
        return expected == serial
    except ValueError:
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
