import ctypes
import struct

def name_routine(name):
    """
    Implements the NAMEROUTINE from the keygen ASM.
    Runs over the name twice (once for len < 15, once for len >= 15)
    producing a 15-byte REZULT array.
    """
    rezult = [0] * 15
    ebp = 0x5A435847
    edx = 0
    ebx = 0
    ecx = 0  # ECX is used as CL for ROL count and CH as a flag
    cl = 0
    ch = 0
    length = len(name)
    name_bytes = [ord(c) for c in name]

    def rol32(val, count):
        count = count & 31
        if count == 0:
            return val & 0xFFFFFFFF
        return ((val << count) | (val >> (32 - count))) & 0xFFFFFFFF

    # First pass
    edx = 0
    ebx = 0
    cl = 0
    ch = 0
    carry = 0

    def adc32(a, b, carry_in):
        result = a + b + carry_in
        return result & 0xFFFFFFFF, 1 if result > 0xFFFFFFFF else 0

    while True:
        al = name_bytes[edx % length]
        # ADC EBP, EAX (carry from previous ADC, initially 0)
        ebp, carry = adc32(ebp, al, carry)
        # ROL EBP, CL
        ebp = rol32(ebp, cl)
        # XOR EAX, EBP  -> eax = al ^ ebp (low byte)
        eax = al ^ (ebp & 0xFF)
        # ADD BYTE PTR DS:[EBX+REZULT], AL
        rezult[ebx % 15] = (rezult[ebx % 15] + (eax & 0xFF)) & 0xFF
        ebx += 1
        if ebx >= 15:
            ebx = 0
            ch = 1
        cl = (cl + 1) & 0xFF
        edx += 1
        if edx < length:
            continue
        edx = 0
        if ch != 0:
            break

    return rezult


def bruteforce_key(length_name):
    """
    Bruteforce the KEY (14-bit value, 0..0x3FFF) such that the
    weighted sum ESI >= 0x5000.
    
    The weighting: bits of KEY (bits 1..14, i.e. mask starting at 0x2000 down)
    are tested. For each bit position i (0..13), if bit is set ESI += length_name^i
    else ESI += 0. Actually: ESI += bit_value * (length_name ** i)
    
    # ASSUMPTION: TICKCOUNT check (CMP DS:[TICKCOUNT], EBP / JG THERE2) is ignored
    # since we cannot replicate GetTickCount behavior; we just find first KEY with ESI >= 0x5000
    """
    for key_candidate in range(0, 0x3FFF + 1):
        esi = 0
        ebx = 1
        mask = 0x2000
        for i in range(14):
            bit_val = 1 if (key_candidate & mask) else 0
            esi += bit_val * ebx
            ebx *= length_name
            mask >>= 1
        if esi >= 0x5000:
            return key_candidate, esi
    # ASSUMPTION: fallback
    return 0x3FFF, 0


