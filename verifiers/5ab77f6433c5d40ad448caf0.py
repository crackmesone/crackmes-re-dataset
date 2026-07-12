#!/usr/bin/env python3
"""
Reverse-engineered keygen for Grinder 1.0 by x_treem.
Based on the keygen source code (KeyGen.asm) from solution by red477.

The serial format is:
  <hex1><hex2><hex3>
where:
  - hex1 and hex2 are two random 32-bit values (GetTickCount squared),
    formatted as "%lX%lX" (combined = 16 hex digits, may be shorter if leading zeros dropped)
  - hex3 is a 3-digit hex suffix derived from the name checksum

The name checksum algorithm:
  For each character in the name:
    - if 'a'-'z': val = (ord(c) - 0x61) >> 1
    - if '0'-'9': val = ord(c) - 0x1E
    - if 'A'-'Z': val = (ord(c) - 0x41) >> 1
    - else:       val = 8
  Then: lSum = (lSum << 1) + szSerial[val]  ... where szSerial[val] is
  the character at position `val` in the already-computed hex serial string.

  After the loop:
    lSum &= 0xFFF
    eax = lSum
    bl = al; al = ah; ah = bl   <- swap low bytes
    bl &= 0xF0; al |= bl
    eax &= 0xFFF
  Format eax as "%03X" and append as last 3 chars of serial
  (serial is truncated to 13 chars before appending, making total 16).

Constraints: name length must be 7..16 characters (cmp eax,6 jb bad; cmp eax,10h jg bad).

NOTE: Because the checksum uses characters from the hex serial string (which is
random), two different calls to keygen() may produce different valid serials.
verify() below reconstructs the check: given a serial, it recomputes what the
suffix should be and compares.
"""

import random


def _compute_suffix(name: str, serial_prefix: str) -> str:
    """
    Given the name and the first part of the serial (at least 9 chars for indexing),
    compute the 3-hex-digit suffix.
    """
    # Work on a mutable copy (the asm modifies chars in-place in szName buffer)
    name_bytes = list(name.encode('ascii', errors='replace'))
    
    # The serial buffer is used as a lookup table; szSerial is the full serial string.
    # We use serial_prefix (the hex string before the suffix) as the lookup table.
    # Pad if needed (the asm allocated 17 bytes, indices come from transformed char values)
    lSum = 0
    serial_bytes = list(serial_prefix.encode('ascii'))
    
    for i in range(len(name_bytes)):
        c = name_bytes[i]
        if 0x61 <= c <= 0x7A:  # 'a'-'z'
            val = (c - 0x61) >> 1  # 0..12
        elif 0x30 <= c <= 0x39:  # '0'-'9'
            val = c - 0x1E         # 0x30-0x1E=0x12=18 .. 0x39-0x1E=0x1B=27
        elif 0x41 <= c <= 0x5A:  # 'A'-'Z'
            val = (c - 0x41) >> 1  # 0..12
        else:
            val = 8
        
        # szSerial[val] - look up character in the serial string at position val
        if val < len(serial_bytes):
            lookup_char = serial_bytes[val]
        else:
            lookup_char = 0
        
        lSum = (lSum << 1) + lookup_char
        lSum &= 0xFFFFFFFF  # keep 32-bit
    
    lSum &= 0xFFF
    eax = lSum
    
    # swap low bytes:
    # bl = al; al = ah; ah = bl
    al = eax & 0xFF
    ah = (eax >> 8) & 0xFF
    bl = al
    al = ah
    ah = bl
    # bl &= 0xF0; al |= bl
    bl &= 0xF0
    al |= bl
    # reconstruct eax from ah:al
    eax = (ah << 8) | al
    eax &= 0xFFF
    
    return '%03X' % eax


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be 7-16 characters.
    """
    if len(name) < 7 or len(name) > 16:
        raise ValueError("Name must be 7-16 characters")
    
    # ASSUMPTION: The two random values come from GetTickCount()^2 each call.
    # We simulate with random 32-bit values (since we can't reproduce exact timing).
    # In the original keygen, two calls to GetTickCount are made, each squared.
    r1 = random.getrandbits(32)
    r2 = random.getrandbits(32)
    
    # Format as "%lX%lX" - uppercase hex without leading zeros
    hex_prefix = '%X%X' % (r1, r2)
    
    # Truncate to 13 chars for the prefix (serial is 17 bytes total: 13 + 3 suffix + null)
    # ASSUMPTION: The asm does: mov byte ptr[szSerial+13],0 then lstrcat
    # So the prefix part used for lookup is the full hex_prefix, but truncated to 13 for output.
    prefix_for_lookup = hex_prefix  # full string used for character lookup
    prefix_truncated = hex_prefix[:13]  # truncated for output
    
    suffix = _compute_suffix(name, prefix_for_lookup)
    
    return prefix_truncated + suffix


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Serial should be 16 characters: 13 hex prefix + 3 hex suffix.
    """
    if len(name) < 7 or len(name) > 16:
        return False
    if len(serial) < 4:
        return False
    
    # Split: first 13 chars are the prefix, last 3 are the suffix
    prefix = serial[:13]
    suffix = serial[13:16].upper()
    
    if len(suffix) != 3:
        return False
    
    # The full serial string (prefix) is used for the lookup table
    expected_suffix = _compute_suffix(name, prefix)
    
    return suffix == expected_suffix.upper()



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
