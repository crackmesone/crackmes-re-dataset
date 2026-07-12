# Reverse-engineered from the writeup for reverend's KeygenMe2
# The writeup was truncated, so only the name-processing steps and partial
# serial structure are known. The full serial1/serial2 check is PARTIAL.

def popcount32(x):
    """Count bits set in a 32-bit value."""
    x = x & 0xFFFFFFFF
    count = 0
    for i in range(32):
        if (x >> i) & 1:
            count += 1
    return count

def pad_name(name):
    """Pad name to 16 chars by repeating it."""
    if len(name) == 0:
        return name
    result = ''
    while len(result) < 16:
        result += name
    return result[:16]

def count_ones(padded_name):
    """Count every bit set to 1 in the 16-byte name array (4 dwords)."""
    import struct
    ebx = 0
    data = padded_name.encode('latin-1')[:16]
    # Pad to 16 bytes if needed
    data = data.ljust(16, b'\x00')
    for i in range(4):
        dword = struct.unpack_from('<I', data, i*4)[0]
        ebx += popcount32(dword)
    return ebx

def compute_nb_ones(padded_name):
    """Compute d_nbOnes as described in writeup.
    total_bits % 10 + 1, stored as float."""
    total = count_ones(padded_name)
    remainder = total % 10  # idiv 10 -> edx is remainder
    nb_ones = remainder + 1  # inc edx
    return float(nb_ones)

def name_block0(padded_name):
    """Process first 32-bit block of padded name."""
    import struct
    data = padded_name.encode('latin-1')[:16].ljust(16, b'\x00')
    r0 = struct.unpack_from('<I', data, 0)[0]
    # vmproc_name0_1:
    # mov r0, [name]
    # shl r0, 0x14  (20)
    # shr r0, 0x15  (21)
    # shl r0, 1
    r0 = (r0 << 20) & 0xFFFFFFFF
    r0 = (r0 >> 21) & 0xFFFFFFFF
    r0 = (r0 << 1) & 0xFFFFFFFF
    # vmproc_name0_2:
    # add r0, r0  => r0 *= 2
    # mul r0, 7
    # add r0, 0xE
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 * 7) & 0xFFFFFFFF
    r0 = (r0 + 0xE) & 0xFFFFFFFF
    return r0

def name_block1(padded_name):
    """Process second 32-bit block of padded name."""
    import struct
    data = padded_name.encode('latin-1')[:16].ljust(16, b'\x00')
    r0 = struct.unpack_from('<I', data, 4)[0]
    # vmproc_name1_1:
    # mov r0, [name+4]
    # shl r0, 0x14
    # shr r0, 0x15
    # shl r0, 1
    r0 = (r0 << 20) & 0xFFFFFFFF
    r0 = (r0 >> 21) & 0xFFFFFFFF
    r0 = (r0 << 1) & 0xFFFFFFFF
    # vmproc_name1_2:
    # add r0, r0  => *2
    # add r0, r0  => *2 again
    # mul r0, 3
    # add r0, 0x18
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 * 3) & 0xFFFFFFFF
    r0 = (r0 + 0x18) & 0xFFFFFFFF
    return r0

def name_block2(padded_name):
    """Process third 32-bit block of padded name."""
    import struct
    data = padded_name.encode('latin-1')[:16].ljust(16, b'\x00')
    r0 = struct.unpack_from('<I', data, 8)[0]
    # vmproc_name2_1:
    # mov r0, [name+8]
    # shl r0, 0x15  (21)
    # shr r0, 0x16  (22)
    # shl r0, 1
    r0 = (r0 << 21) & 0xFFFFFFFF
    r0 = (r0 >> 22) & 0xFFFFFFFF
    r0 = (r0 << 1) & 0xFFFFFFFF
    # vmproc_name2_2:
    # add r0, r0  => *2
    # add r0, r0  => *2 again
    # mul r0, 0xF
    # add r0, 0x104
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 * 0xF) & 0xFFFFFFFF
    r0 = (r0 + 0x104) & 0xFFFFFFFF
    return r0

