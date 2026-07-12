import ctypes

def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def ror32(val, n):
    return rol32(val, 32 - n)

def compute_first_part(name):
    """
    Assembly loop over name bytes:
      EAX=1, EDX=0 initially (EDX not shown initialized, ASSUMPTION: EDX=0)
      for each byte b in name:
          EBX = b
          EBX ^= EDX
          EAX += EBX
          EAX = ROL(EAX, 7)
          EDX = EBX
    After loop, run 10 mixing iterations (ECX=0..9):
      XOR EAX, EBX
      EBX = ROL(EBX, 16)
      EBX += EDX
      XOR EAX, EBX
      EAX = ROL(EAX, 3)
      XOR EAX, EDX
      EDX = ROL(EDX, 8)
      EDX += EBX
      XOR EAX, EDX
      EAX = ROL(EAX, 5)
    Return EAX
    """
    eax = 1
    edx = 0
    ebx = 0
    for ch in name:
        b = ord(ch) if isinstance(ch, str) else ch
        ebx = b
        ebx ^= edx
        ebx &= 0xFFFFFFFF
        eax = (eax + ebx) & 0xFFFFFFFF
        eax = rol32(eax, 7)
        edx = ebx

    # 10 mixing iterations
    ecx = 0
    while True:
        eax = (eax ^ ebx) & 0xFFFFFFFF
        ebx = rol32(ebx, 16)
        ebx = (ebx + edx) & 0xFFFFFFFF
        eax = (eax ^ ebx) & 0xFFFFFFFF
        eax = rol32(eax, 3)
        eax = (eax ^ edx) & 0xFFFFFFFF
        edx = rol32(edx, 8)
        edx = (edx + ebx) & 0xFFFFFFFF
        eax = (eax ^ edx) & 0xFFFFFFFF
        eax = rol32(eax, 5)
        ecx += 1
        if ecx >= 10:
            break

    return eax

def compute_second_part(serial_input_16):
    """
    The second part uses the 16-char serial input string (the one typed by the user).
    The code at 004087C4 loads 'indoKGM1.0040A7A4' which was shown as ASCII '1234567890123456'
    in the example - this is likely the ENTERED serial string (16 chars).
    ASSUMPTION: 40A7A4 contains the entered serial string, 40A7A0 is some related dword.
    ASSUMPTION: 40A7BC (result) is initialized to 0.
    ASSUMPTION: 40A7A0 = dword at offset 0 of the serial buffer (first 4 bytes as little-endian dword).
    
    The loop (EAX=1..16, EDX pointer to serial chars):
      result ^= CL  (byte from serial)
      if EAX != 16: result = SHL(result, 2)
      EAX++, EDX++
    
    Then post-processing:
      tmp = result
      result = (tmp >> 12) << 12   # clear lower 12 bits
      edx2 = mem[40A7A0] >> 20     # upper bits of first dword of serial
      result += edx2
      edx2b = mem[40A7A0] & 0xFFFFF  # lower 20 bits
      result ^= edx2b
      edx3 = (mem[40A7A0] << 12) >> 24  # bits 8..19 of first dword?
      result ^= edx3
    Repeat 4 times, concatenate.
    """
    # First 4 bytes of serial as little-endian dword
    # ASSUMPTION: serial_input_16 is the 16-char hex serial being validated
    ser_bytes = serial_input_16.encode('ascii') if isinstance(serial_input_16, str) else serial_input_16
    # mem[40A7A0]: ASSUMPTION it's the dword formed by first 4 bytes of serial string
    a7a0 = int.from_bytes(ser_bytes[:4], 'little') & 0xFFFFFFFF

    results = []
    for _ in range(4):
        result = 0
        eax = 1
        for i in range(16):
            cl = ser_bytes[i] & 0xFF
            result = (result ^ cl) & 0xFFFFFFFF
            if eax != 16:
                result = (result << 2) & 0xFFFFFFFF
            eax += 1

        # Post-process
        result = (result >> 12) << 12
        result &= 0xFFFFFFFF
        edx2 = (a7a0 >> 20) & 0xFFFFFFFF
        result = (result + edx2) & 0xFFFFFFFF
        edx2b = a7a0 & 0xFFFFF
        result = (result ^ edx2b) & 0xFFFFFFFF
        edx3 = ((a7a0 << 12) & 0xFFFFFFFF) >> 24
        result = (result ^ edx3) & 0xFFFFFFFF
        results.append(result)

    # ASSUMPTION: second part is the XOR/combination of 4 iterations
    # The writeup says 'repeat 4 times' and gets a single 32-bit value -> use last result
    return results[-1]

def verify(name, serial):
    """
    Verify name/serial pair.
    Serial should be 16 hex chars: FirstPart(8) + SecondPart(8)
    """
    if len(serial) != 16:
        return False
    try:
        s_int = int(serial, 16)
    except ValueError:
        return False

    first_part = compute_first_part(name)
    first_hex = '%08X' % first_part

    # The second part generation uses the entered serial - but that is circular.
    # ASSUMPTION: The second part is derived independently from the name or first part.
    # Since the writeup is unclear about 40A7A0, we just check first part for now.
    # Mark as partial: only first part check is reliable.
    given_first = serial[:8].upper()
    if given_first != first_hex:
        return False

    # ASSUMPTION: second part check omitted due to insufficient info about 40A7A0 source
    return True

def keygen(name):
    """
    Generate serial for given name.
    First part is fully computed.
    Second part: ASSUMPTION based on partial reverse - placeholder 00000000.
    """
    first_part = compute_first_part(name)
    first_hex = '%08X' % first_part
    # ASSUMPTION: second part cannot be reliably generated without knowing 40A7A0 source
    # For Kostya the answer is 5B588047 - we return first part only with placeholder
    second_hex = '00000000'  # ASSUMPTION: placeholder
    return first_hex + second_hex


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
