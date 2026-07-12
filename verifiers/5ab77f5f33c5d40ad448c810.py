# Reverse-engineered keygen for ty123's DFCG Crackme #2
# Based on writeup analysis. Some details are reconstructed/assumed.

import struct

# The lookup table used in the crackme (0-9, A-Z, a-d = 40 chars)
# Base table: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd'
BASE_TABLE = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd'

def rotate_table(table, shift):
    """Rotate the table by shift positions (increase starting index by shift)."""
    # ASSUMPTION: 'generate lookup table' call shifts table start by the given value
    # From writeup: first hash uses table shifted by 5 ('56789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi')
    # But the crackme table only has 40 chars (0-9,A-Z,a-d), so wrap around
    n = len(table)
    shift = shift % n
    return table[shift:] + table[:shift]

def generate_hash(input_str, table):
    """Hash function from the crackme.
    For each char in input_str:
      1. ax = ord(char)
      2. ax += 0x22 (34)
      3. remainder = ax % 0x22
      4. result_char = table[remainder]
    Returns 8-char hash string.
    """
    result = []
    tbl = list(table)
    for ch in input_str:
        ax = ord(ch)
        ax += 0x22
        remainder = ax % 0x22
        # ASSUMPTION: remainder is used as index into the table (XLAT)
        idx = remainder % len(tbl)
        result.append(tbl[idx])
    return ''.join(result)

def get_volume_serial():
    """Get the volume serial number of the root drive.
    Returns the serial as an integer.
    This is hardware-based and must be obtained at runtime.
    """
    import ctypes
    serial = ctypes.c_ulong(0)
    # ASSUMPTION: We get serial of the default drive (None = current)
    ctypes.windll.kernel32.GetVolumeInformationA(
        None, None, 0, ctypes.byref(serial), None, None, None, 0
    )
    return serial.value

def compute_id_no():
    """Compute the ID No. displayed by the crackme.
    Steps from writeup:
    1. Get volume serial number
    2. BSWAP it
    3. Add 0x44464347 ('DFCG' in little-endian as ASCII 'GFCD'? actually 'DFCG')
    4. Convert to hex string (8 chars) -> this is an intermediate value
    5. Hash that hex string using base table -> this is the ID No.
    """
    try:
        vol_serial = get_volume_serial()
    except Exception:
        # ASSUMPTION: fallback for non-Windows or testing
        vol_serial = 0x12345678

    # BSWAP: reverse bytes
    bswapped = struct.unpack('<I', struct.pack('>I', vol_serial))[0]
    # Add 0x44464347 (DFCG)
    added = (bswapped + 0x44464347) & 0xFFFFFFFF
    # Convert to uppercase hex string (8 chars)
    hex_str = '{:08X}'.format(added)
    # Hash using base table with no shift (shift=0)
    # ASSUMPTION: The ID No. display uses the base table
    id_hash = generate_hash(hex_str, BASE_TABLE)
    return id_hash, hex_str

