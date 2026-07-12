def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against a system_id (name).
    
    The crackme uses:
      - A constant string: "m@[tador]'sKeyGenMe#3" (22 chars)
      - A system_id (here called 'name'), must be > 16 chars (len > 16)
      - For each position i in range(0x16) = range(22):
            counter = i + 1
            expected_byte = (string[i] // counter) ^ (system_id[i] + 0x19)
        where // is integer division (IDIV in x86, signed)
      - At least 20 out of 22 chars must match (CMP var, 0x14 where 0x14=20)
        but the keygen produces all 22 correct, so we check all 22 for keygen.
    
    For verify we check that >= 20 chars match (as per the crackme logic).
    """
    CONSTANT_STRING = "m@[tador]'sKeyGenMe#3"
    system_id = name
    
    # The system_id must be longer than 16 chars
    if len(system_id) <= 16:
        return False
    
    if len(serial) < 0x16:
        return False
    
    matches = 0
    for i in range(0x16):  # 0 to 21, 22 iterations
        counter = i + 1
        string_byte = CONSTANT_STRING[i] if i < len(CONSTANT_STRING) else 0
        sys_byte = system_id[i] if i < len(system_id) else 0
        
        # IDIV: integer division (signed, truncate toward zero)
        # In Delphi/x86 IDIV: EAX = ord(string[i]), EDI = counter (1..22)
        # Since counter >= 1 and ord(string[i]) >= 0, this is just floor div
        eax = ord(string_byte) if isinstance(string_byte, str) else string_byte
        edi = counter
        # CDQ sign-extends EAX into EDX:EAX, then IDIV EDI
        # For positive eax and positive edi, result is eax // edi
        quotient = int(eax / edi)  # truncate toward zero
        
        edx = ord(sys_byte) if isinstance(sys_byte, str) else sys_byte
        edx = (edx + 0x19) & 0xFF
        
        expected = (quotient ^ edx) & 0xFF
        
        serial_byte = ord(serial[i]) if i < len(serial) else -1
        if serial_byte == expected:
            matches += 1
    
    # The crackme checks: if matches >= 20 (0x14), it's valid
    return matches >= 20


def keygen(name: str) -> str:
    """
    Generate a valid serial for a given system_id (name).
    
    Requirements:
      - name (system_id) must be longer than 16 characters
      - For each position i in 0..21:
            counter = i + 1
            serial[i] = (ord(constant_string[i]) // counter) XOR (ord(system_id[i]) + 0x19)
    """
    CONSTANT_STRING = "m@[tador]'sKeyGenMe#3"
    system_id = name
    
    if len(system_id) <= 16:
        raise ValueError(f"System ID must be longer than 16 characters, got {len(system_id)}")
    
    serial_bytes = []
    for i in range(0x16):  # 22 iterations
        counter = i + 1
        eax = ord(CONSTANT_STRING[i])
        # IDIV: signed integer division, truncate toward zero
        quotient = int(eax / counter)
        
        sys_byte = ord(system_id[i]) if i < len(system_id) else 0
        edx = (sys_byte + 0x19) & 0xFF
        
        result = (quotient ^ edx) & 0xFF
        serial_bytes.append(result)
    
    # Build serial string; some bytes may not be printable ASCII
    serial = bytes(serial_bytes).decode('latin-1')
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
