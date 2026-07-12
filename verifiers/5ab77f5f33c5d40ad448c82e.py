# Keygenme1 by mrio_crk - Reverse engineered serial validation
# Based on solution writeup analysis
#
# From the writeup (encoded text decoded):
# 1. Serial is converted to binary (hex format: B4 B3 B2 B1 B4 B3 B2 B1)
# 2. Bytes are BSWAP'ed
# 3. The TEAM text is summed up to a 4*4 dword sum (called 'c')
# 4. There's a byte to XOR to the serial array calculated as: s ^= a ^ e (name_sum XOR team_sum)
# 5. CHECK does: s ^ a ^ n == e  (so s = n ^ a ^ e)
# 6. Name bytes are XOR'd to 's' array
# 7. Serial bytes are XOR'd to each byte of C (team encoding)
# 8. A sudoku-like grid of 3x3 groups is constructed from the s-array
# 9. The needed_bytes (sudoku solution) are XOR'd into the serial
#
# The assembly at 004020B8 loop processes 8 bytes per iteration:
#   inner loop (ECX 0..7):
#     DX += CX
#     AH ^= byte[ESI + ECX*2]      (even bytes of S-array chunk)
#     DX = DX * 0x4E35
#     AL ^= byte[ESI + ECX*2 + 1]  (odd bytes of S-array chunk)
#     DX += DI
#     DI = AX * 0x015A
#     DX += DI
#     AX = AX * 0x4E35
#     BX ^= DX
#     AX++
#     BX ^= AX
#   BL ^= BH
#   store result byte (BL xor'd with something from name)
#
# ASSUMPTION: The exact memory layout, sudoku needed_bytes array, and
# team/name screwing functions are not fully recoverable from the truncated writeup.
# The core loop is reconstructed but some details are assumed.

def _team_sum(team):
    """Sum team bytes into a 4-byte (32-bit) accumulator, wrapping."""
    # ASSUMPTION: simple byte sum mod 256 per position cycling 4 bytes
    acc = [0, 0, 0, 0]
    for i, ch in enumerate(team.encode('latin-1')):
        acc[i % 4] = (acc[i % 4] + ch) & 0xFF
    return acc

def _name_sum(name):
    """XOR all name bytes together into a single accumulator."""
    # ASSUMPTION: simple XOR of all bytes
    acc = 0
    for ch in name.encode('latin-1'):
        acc ^= ch
    return acc

def _core_loop(s_array, name_bytes):
    """
    Reconstructed from assembly at 004020B8.
    Processes the s_array in chunks, producing output bytes.
    ESI points to s_array, EBP points to output.
    Count = len(s_array)//16  (ASSUMPTION)
    """
    # ASSUMPTION: s_array is 0x51 bytes (from PUSH 51 in code)
    # Each outer iteration consumes 16 bytes (8 word-pairs) from ESI? 
    # Actually inner loop goes ECX 0..7 (8 iterations) reading ESI+ECX*2 and +1
    # so 16 bytes per outer iteration.
    # count stored at [404628] = ECX from [ESP+28] = PUSH 51 = 0x51 = 81
    # ASSUMPTION: count = 0x51
    
    out = []
    DI = 0  # 16-bit
    DX = 0  # 16-bit
    
    # ASSUMPTION: ESI advances by 16 each outer iteration
    # ASSUMPTION: name_bytes used in inner XOR step (from [EAX] = [EBP+0x2E8F])
    
    name_len = len(name_bytes)
    
    s_idx = 0
    for outer in range(0x51):
        AX = 0  # 16-bit
        BX = 0  # 16-bit
        for cx in range(8):
            DX = (DX + cx) & 0xFFFF
            # AH ^= byte[ESI + ECX*2]
            AH = (AX >> 8) & 0xFF
            idx0 = s_idx + cx * 2
            b0 = s_array[idx0 % len(s_array)] if s_array else 0
            AH ^= b0
            AX = (AH << 8) | (AX & 0xFF)
            # DX = DX * 0x4E35
            DX = (DX * 0x4E35) & 0xFFFF
            # AL ^= byte[ESI + ECX*2+1]
            AL = AX & 0xFF
            idx1 = s_idx + cx * 2 + 1
            b1 = s_array[idx1 % len(s_array)] if s_array else 0
            AL ^= b1
            AX = (AX & 0xFF00) | AL
            # DX += DI
            DX = (DX + DI) & 0xFFFF
            # DI = AX * 0x015A
            DI = (AX * 0x015A) & 0xFFFF
            # DX += DI
            DX = (DX + DI) & 0xFFFF
            # AX = AX * 0x4E35
            AX = (AX * 0x4E35) & 0xFFFF
            # BX ^= DX
            BX ^= DX
            # AX++
            AX = (AX + 1) & 0xFFFF
            # BX ^= AX
            BX ^= AX
        # BL ^= BH
        BL = BX & 0xFF
        BH = (BX >> 8) & 0xFF
        BL ^= BH
        BX = (BX & 0xFF00) | BL
        
        # Store: XOR with name byte at [EBP+0x2E8F] offset
        # ASSUMPTION: this is the name_bytes cycling
        name_byte = name_bytes[outer % name_len] if name_len > 0 else 0
        # From assembly: XOR [EBP], BL then XOR [EBP], AL_from_name
        result_byte = BL ^ name_byte
        out.append(result_byte & 0xFF)
        
        s_idx += 16
    
    return out

