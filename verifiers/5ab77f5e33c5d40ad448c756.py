import ctypes

def _compute_char(name, i, magic_str):
    """
    Compute one serial character from the name character at position:
    - index into name is: name[i % len(magic_str)] where magic_str = 'aicgetocnpqbwm'
    Actually from the disassembly: lpName[i % len_magic_str]
    """
    # ASSUMPTION: magic_str is appended to or used alongside the name.
    # From the write-up: 'calculates a single character from the name entered + "aicgetocnpqbwm"'
    # The name string used is: name + 'aicgetocnpqbwm', indexed by i % len(name+magic)
    magic_str = 'aicgetocnpqbwm'
    full_str = name + magic_str
    # ASSUMPTION: modulus divisor is len(full_str) based on idiv in disassembly
    divisor = len(full_str)
    if divisor == 0:
        return None
    idx = i % divisor
    # Get character
    c = ord(full_str[idx])

    # Step 1: if NOT ('?' < chr <= 'Z'), i.e. chr <= '?' or chr > 'Z', apply transform
    if not (c > 0x3F and c <= 0x5A):
        # Assembly arithmetic to map c into range
        # movzx ecx, chr
        # movsx ax, cl
        # imul eax, eax, 0x67
        # movzx eax, ax  (take low 16 bits)
        # shr eax, 8
        # dl = al
        # sar dl, 3
        # al = cl
        # sar al, 7
        # sub dl, al
        # al = dl
        # shl al, 2
        # add al, dl
        # shl al, 2
        # sub cl, al
        # al = cl
        # add al, 0x62
        ecx = c & 0xFF
        cl = ecx
        ax = ctypes.c_int16(c).value
        eax = (ax * 0x67) & 0xFFFF  # imul then movzx ax (16-bit)
        eax = (eax >> 8) & 0xFF
        dl = eax & 0xFF
        # sar dl, 3 (arithmetic shift right)
        dl = ctypes.c_int8(dl).value >> 3
        al = ctypes.c_int8(cl).value >> 7
        dl = (dl - al) & 0xFF
        al = dl
        al = (al << 2) & 0xFF
        al = (al + dl) & 0xFF
        al = (al << 2) & 0xFF
        cl = (cl - al) & 0xFF
        al = cl
        al = (al + 0x62) & 0xFF
        c = al

    # Step 2: XOR with 0x21
    c = c ^ 0x21

    # Step 3: if signed(c) < 0, add 3
    c_signed = ctypes.c_int8(c & 0xFF).value
    if c_signed < 0:
        c = (c + 3) & 0xFF

    # Step 4: compute bFlag
    # sar eax, 2 where eax = c (signed extend)
    c_val = ctypes.c_int32(ctypes.c_int8(c & 0xFF).value).value
    tmp = c_val >> 2  # arithmetic right shift
    ecx = tmp + i

    # Compute ecx mod 6 using the 0x2AAAAAAB trick (division by 6)
    # The magic number 0x2AAAAAAB with imul gives floor division by 6
    # edx:eax = ecx * 0x2AAAAAAB
    product = ctypes.c_int32(ecx).value * 0x2AAAAAAB
    edx = (product >> 32) & 0xFFFFFFFF
    edx_signed = ctypes.c_int32(edx).value
    eax2 = ctypes.c_int32(ecx).value
    sar_result = eax2 >> 31  # sign of ecx
    quotient = edx_signed - sar_result
    # remainder = ecx - quotient * 6
    remainder = ctypes.c_int32(ecx).value - quotient * 6
    bFlag = remainder

    # Step 5: if bFlag <= 2, tolower
    final_c = c & 0xFF
    if bFlag <= 2:
        final_c = ord(chr(final_c).lower()) if 0 < final_c < 128 else final_c

    return final_c


def keygen(name):
    """
    Generate serial for a given name.
    Serial is 19 chars: 4 groups of 4 chars separated by '-'
    Format: XXXX-XXXX-XXXX-XXXX (positions 4,9,14 are '-')
    But length 19 with '-' at positions 4,9,14 => indices 4,9,14
    Actually: groups at i=0..3, dash, i=4..7, dash, i=8..11, dash, i=12..15
    The loop runs i from 0 to 15 (16 chars), dashes inserted at multiples of 4
    """
    serial_chars = []
    j = 0  # serial index
    for i in range(16):
        # Insert dash at positions that are multiples of 4 (but not 0)
        if i > 0 and i % 4 == 0:
            serial_chars.append('-')
        c = _compute_char(name, i, '')
        if c is None:
            return None
        serial_chars.append(chr(c))
    return ''.join(serial_chars)


def verify(name, serial):
    """
    Verify name/serial pair.
    """
    if len(serial) != 19:
        return False
    # Check dashes at positions 4, 9, 14
    if serial[4] != '-' or serial[9] != '-' or serial[14] != '-':
        return False
    # Remove dashes and compare 16 generated chars
    serial_no_dash = serial.replace('-', '')
    if len(serial_no_dash) != 16:
        return False
    generated = keygen(name)
    if generated is None:
        return False
    return serial == generated



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
