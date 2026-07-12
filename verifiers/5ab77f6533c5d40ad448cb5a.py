# Reconstruction of haggar's keyme2 serial validation algorithm
# Based on writeup analysis from indomit and Ox87k solutions
#
# Serial format derived from the assembly checks:
# The serial is stored at 0x403250 (as a buffer)
# ECX points to position of ".no=" found between bytes 4-8 (0-indexed)
# Positions 19 and 28 (0-indexed from serial start) must be ':'
# Position 37 must be null terminator (serial length == 37)
# The substring ".no=" must appear exactly once at positions 4-8
# After ".no=" comes a 'serial' substring check
#
# Serial structure (36 chars total, 0-indexed):
# [0..3]   = prefix (before '.no=')
# [4..7]   = '.no=' (found once between positions 4 and 8)
# [8..18]  = part1 (11 chars)
# [19]     = ':'
# [20..27] = part2 (8 chars)
# [28]     = ':'
# [29..35] = part3 (7 chars)
# total length = 36 chars (position 36 is null = end)
#
# ASSUMPTION: The writeup says position 37 is end of string.
# Counting from 1 (as Olly offsets suggest ECX+0x1E=30th? Let me recount):
# From solution1: "19th, 28th is ':' and 37th is end of string"
# These appear to be 1-indexed offsets from ECX (the position of '.no=')
# ECX = index of '.no=' in buffer at 0x403250
# buffer[0x403250] is serial, ECX offset into it
# ASSUMPTION: positions 19,28 and length 37 are absolute 1-based positions
# in the serial string itself.
# So serial[18] == ':', serial[27] == ':', len(serial) == 36
#
# From point 0x04: after '.no=' is stripped, the remaining part
# (8 bytes = 2 dwords) is copied to 0x403280 as 'serial' substring
# Then at 0x004014FC: PUSH 0x00403280 with string "serial" is compared
# ASSUMPTION: the part after '.no=' up to first ':' must equal "serial"
# Actually from writeup: the program pushes 0x00403280 as String = "serial"
# suggesting the copied bytes spell "serial" -- but that's only 6 chars not 8
# ASSUMPTION: the 8 bytes copied = "serial" + padding or similar
#
# Let me re-read: ECX = position of '.no=' (an offset 4..8)
# The loop checks bytes 4..8 for '.no=' dword
# If '.no=' is at position p (0-indexed), then:
#   serial[p:p+4] == '.no='
#   serial[p+4:p+12] is copied to 0x403280 (2 dwords = 8 bytes)
# Then "serial" check: the copied string == "serial" (6 bytes)
# ASSUMPTION: serial[p+4:p+10] == "serial" (exactly)
#
# From checks:
#   - serial[18] == ':' (1-indexed 19th)
#   - serial[27] == ':' (1-indexed 28th)
#   - len(serial) == 36 (37th byte is null)
#   - '.no=' appears exactly once, at positions 4-8 (loop EAX=4..8)
#     actually EAX runs from 4 to 8 (CMP EAX,9 stops before 9),
#     these are byte offsets into buffer at 0x403250
#     ASSUMPTION: the serial buffer starts at 0x403250, EAX is offset
#     so '.no=' is at serial[4..7] meaning serial[4:8] == '.no='
#
# Additional numeric checks are truncated in the writeup.
# ASSUMPTION: there is a numeric computation on the parts around ':' separators
# that we cannot fully reconstruct from the truncated text.
#
# What we CAN reconstruct fully:
#   1. len(serial) == 36
#   2. serial[4:8] == '.no='
#   3. serial[18] == ':'
#   4. serial[27] == ':'
#   5. serial[8:14] starts with 'serial' (from the lstrcmpA check at 0x4014FC)
#      actually the copied region is serial[4..11] (2 dwords after the '.no=' position)
#      Wait: ECX holds the offset where '.no=' was found (EAX at that point)
#      Then at 0x00401391: MOV EBX,[403250+0] and [403250+4] 
#      -- these are the 2 dwords BEFORE '.no=' was zeroed out? No.
#      After zeroing '.no=': the remaining serial from position ECX
#      is repacked. Let me trust: copied region = serial after stripping '.no='
#      becomes "serial..." -- ASSUMPTION: serial[8:14] == 'serial'

import struct

def verify(name: str, serial: str) -> bool:
    """
    Verify a serial based on the known format checks from the crackme.
    NOTE: The full numeric/hash check is not available from the truncated writeup.
    This only verifies the format constraints that are described.
    """
    # Check 1: length must be 36
    if len(serial) != 36:
        return False
    
    # Check 2: '.no=' must appear exactly once at positions 4-8
    # Loop: EAX from 4 to 8, checks serial[EAX:EAX+4] == '.no='
    # Must find exactly one match (EBX==1)
    count = 0
    pos = -1
    for eax in range(4, 9):  # 4,5,6,7,8
        if serial[eax:eax+4] == '.no=':
            count += 1
            pos = eax
    if count != 1:
        return False
    
    # Check 3: absolute positions 19th and 28th (1-indexed) are ':'
    # i.e. serial[18] == ':' and serial[27] == ':'
    if serial[18] != ':':
        return False
    if serial[27] != ':':
        return False
    
    # Check 4: position 37 is end (already handled by len==36)
    
    # Check 5: after '.no=' (at pos), next 6 chars == 'serial'
    # From writeup: copied buffer compared with lstrcmpA to "serial"
    # ASSUMPTION: serial[pos+4:pos+10] == 'serial'
    if serial[pos+4:pos+10] != 'serial':
        return False
    
    # ASSUMPTION: There are additional numeric checks on the parts
    # between ':' delimiters that are not fully described in the writeup
    # (the writeup was truncated). We cannot verify those here.
    # For now, format checks pass.
    
    # ASSUMPTION: name is not used in serial computation
    # (no name-based check is described in the writeup)
    
    return True


def keygen(name: str) -> str:
    """
    Generate a serial that passes the known format checks.
    
    Format: [4 bytes prefix]['.no='][part after .no= including 'serial'][...][':'...][':'...]
    Total length: 36
    
    Structure:
      serial[0:4]   = 4-char prefix (must NOT contain '.no=' starting at positions 5..8)
      serial[4:8]   = '.no='
      serial[8:14]  = 'serial'  (satisfies the lstrcmpA check)
      serial[14:18] = 4 more chars (padding before first ':')
      serial[18]    = ':'
      serial[19:27] = 8 chars between colons
      serial[27]    = ':'
      serial[28:36] = 8 chars after last colon
    
    ASSUMPTION: The numeric parts between ':' can be arbitrary since
    the full hash/computation check is not described.
    """
    prefix = 'AAAA'           # serial[0:4] - 4 chars, no '.no=' here
    # serial[4:8] = '.no='
    after_no = 'serial'       # serial[8:14] = 'serial'
    pad1 = 'XXXX'            # serial[14:18] = 4 chars
    colon1 = ':'              # serial[18]
    mid = '12345678'         # serial[19:27] = 8 chars
    colon2 = ':'              # serial[27]
    tail = '87654321'        # serial[28:36] = 8 chars
    
    serial = prefix + '.no=' + after_no + pad1 + colon1 + mid + colon2 + tail
    
    assert len(serial) == 36, f'Length mismatch: {len(serial)}'
    
    # Verify the generated serial passes our format check
    if verify(name, serial):
        return serial
    else:
        raise ValueError('Generated serial failed format check')



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
