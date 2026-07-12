# Password check algorithm for therapy's crackme #2
# The crackme stores a 15-character password as 120 bytes at 0x0040201A
# Each char is encoded as 8 ASCII hex-nibble bytes (4 bytes per nibble)
# The check: for each of the 120 encoded bytes, (0xFF - encoded_byte) must equal the stored table byte
# Equivalently: the password, when hex-expanded, must XOR/complement match the table

# The stored table bytes at 0x0040201A (every 4th byte matters for the actual check,
# but ALL 120 bytes are compared against the expanded password)
# From the writeup, the table is:
TABLE = bytes([
    0xCC, 0xCC, 0xCC, 0xC8,  0xCC, 0xCC, 0xCC, 0xC6,
    0xCC, 0xCC, 0xCC, 0xC9,  0xCC, 0xCC, 0xCC, 0xCA,
    0xCC, 0xCC, 0xCC, 0xCA,  0xCC, 0xCC, 0xCC, 0xCC,
    0xCC, 0xCC, 0xCC, 0xCD,  0xCC, 0xCC, 0xCC, 0xCF,
    0xCC, 0xCC, 0xCC, 0xC8,  0xCC, 0xCC, 0xCC, 0xC6,
    0xCC, 0xCC, 0xCC, 0xC9,  0xCC, 0xCB, 0xCC, 0xCA,  # note: index 45 is 0xCB (out-of-sequence)
    0xCC, 0xCC, 0xCC, 0xCA,  0xCC, 0xCC, 0xCC, 0xCA,
    0xCC, 0xCC, 0xCC, 0xCD,  0xCC, 0xCC, 0xCC, 0xCF,
    0xCC, 0xCC, 0xCC, 0xC9,  0xCC, 0xCC, 0xCC, 0xCB,
    0xCC, 0xCC, 0xCC, 0xC9,  0xCC, 0xCC, 0xCC, 0xC6,
    0xCC, 0xCC, 0xCC, 0xCB,  0xCC, 0xCC, 0xCC, 0xCB,
    0xCC, 0xCC, 0xCC, 0xCD,  0xCC, 0xCC, 0xCC, 0xCF,
    0xCC, 0xCC, 0xCC, 0xC9,  0xCC, 0xCC, 0xCC, 0xC6,
    0xCC, 0xCC, 0xCC, 0xCA,  0xCC, 0xCC, 0xCC, 0xCB,
    0xCC, 0xCC, 0xCC, 0xCD,  0xCC, 0xCC, 0xCC, 0xCE,
])

# The password length must be 15 characters.
# Each character is encoded into 8 bytes as follows:
#   high_nibble = (char >> 4)
#   low_nibble  = (char & 0x0F)
#   if high_nibble > 9: high_nibble_byte = high_nibble + 0x36  else: high_nibble_byte = high_nibble + 0x30
#   if low_nibble  > 9: low_nibble_byte  = low_nibble  + 0x36  else: low_nibble_byte  = low_nibble  + 0x30
#   encoded[2*i]   = high_nibble_byte
#   encoded[2*i+1] = low_nibble_byte
# Wait - actually each char produces 2 bytes, and the grid shows 120 bytes for 15 chars => 8 bytes per char
# The encoding is recursive hex expansion:
#   char -> hex string of 2 nibble chars -> each nibble char -> hex string of 2 nibble chars
# So 'y' = 0x79 -> '7','9' -> '37','39' -> '33','37','33','39'
# That gives 8 bytes per character (2 levels of hex expansion)

def char_to_8bytes(c):
    """Expand a single character into 8 ASCII bytes via two levels of hex encoding."""
    byte_val = ord(c)
    # Level 1: get high and low nibble ASCII hex chars
    def nibble_to_hex_char(n):
        if n <= 9:
            return 0x30 + n  # '0'-'9'
        else:
            return 0x36 + n  # 'a'-'f' style (0x36+10=0x40? let's check: 0x36+10=70='F'? no)
            # Actually from code: if > 9: add 0x36, else add 0x30
            # For nibble=0xA(10): 0x36+10=0x40='@'? That seems wrong.
            # But for printable ASCII (0x20-0x7E), high nibble is 2,3,4,5,6,7 => all <=9 after >>4
            # Low nibble can be 0-F
            # From example: 'y'=0x79, high=7->0x30+7=0x37='7', low=9->0x30+9=0x39='9'
            # Then '7'=0x37, high=3->0x33='3', low=7->0x37='7'
            # Then '9'=0x39, high=3->0x33='3', low=9->0x39='9'
            # Result: 33 37 33 39 = '3','7','3','9' matching the example
    
    hi1 = (byte_val >> 4) & 0x0F
    lo1 = byte_val & 0x0F
    hi1_char = nibble_to_hex_char(hi1)
    lo1_char = nibble_to_hex_char(lo1)
    
    # Level 2: expand each of those
    def expand_byte(b):
        hi = (b >> 4) & 0x0F
        lo = b & 0x0F
        return nibble_to_hex_char(hi), nibble_to_hex_char(lo)
    
    b0, b1 = expand_byte(hi1_char)
    b2, b3 = expand_byte(lo1_char)
    return bytes([b0, b1, b2, b3])