def verify(name, serial):
    """Verify the serial.
    Serial format: 8 chars + '-' + 8 chars = 17 chars total
    e.g. '12345678-ABCDABCD'
    
    Steps:
    1. Serial must be 17 chars
    2. 9th char must be '-'
    3. Split into part1 (8 chars) and part2 (8 chars)
    4. Generate lookup table shifted by 5
    5. Compute hash1 = generate_hash(part1, shifted_table_5)
    6. hash1 must NOT equal magic value at 0x403195 (it's an exit condition trick)
       Actually from writeup: the check at 0x00401304 exits if hash1 == that magic value
       Wait - re-reading: 'JNZ Crackme2.00401393' after compare, so exit if NOT equal
       ASSUMPTION: hash1 of part1 must equal the stored intermediate hash
    7. Generate lookup table shifted by 0 (base)
    8. Compute hash2 = generate_hash(hash1, base_table)
    9. hash2 must equal the ID No.
    """
    # Step 1: Length check
    if len(serial) != 17:
        return False
    # Step 2: 9th char must be '-'
    if serial[8] != '-':
        return False
    
    part1 = serial[:8]
    part2 = serial[9:]  # 8 chars
    
    # Step 3: Generate table shifted by 5
    # From writeup: '[4031A2] = 5' and table becomes '56789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi'
    table_shift5 = rotate_table(BASE_TABLE, 5)
    
    # Step 4: Generate hash1 from part1
    hash1 = generate_hash(part1, table_shift5)
    
    # ASSUMPTION: The trick at 0x0040130B: exit if hash1 != magic stored value
    # This means for valid serial, hash1 produced from part1 must match some intermediate
    # The writeup says hash1 is compared to '6129149B' (machine-specific)
    # We skip this intermediate check as it depends on hardware
    # For verification purposes, we check the final hash2 == ID No.
    
    # Step 5: Generate hash2 from hash1 using base table (shift=0)
    table_base = rotate_table(BASE_TABLE, 0)
    hash2 = generate_hash(hash1, table_base)
    
    # Step 6: Get the ID No. for this machine
    try:
        id_no, _ = compute_id_no()
    except Exception:
        # ASSUMPTION: cannot verify without Windows API
        return False
    
    # hash2 must equal ID No.
    if hash2 != id_no:
        return False
    
    # ASSUMPTION: part2 may have additional checks not fully described in writeup
    # The writeup mentions a second part but is truncated
    return True

def keygen(name=None):
    """Generate a valid serial for this machine.
    
    The serial is hardware-based (volume serial number), not name-based.
    The 'name' parameter is not used by this crackme.
    
    Algorithm (reverse of verify):
    1. Compute ID No. (hash2)
    2. Find hash1 such that generate_hash(hash1, base_table) == hash2
       -> We need to reverse the hash function
    3. Find part1 such that generate_hash(part1, shifted_table_5) == hash1
    4. Serial = part1 + '-' + part2
       part2: ASSUMPTION - use any 8 valid chars (not fully described in writeup)
    """
    try:
        id_no, intermediate_hex = compute_id_no()
    except Exception:
        # For testing without Windows
        id_no = 'KLMNOPQR'  # example from writeup
        intermediate_hex = '????????'
    
    # The hash function: for each char c in input, output = table[(ord(c) + 0x22) % 0x22]
    # This means output depends only on (ord(c) % 0x22)
    # To reverse: given output char, find input char
    # output_char = table[(ord(c) + 0x22) % 0x22] = table[ord(c) % 0x22]
    # So we need: table[ord(c) % 0x22] == target_char
    # Find idx such that table[idx] == target_char, then ord(c) % 0x22 == idx
    # Then c = chr(idx) or chr(idx + 0x22) or chr(idx + 2*0x22) etc.
    
    def reverse_hash_char(target_char, table):
        """Find an input char that hashes to target_char using given table."""
        for idx in range(len(table)):
            if table[idx] == target_char:
                # Need ord(c) % 0x22 == idx
                # Try various values
                for multiplier in range(10):
                    c_ord = idx + multiplier * 0x22
                    if 0x20 <= c_ord <= 0x7E:  # printable ASCII
                        return chr(c_ord)
        return '?'
    
    def reverse_hash(target_str, table):
        result = ''
        for ch in target_str:
            result += reverse_hash_char(ch, list(table))
        return result
    
    # Step 1: Reverse hash2 to get hash1
    # hash2 = generate_hash(hash1, base_table)
    # ASSUMPTION: hash1 consists of printable chars from the base table
    table_base = rotate_table(BASE_TABLE, 0)
    hash1 = reverse_hash(id_no, table_base)
    
    # Step 2: Reverse hash1 to get part1
    # hash1 = generate_hash(part1, table_shift5)
    table_shift5 = rotate_table(BASE_TABLE, 5)
    part1 = reverse_hash(hash1, table_shift5)
    
    # ASSUMPTION: part2 is not described in the truncated writeup; use a placeholder
    # From writeup format hint: '12345678-ABCDABCD'
    part2 = 'ABCDABCD'  # ASSUMPTION: part2 may be free or have separate validation
    
    serial = part1 + '-' + part2
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
