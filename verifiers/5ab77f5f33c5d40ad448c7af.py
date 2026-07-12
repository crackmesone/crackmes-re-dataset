import struct

def _normalize_char(b):
    """
    Normalize a name character to uppercase A-Z range,
    with fallback values for out-of-range chars.
    Assembly logic:
      if bl < 0x41:
          add bl, 0x20
          if bl < 0x41: bl = 0x46
          goto upper_check
      upper_check:
      if bl > 0x5A:
          sub bl, 0x20
          if bl > 0x5A: bl = 0x47
          if bl < 0x41: bl = 0x53
    """
    bl = b
    if bl < 0x41:
        bl = bl + 0x20
        if bl < 0x41:
            bl = 0x46  # 'F'
    # now check upper bound
    if bl > 0x5A:
        bl = bl - 0x20
        if bl > 0x5A:
            bl = 0x47  # 'G'
        if bl < 0x41:
            bl = 0x53  # 'S'
    return bl

def keygen(name):
    """
    Generate the serial for the given name.
    Name must be 1..8 chars.
    Returns 16-char serial string.
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    if len(name_bytes) < 1 or len(name_bytes) > 8:
        raise ValueError("Name must be 1 to 8 characters long")

    # Step 1: Build table1 (16 bytes) initialized to predefined string
    # Predefined: SJKAZBVTECGIDFNG
    # In memory at offsets 0..15:
    # S J K A Z B V T E C G I D F N G
    # 53 4A 4B 41 5A 42 56 54 45 43 47 49 44 46 4E 47
    table1 = bytearray(b'SJKAZBVTECGIDFNG')

    # Step 2: For each name char, normalize and store into table1 at even positions (0,2,4,...)
    # i.e., table1[edx] where edx starts at 0 and increments by 2 for each name char
    name_len = len(name_bytes)
    edx = 0
    for i in range(name_len):
        bl = _normalize_char(name_bytes[i])
        table1[edx] = bl
        edx += 2

    # Step 3: Sum all 16 chars of table1
    char_sum = sum(table1) & 0xFFFFFFFF

    # eax = name_len (from GetDlgItemTextA return value)
    # eax = eax * 0xFF
    eax = (name_len * 0xFF) & 0xFFFFFFFF

    # edx = char_sum * eax
    edx = (char_sum * eax) & 0xFFFFFFFF

    # edx ^= 0xACEBDFAB
    edx = edx ^ 0xACEBDFAB

    # bswap edx
    edx_bytes = struct.pack('>I', edx & 0xFFFFFFFF)
    edx = struct.unpack('<I', edx_bytes)[0]

    # Step 4: Convert to uppercase hex string (wsprintf "%lX")
    hex_str = '%X' % (edx & 0xFFFFFFFF)
    # Pad to 8 chars
    hex_str = hex_str.upper()
    # temp1 buffer: up to 8 chars used
    temp1 = bytearray(hex_str.encode('ascii'))
    # Pad to 8 bytes if shorter
    while len(temp1) < 8:
        temp1.insert(0, ord('0'))

    # Step 5: For each char in temp1 (8 chars), if char < 0x3A (i.e., a digit), add 0x11
    for i in range(8):
        if temp1[i] < 0x3A:
            temp1[i] = (temp1[i] + 0x11) & 0xFF

    # Step 6: Copy temp1 into table1 at odd positions (1,3,5,...)
    edx2 = 0
    for i in range(8):
        table1[edx2 + 1] = temp1[i]
        edx2 += 2

    # Step 7: Add 5 to every odd-indexed byte in table1 (positions 1,3,5,...,15)
    ecx = 0
    while ecx < 16:
        table1[ecx + 1] = (table1[ecx + 1] + 5) & 0xFF
        ecx += 2

    # The serial is the 16-byte table1 as a string
    serial = table1.decode('latin-1')
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    """
    if len(serial) != 16:
        return False
    try:
        expected = keygen(name)
    except ValueError:
        return False
    return serial == expected



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
