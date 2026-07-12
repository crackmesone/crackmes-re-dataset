#!/usr/bin/env python3
"""
Reverse-engineered keygen for lord_Phoenix's Crackme #1

Based on the BigBOi writeup. The crackme validates a 20-character
hex-string password (chars 0-9, A-F uppercase) against a username.

The core algorithm:
1. Password must be exactly 20 hex chars (0-9, A-F uppercase).
2. A 'common function' takes input, uses a table initialized with
   [0x75, 0x49, 0xBC, 0x3A, 0xDE, 0x2F, 0xDF, 0x1A] (little-endian dwords
   0x3ABC4975 and 0x1AFD2FDE stored as byte array), then iterates 16 times
   multiplying table bytes by chars of the input (plus 0x2A terminator),
   cycling through the input string. Returns 8 bytes -> 16 hex chars.
3. First call: input = username + chr(0x2A). First 8 returned bytes (as uppercase hex)
   must match password[0:8] (first 4 bytes = first 8 hex chars).
4. Second call: input = password[0:16] converted from hex string to raw bytes
   (8 bytes). The returned value's bytes 2-3 (chars 4-7 of first 4-byte hex)
   must match password[8:12].
   The remaining chars password[12:20] must match some other check.

NOTE: The writeup is truncated and many details are missing, especially for
password[12:20]. Gaps are marked with # ASSUMPTION.
"""
import struct


TABLE_INIT = [0x75, 0x49, 0xBC, 0x3A, 0xDE, 0x2F, 0xDF, 0x1A]


def common_function(input_bytes):
    """
    Implements the iterative computation described in the writeup.
    Table is 8 bytes: [0x75, 0x49, 0xBC, 0x3A, 0xDE, 0x2F, 0xDF, 0x1A]
    Input is the username bytes + 0x2A terminator (or password bytes).
    Loop runs 16 times total.
    Each iteration i (0..15):
      - Pick input char: input_bytes[i % len(input_bytes)]
        but the description says loop index into input via IDIV by len
        so: char = input_bytes[i % len(input_bytes)]
      - table_index = i % 8  (using AND 0x80000007 + sign correction = i & 7)
      - multiplier = table[table_index]
      - product = char * multiplier  (IMUL)
      - result masked to signed byte: AND 0x800000FF then sign-extend to byte
      - store back to table[table_index]
    Returns the 8-byte table as a bytes object.
    """
    # ASSUMPTION: input_bytes is the raw bytes fed to this function
    # ASSUMPTION: loop count is always 16 (0x10) regardless of input length
    table = list(TABLE_INIT)  # fresh copy each call
    input_len = len(input_bytes)
    
    # EBX starts at 1 based on the writeup (starts at 0x49 = table[1])
    # ASSUMPTION: EBX starts at 1 (since writeup says "starting at 0x49")
    ebx = 1
    
    # ESI = 16 (loop count), decremented each iter
    esi = 16
    
    for _ in range(16):
        # EDX = 0, then loop uses IDIV: EBX / len(input) -> remainder in EDX
        # char index = EBX % input_len
        char_idx = ebx % input_len
        char_val = input_bytes[char_idx]  # MOVZX: unsigned byte
        
        # table_index: EDI = EBX & 0x80000007, with sign correction
        # For positive EBX < 8, this is just EBX & 7
        edi = ebx & 0x80000007
        # Sign correction for negative: if bit 31 set, (edi-1)|0xFFFFFFF8 +1
        if edi & 0x80000000:
            edi = ((edi - 1) | 0xFFFFFFF8) + 1
            edi = edi & 0xFFFFFFFF
        table_idx = edi & 7  # effectively ebx mod 8
        
        # multiplier from table at [EBP+EDI-8] = table[table_idx]
        edx = table[table_idx]  # MOV DL, ... -> unsigned byte
        
        # IMUL: char_val (treated as signed) * edx (treated as signed)
        # Both are bytes; treat as signed
        char_signed = char_val if char_val < 128 else char_val - 256
        edx_signed = edx if edx < 128 else edx - 256
        product = char_signed * edx_signed  # IMUL EDX (EAX = EAX * EDX)
        
        # AND EAX, 0x800000FF then sign correction to get a signed byte
        eax = product & 0x800000FF
        if eax & 0x80000000:
            eax = ((eax - 1) | 0xFFFFFF00) + 1
            eax = eax & 0xFFFFFFFF
        result_byte = eax & 0xFF
        
        table[table_idx] = result_byte
        
        ebx += 1
        esi -= 1
        # loop continues while esi != 0
    
    return bytes(table)


