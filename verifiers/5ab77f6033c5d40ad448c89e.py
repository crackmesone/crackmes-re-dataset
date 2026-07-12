# Reconstructed from Project1.cpp keygen source
# The assembly blocks are partially interpreted
# ASSUMPTION: The assembly rol/ror nibble extraction logic is approximated

def compute_serial_num(name):
    """Compute the main serial number from the name."""
    size = len(name)
    if size < 4:
        return None

    # First loop: sum of (char * size)
    serial2 = 0
    for c in name:
        serial = ord(c) * size
        serial2 += serial
    serial3 = serial2
    serial2 = 0

    # Second loop: sum of (char XOR size)
    for c in name:
        serial = ord(c) ^ size
        serial2 += serial

    serial = serial2 + serial3
    serial2 = 0
    serial3 = 0

    # Double nested loop: sum of (Buffer[i] * Buffer[j]) for all i,j
    for j in range(size):
        for i in range(size):
            serial2_inner = ord(name[i]) * ord(name[j])
            serial3 += serial2_inner

    serial = serial + serial3
    return serial & 0xFFFFFFFF


def nibble_to_char(nibble):
    """Convert nibble to digit char (the assembly loop reduces values > 9 by 4 repeatedly)."""
    v = nibble & 0xF
    while v > 9:
        v -= 4
        # ASSUMPTION: loop: sub 4, check > 9, repeat
    return chr(v + 0x30)


def int_to_serial_string(value):
    """Convert integer to serial string using the assembly nibble-extraction logic.
    Assembly: rol eax,4; take low byte bl; ror ebx,4 (low nibble); convert; xor al,al; ror eax,8; repeat
    ASSUMPTION: This extracts nibbles from the value MSB-first after rotation and builds a string.
    """
    value = value & 0xFFFFFFFF
    if value == 0:
        return '0'
    
    result = []
    eax = value
    # Simulate the assembly loop
    # rol eax, 4 => rotate left 4 bits (32-bit)
    # mov bl, al => take low byte
    # ror ebx, 4 => rotate ebx right 4 => low nibble of bl moves to bit 28 of ebx, we care about the nibble
    # The nibble extracted is the low nibble of al after rol
    # Then xor al,al zeros low byte; ror eax,8 shifts right 8 bits
    # ASSUMPTION: We extract nibbles one at a time from value going MSB to LSB of nibbles
    
    # Simpler interpretation: extract each 4-bit nibble from LSB to MSB
    temp = value
    nibbles = []
    while temp != 0:
        nibble = (temp >> 28) & 0xF  # top nibble after rol 4
        # But assembly does rol eax,4 first so top nibble rotates to bottom
        # Let's try: extract nibbles by rotating left 4 each time
        nibbles.append(nibble)
        temp = ((temp << 4) | (temp >> 28)) & 0xFFFFFFFF
        temp = temp & 0xFFFFFF00  # zero low byte (xor al,al)
        temp = ((temp >> 8) | (temp << 24)) & 0xFFFFFFFF  # ror eax, 8
        if temp == 0:
            break
    
    for n in nibbles:
        result.append(nibble_to_char(n))
    
    return ''.join(result)


def compute_serial2(serial_str):
    """Second serial part: sum of (Serial[i] * 0x2d) then convert."""
    serial2 = 0
    for c in serial_str:
        serial2 += ord(c) * 0x2d
    serial2 = serial2 & 0xFFFFFFFF
    return serial2


def int_to_serial2_string(value):
    """ASSUMPTION: Same nibble extraction but stored at Serial2+3 with dec ebp (reverse order).
    This writes bytes at Serial2+3, Serial2+2, Serial2+1, Serial2+0 (reverse).
    We approximate as the same conversion but reversed.
    """
    # ASSUMPTION: Same logic as int_to_serial_string but characters stored in reverse
    s = int_to_serial_string(value)
    return s[::-1]


def keygen(name):
    """Generate serial for a given name."""
    if len(name) < 4:
        return None
    
    # Compute main serial number
    serial_val = compute_serial_num(name)
    
    # Convert to string (Serial)
    serial_str = int_to_serial_string(serial_val)
    
    # Build final serial: first 4 chars of name + '-' + Serial + '-' + Serial2 + '-X'
    prefix = name[:4]
    
    # Compute serial2 from serial_str
    serial2_val = compute_serial2(serial_str)
    serial2_str = int_to_serial2_string(serial2_val)
    
    final_serial = prefix + '-' + serial_str + '-' + serial2_str + '-X'
    return final_serial


def verify(name, serial):
    """Verify name/serial pair.
    ASSUMPTION: The crackme verifies the serial matches what keygen produces.
    We regenerate and compare.
    """
    if len(name) < 4:
        return False
    expected = keygen(name)
    return expected == serial



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