def password_to_expanded(password):
    """Convert a 15-char password into 120-byte expanded form (but only 30 meaningful bytes)."""
    # Actually from code analysis: each char -> 2 bytes (stored at positions 2*i and 2*i+1)
    # But the table has 120 bytes... let me re-read.
    # The writeup says: 120 codes, 30 password codes (every 4th), 89 CC codes, 1 out-of-sequence
    # So the expanded password has 30 bytes (2 per char for 15 chars)
    # But the table is 120 bytes and checked byte-by-byte
    # The 'CC' bytes in table correspond to '33' bytes (0xFF-0x33=0xCC) in expanded password
    # The expanded password from '123456789012345' shows 33 33 33 31 33 33 33 32...
    # So each char produces 8 bytes in the expanded buffer (stored at 2*i and 2*i+1 but the buffer
    # is actually the result of the recursive expansion written to positions 2*i, 2*i+1 in one pass
    # but the INPUT to that pass is already the 2-byte-per-char expansion of the original)
    # Actually looking more carefully: the function at 0x401214 takes the password and writes
    # 2 bytes per input char at positions 2*i and 2*i+1 in the output buffer.
    # The result for '123456789012345' is 30 bytes. But the comparison is over 120 bytes.
    # The function must be called TWICE (or on its own output) to produce 120 bytes from 15 chars.
    # 15 -> 30 -> 60? No. 15*8=120. So it's called twice on the result.
    result = b''
    for c in password:
        b = ord(c)
        hi = (b >> 4) & 0x0F
        lo = b & 0x0F
        hi_char = (0x30 + hi) if hi <= 9 else (0x36 + hi)
        lo_char = (0x30 + lo) if lo <= 9 else (0x36 + lo)
        result += bytes([hi_char, lo_char])
    return result

def double_expand(password):
    """Two-level hex expansion: password -> 30 bytes -> 120 bytes."""
    first = password_to_expanded(password)
    second = password_to_expanded(first.decode('latin-1'))
    return second

def verify(name, serial):
    # name is not used in this crackme
    if len(serial) != 15:
        return False
    expanded = double_expand(serial)
    if len(expanded) != 120:
        return False
    # Check: for each of the 120 bytes, (0xFF - expanded[i]) == TABLE[i]
    # Equivalently: expanded[i] + TABLE[i] == 0xFF
    good_count = 0
    for i in range(120):
        if (0xFF - expanded[i]) & 0xFF == TABLE[i]:
            good_count += 1
    # Must have 120 good codes (0x78 = 120 in the CMP)
    # Wait the code says CMP counter2, 0x78 => 0x78 = 120 decimal
    # ASSUMPTION: all 120 bytes must match for correct (good_count == 120)
    return good_count == 120

def recover_password_from_table():
    """Reverse the table to find the password."""
    # The table at 0x0040201A has 120 bytes, 8 per character
    # Each char c produces 8 bytes via double_expand
    # We can brute-force printable ASCII chars and see which 8-byte expansion matches
    
    # Build lookup: 8-byte-expansion -> char
    lookup = {}
    for code in range(32, 127):
        c = chr(code)
        exp = double_expand(c)
        # What does (0xFF - b) for each b give us?
        inv = bytes([(0xFF - b) & 0xFF for b in exp])
        lookup[inv] = c
    
    password = ''
    for i in range(15):
        chunk = TABLE[i*8:(i+1)*8]
        if chunk in lookup:
            password += lookup[chunk]
        else:
            password += '?'  # ASSUMPTION: unrecognized chunk
    return password

def keygen(name):
    # The password is fixed (not name-based)
    # Recover from table
    pwd = recover_password_from_table()
    return pwd


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