# ASSUMPTION: Fourth block processing is not shown (writeup truncated).
# We assume a similar pattern for block3.
def name_block3(padded_name):
    import struct
    data = padded_name.encode('latin-1')[:16].ljust(16, b'\x00')
    r0 = struct.unpack_from('<I', data, 12)[0]
    # ASSUMPTION: Similar shift pattern to block2 but details unknown.
    # Using block1 pattern as placeholder.
    r0 = (r0 << 20) & 0xFFFFFFFF
    r0 = (r0 >> 21) & 0xFFFFFFFF
    r0 = (r0 << 1) & 0xFFFFFFFF
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 + r0) & 0xFFFFFFFF
    r0 = (r0 * 3) & 0xFFFFFFFF
    r0 = (r0 + 0x18) & 0xFFFFFFFF
    return r0

def compute_name_array(padded_name):
    """Compute the name_array of 4 dwords used in serial verification."""
    return [
        name_block0(padded_name),
        name_block1(padded_name),
        name_block2(padded_name),
        name_block3(padded_name),
    ]

def parse_serial1(serial1):
    """Parse Serial1: xxxx-xxxx-xxxx-xxxx (4 hex groups)."""
    parts = serial1.split('-')
    if len(parts) != 4:
        return None
    try:
        return [int(p, 16) for p in parts]
    except ValueError:
        return None

def parse_serial2(serial2):
    """Parse Serial2: 8 groups of 8 hex chars."""
    parts = serial2.split('-')
    if len(parts) != 8:
        return None
    try:
        return [int(p, 16) for p in parts]
    except ValueError:
        return None

# ASSUMPTION: The actual serial1 and serial2 verification against name_array
# and d_nbOnes is not fully described in the (truncated) writeup.
# The following verify() implements what IS known, and returns True if the
# format is correct and name processing works; the actual comparison is
# ASSUMED to match name_array values.
def verify(name, serial):
    """Verify name + combined serial string.
    serial should be in format: <serial1>|<serial2>
    where serial1 is xxxx-xxxx-xxxx-xxxx
    and serial2 is xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx
    """
    if not name or not serial:
        return False
    if '|' not in serial:
        return False
    s1_str, s2_str = serial.split('|', 1)
    s1 = parse_serial1(s1_str.strip())
    s2 = parse_serial2(s2_str.strip())
    if s1 is None or s2 is None:
        return False

    padded = pad_name(name)
    nb_ones = compute_nb_ones(padded)
    name_arr = compute_name_array(padded)

    # ASSUMPTION: Serial1 parts correspond to name_array values.
    # The exact relationship is not given in the truncated writeup.
    # We cannot fully verify without the complete algorithm.
    # Returning False as we cannot confirm correctness.
    # A real implementation would compare s1[i] and s2[i] to derived values.
    return False  # ASSUMPTION: Cannot complete without full writeup.

def keygen(name):
    """Generate serial for a given name (partial - only name processing known)."""
    if not name:
        return None
    padded = pad_name(name)
    nb_ones = compute_nb_ones(padded)
    name_arr = compute_name_array(padded)

    # ASSUMPTION: Serial1 is derived from name_array[0..3], each truncated to 16 bits.
    # ASSUMPTION: Serial2 is derived from name_array and nb_ones via further VM ops.
    # Since writeup is truncated we can only output known name derivatives.
    s1_parts = [name_arr[i] & 0xFFFF for i in range(4)]
    serial1 = '-'.join('%04X' % p for p in s1_parts)

    # ASSUMPTION: Serial2 parts unknown; use placeholder zeros.
    serial2 = '-'.join('%08X' % 0 for _ in range(8))

    print(f'Padded name : {padded}')
    print(f'nb_ones     : {nb_ones}')
    print(f'name_array  : {[hex(x) for x in name_arr]}')
    print(f'Serial1     : {serial1}')
    print(f'Serial2     : {serial2}')
    return serial1 + '|' + serial2


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