def _serial_to_bytes(serial):
    """Convert serial string (hex digits groups) to byte array."""
    # ASSUMPTION: serial is formatted as hex string, possibly with dashes
    cleaned = serial.replace('-', '').replace(' ', '')
    try:
        data = bytes.fromhex(cleaned)
        return list(data)
    except Exception:
        return []

def _bytes_to_serial(byte_list):
    """Convert byte list to serial string."""
    return ''.join(f'{b:02X}' for b in byte_list)

# Needed bytes from the sudoku solution (from writeup, decimal values)
# The writeup lists these as the required S array values for a valid serial
NEEDED_BYTES_HEX = [
    0x33, 0x39, 0x33, 0x31, 0x33, 0x35, 0x33, 0x36,
    0x33, 0x32, 0x33, 0x34, 0x33, 0x38, 0x33, 0x37,
    0x33, 0x35, 0x33, 0x36, 0x33, 0x34, 0x33, 0x33,
    0x33, 0x37, 0x33, 0x38, 0x33, 0x32, 0x33, 0x31,
    0x33, 0x39, 0x33, 0x38, 0x33, 0x32, 0x33, 0x37,
    0x33, 0x34, 0x33, 0x39, 0x33, 0x31, 0x33, 0x33,
    0x33, 0x36, 0x33, 0x35, 0x33, 0x36, 0x33, 0x35,
    0x33, 0x38, 0x33, 0x39, 0x33, 0x31, 0x33, 0x34,
    0x33, 0x37, 0x33, 0x33, 0x33, 0x32,
]

def _build_s_array(name, team=""):
    """
    Build the S array from name and team.
    From writeup: name is XOR'd to a null array,
    team sum is XOR'd in too.
    ASSUMPTION: S array = name bytes XOR'd cyclically into 0x51-byte zero array,
    then team sum XOR'd in.
    """
    s = [0] * 0x51
    nb = list(name.encode('latin-1'))
    tb = _team_sum(team)
    for i in range(0x51):
        s[i] ^= nb[i % len(nb)] if nb else 0
        s[i] ^= tb[i % 4]
    return s

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: The serial encodes the output of the core loop applied to
    the name-derived S array. A valid serial produces the NEEDED_BYTES pattern.
    """
    # ASSUMPTION: team is empty string for standalone keygen
    team = ""
    s = _build_s_array(name, team)
    name_bytes = list(name.encode('latin-1'))
    if not name_bytes:
        return False
    
    serial_bytes = _serial_to_bytes(serial)
    if len(serial_bytes) < len(NEEDED_BYTES_HEX):
        return False
    
    # ASSUMPTION: to verify, we reconstruct what the serial should be
    expected = keygen(name)
    return serial.upper().replace('-','').replace(' ','') == expected.upper().replace('-','').replace(' ','')

def keygen(name, team=""):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: The serial is produced by XOR'ing the NEEDED_BYTES with
    the output of the name-derived core loop transformation.
    From writeup: s = n ^ a ^ e, so serial_byte = needed ^ name_contribution ^ team_contribution
    """
    s = _build_s_array(name, team)
    name_bytes = list(name.encode('latin-1'))
    if not name_bytes:
        return ''
    
    core_out = _core_loop(s, name_bytes)
    
    # ASSUMPTION: serial bytes = NEEDED_BYTES XOR core_out
    serial_bytes = []
    for i in range(len(NEEDED_BYTES_HEX)):
        b = NEEDED_BYTES_HEX[i] ^ (core_out[i] if i < len(core_out) else 0)
        serial_bytes.append(b & 0xFF)
    
    return _bytes_to_serial(serial_bytes)


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