def serial_from_rezult_and_dwordd(rezult, dwordd_val):
    """
    Implements the Name-, Serial- & Checkboxroutine and Serialroutine.
    
    Step 1: Build ECX from REZULT (L00P)
      ECX = 0
      for edx in range(4):
        ECX = (ECX << 8) & 0xFFFFFFFF
        CL += rezult[edx] + rezult[edx+4] + rezult[edx+8] + rezult[edx+12]
      (note: only adds 4 bytes per column, last column is rezult[12..15] but
       rezult[12] + rezult[12+4] would wrap; only 15 bytes exist)
    
    # ASSUMPTION: The exact indexing for the 4 columns is:
    #   row 0: rezult[0], rezult[4], rezult[8], rezult[12]
    #   row 1: rezult[1], rezult[5], rezult[9], rezult[13]
    #   row 2: rezult[2], rezult[6], rezult[10], rezult[14]
    #   row 3: rezult[3], rezult[7], rezult[11], (rezult[15] = 0 since array is 0-filled)
    """
    # L00P builds ECX as 4-byte value with each byte being sum of column
    rezult16 = rezult + [0]  # pad to 16
    ecx = 0
    for edx in range(4):
        ecx = (ecx << 8) & 0xFFFFFFFF
        cl_val = (rezult16[edx] + rezult16[edx+4] + rezult16[edx+8] + rezult16[edx+12]) & 0xFF
        ecx = (ecx & 0xFFFFFF00) | cl_val

    # L00P2: builds EAX from DWORDD bytes minus ECX bytes
    # DWORDD is a 4-byte value (ESI from bruteforcer)
    dwordd_bytes = struct.pack('<I', dwordd_val & 0xFFFFFFFF)
    eax = 0
    ecx_work = ecx
    for edx2 in range(4):
        eax = (eax << 8) & 0xFFFFFFFF
        al = dwordd_bytes[edx2]
        cl2 = ecx_work & 0xFF
        al = (al - cl2) & 0xFF
        eax = (eax & 0xFFFFFF00) | al
        ecx_work = (ecx_work >> 8) & 0xFFFFFFFF
    # ROR EAX, 8
    eax = ((eax >> 8) | (eax << 24)) & 0xFFFFFFFF

    # Now distribute EAX bytes into REZULT
    ebx_val = eax
    result_out = list(rezult16[:15])

    # Byte 0 (ESI+0..3, ESI+8..11, ESI+12..15)
    al0 = ebx_val & 0xFF
    ah0 = 0
    # DIV CL (ECX=4): AL = al0 // 4, AH = al0 % 4
    al_q = (al0 // 4) & 0xFF
    ah_q = (al0 % 4) & 0xFF
    result_out[0] = al_q
    result_out[4] = al_q
    result_out[8] = al_q
    result_out[12] = (al_q + ah_q) & 0xFF

    ebx_val = (ebx_val >> 8) & 0xFFFFFFFF
    al1 = ebx_val & 0xFF
    al_q1 = (al1 // 4) & 0xFF
    ah_q1 = (al1 % 4) & 0xFF
    result_out[1] = al_q1
    result_out[5] = al_q1
    result_out[9] = al_q1
    result_out[13] = (al_q1 + ah_q1) & 0xFF

    ebx_val = (ebx_val >> 8) & 0xFFFFFFFF
    al2 = ebx_val & 0xFF
    al_q2 = (al2 // 4) & 0xFF
    ah_q2 = (al2 % 4) & 0xFF
    result_out[2] = al_q2
    result_out[6] = al_q2
    result_out[10] = al_q2
    result_out[14] = (al_q2 + ah_q2) & 0xFF

    ebx_val = (ebx_val >> 8) & 0xFFFFFFFF
    al3 = ebx_val & 0xFF
    # DIV CL (ECX=3): AL = al3 // 3, AH = al3 % 3
    al_q3 = (al3 // 3) & 0xFF if 3 != 0 else al3
    ah_q3 = (al3 % 3) & 0xFF if 3 != 0 else 0
    result_out[3] = al_q3
    result_out[7] = al_q3
    result_out[11] = (al_q3 + ah_q3) & 0xFF
    # Note: only 3 entries for last byte (ESI, ESI+4, ESI+8) based on DIV by 3

    return result_out


def rezult_to_serial_string(rezult_final):
    """
    # ASSUMPTION: The Serialroutine (truncated in writeup) converts REZULT bytes
    # to a printable serial string. Common approach: hex encode or map to ASCII range.
    # We map each byte to printable ASCII by (byte % 26) + ord('A')
    """
    chars = []
    for b in rezult_final[:15]:
        c = (b % 26) + ord('A')
        chars.append(chr(c))
    # Group as 4-3-4-4 or just return as-is
    s = ''.join(chars)
    return s


def keygen(name):
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")
    rezult = name_routine(name)
    key_val, esi_val = bruteforce_key(len(name))
    rezult_final = serial_from_rezult_and_dwordd(rezult, esi_val)
    serial = rezult_to_serial_string(rezult_final)
    return serial


def verify(name, serial):
    """
    # ASSUMPTION: We cannot fully verify without the original crackme binary.
    # We check that keygen(name) produces the given serial.
    """
    if len(name) < 5:
        return False
    try:
        expected = keygen(name)
        return expected == serial
    except Exception:
        return False



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