def keygen(name):
    """
    Generate a valid 20-character hex password for the given name.
    """
    # Input to first common_function call: username bytes + 0x2A
    name_bytes = name.encode('ascii') + bytes([0x2A])
    
    result1 = common_function(name_bytes)
    # First 8 hex chars of password = first 4 bytes of result as uppercase hex
    # ASSUMPTION: all 8 bytes map to password chars 0..15 (16 hex chars)
    # But writeup says "first 8 hex bits" = first 4 bytes -> 8 hex chars
    part1_hex = result1[:4].hex().upper()  # 8 chars for password[0:8]
    
    # Second call: input = password[0:16] as raw bytes (8 bytes from hex)
    # We need to know the full 16-char first section first.
    # ASSUMPTION: result1 gives the full 8 bytes -> 16 hex chars for password[0:16]
    part1_full_hex = result1.hex().upper()  # 16 chars
    
    # Second call uses the 8 raw bytes of part1_full_hex decoded
    second_input = result1  # 8 bytes
    result2 = common_function(second_input)
    
    # password[8:12] = bytes 2-3 (chars 4-7) of the first 4 bytes of result2 as hex
    # writeup: "DE07 came from returned value, chars 4-7 of it"
    part2_hex = result2.hex().upper()[4:8]  # 4 chars for password[8:12] (bytes index 2-3)
    
    # password[12:20] - writeup is truncated, no info on last 8 chars
    # ASSUMPTION: last 8 chars come from remaining bytes of result2
    # Using bytes 4-7 of result2 as hex
    part3_hex = result2.hex().upper()[8:16]  # ASSUMPTION: last 8 chars
    
    password = part1_hex + part2_hex + part3_hex
    
    # Ensure exactly 20 chars
    if len(password) != 20:
        password = password[:20].ljust(20, '0')
    
    return password


def is_hex_string(s):
    """Check all chars are 0-9 or A-F uppercase."""
    return all(c in '0123456789ABCDEF' for c in s)


def verify(name, serial):
    """
    Verify a (name, serial) pair.
    Returns True if serial is valid for name.
    """
    # Check 1: length must be 20
    if len(serial) != 20:
        return False
    
    # Check 2: all characters must be hex (0-9, A-F uppercase)
    if not is_hex_string(serial):
        return False
    
    # Check 3: first 8 chars must match result of common_function(name + 0x2A)
    name_bytes = name.encode('ascii') + bytes([0x2A])
    result1 = common_function(name_bytes)
    expected_part1 = result1[:4].hex().upper()
    if serial[:8].upper() != expected_part1:
        return False
    
    # Check 4: second call with first 16 chars of password (as 8 raw bytes)
    # ASSUMPTION: the 16-char section is the full result1 hex
    # But we use serial[0:16] decoded as hex bytes for the second call input
    try:
        second_input = bytes.fromhex(serial[:16])
    except ValueError:
        return False
    
    result2 = common_function(second_input)
    
    # Check 5: serial[8:12] must match bytes 2-3 of result2 as hex
    expected_part2 = result2.hex().upper()[4:8]
    if serial[8:12].upper() != expected_part2:
        return False
    
    # Check 6: serial[12:20] - ASSUMPTION: matches bytes 4-7 of result2
    expected_part3 = result2.hex().upper()[8:16]
    if serial[12:20].upper() != expected_part3:
        return False
    
    return True



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
