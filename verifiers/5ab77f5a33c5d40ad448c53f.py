# Keygen for ReWrit's Crackme #13
# Based on the keygen assembly source provided in the solution writeup
# by 'Holy' (crackmes.de)

def _signed_byte(v):
    v = v & 0xFF
    if v >= 0x80:
        return v - 0x256
    return v

def _sar_byte(v, n):
    """Arithmetic shift right on a signed byte"""
    sb = _signed_byte(v)
    return sb >> n

def get_serial(name):
    """
    Implements GetSerial from Module2.asm.
    Works on mutable copy of name bytes stored in NameBuffer.
    ResultBuffer holds the output serial bytes.
    """
    ENCRYPTION_TABLE = [
        ord('S'), ord('g'), ord('h'), ord('r'), ord('h'),
        ord('r'), ord('s'), ord('g'), ord('d'), ord('h'),
        ord('l'), ord('o'), ord('n'), ord('q'), ord('s'),
        0x60,
        ord('m'), ord('s'), ord('j'), ord('d'), ord('x'),
    ]

    name_buf = list(name.encode('latin-1')) if isinstance(name, str) else list(name)
    name_len = len(name_buf)
    result_buf = [0] * name_len

    for counter in range(name_len):
        # --- Transform NameBuffer[counter] ---
        dl = name_buf[counter] & 0xFF
        # SAR DL, 7 then SHR DL, 7 on AL=DL
        al = dl
        # SAR al, 7: arithmetic shift right by 7 => gives 0xFF if high bit set, else 0x00
        al_sar = _sar_byte(al, 7) & 0xFF
        # SHR al, 7: logical shift right by 7 of previous result
        al_shr = (al_sar & 0xFF) >> 7
        # ADD al, dl
        al_add = (al_shr + dl) & 0xFF
        dl2 = al_add
        # SAR dl, 1
        dl2_sar = _sar_byte(dl2, 1) & 0xFF

        # enc_table[counter] - dl2_sar + 1 XOR name_buf[counter]
        enc_val = ENCRYPTION_TABLE[counter] if counter < len(ENCRYPTION_TABLE) else 0
        al_enc = (enc_val - dl2_sar + 1) & 0xFF
        al_xor = (al_enc ^ name_buf[counter]) & 0xFF
        name_buf[counter] = al_xor  # mutate NameBuffer

        # --- Check if counter is even (par) ---
        if (counter & 1) == 0:
            result_buf[counter] = (name_buf[counter] + 1) & 0xFF

        # --- Check counter % 3 == 0 ---
        # The assembly computes counter mod 3 using the magic multiplier 0x55555556
        # ASSUMPTION: The code checks if counter % 3 == 0
        counter2 = counter
        # 64-bit signed multiply: 0x55555556 * counter2
        prod = 0x55555556 * counter2
        # Take high 32 bits (EDX)
        edx = (prod >> 32) & 0xFFFFFFFF
        # Sign-extend EDX as 32-bit signed
        if edx >= 0x80000000:
            edx_s = edx - 0x100000000
        else:
            edx_s = edx
        # EAX = SAR counter2, 31
        eax_sar = (counter2 >> 31) if counter2 >= 0 else -1  # ASSUMPTION: counter2 always >= 0 here
        ecx_val = edx_s - eax_sar
        eax_val = ecx_val
        # eax = ecx*2 + ecx = ecx*3
        eax_3 = eax_val * 3
        edx_mod = counter2 - eax_3
        if edx_mod == 0:
            result_buf[counter] = (name_buf[counter] + 2) & 0xFF

        # --- Check previous+current letter parity ---
        if counter == 0:
            continue  # skip the prev-letter check

        prev = _signed_byte(name_buf[counter - 1])
        curr = _signed_byte(name_buf[counter])
        sum_pc = (prev + curr) & 0xFFFFFFFF
        if (sum_pc & 1) == 0:
            # Even: result_buf[counter] += 2
            result_buf[counter] = (result_buf[counter] + 2) & 0xFF
        else:
            # Odd (Impar2): check next letter
            if counter + 1 < name_len:
                next_letter = _signed_byte(name_buf[counter + 1])
                sum_nc = (next_letter + curr) & 0xFFFFFFFF
                # counter2 = sum_nc; check if sum_nc % 3 == 0
                counter2b = sum_nc
                prod2 = 0x55555556 * counter2b
                edx2 = (prod2 >> 32) & 0xFFFFFFFF
                if edx2 >= 0x80000000:
                    edx2_s = edx2 - 0x100000000
                else:
                    edx2_s = edx2
                eax2_sar = (counter2b >> 31) if counter2b >= 0 else -1
                ecx2 = edx2_s - eax2_sar
                eax2_3 = ecx2 * 3
                edx2_mod = counter2b - eax2_3
                if edx2_mod == 0:
                    result_buf[counter] = (result_buf[counter] + 4) & 0xFF
            # else: skip, no next letter

    # --- DeleteThe02: normalize result bytes to printable range ---
    result_buf = delete_the_02(name_buf, result_buf)
    return result_buf


def delete_the_02(name_buf, result_buf):
    """
    Implements DeleteThe02 from Module2.asm.
    Ensures all bytes in result_buf are in a printable range.
    If result_buf[i] > 0x79 ('y'), reduce it.
    If result_buf[i] <= 0x41 ('A'), increase it.
    """
    name_len = len(name_buf)
    result = list(result_buf)
    counter60 = 0  # counts how many times we've incremented above 0x79

    for counter in range(name_len):
        # Loop to bring byte <= 0x79
        while result[counter] > 0x79:
            counter60 += 1
            counter2_val = counter60
            counter63_val = counter + 1
            # ASSUMPTION: counter2_val = counter2_val // counter63_val (integer division)
            div_val = counter2_val // counter63_val
            # Sub Al, Byte Ptr Ds:[Counter2]  => counter2 is a DWORD variable, not an array
            # ASSUMPTION: the assembly subtracts the byte value of div_val from result[counter]
            result[counter] = (result[counter] - (div_val & 0xFF)) & 0xFF
            if result[counter] > 0x79:
                continue
            break

        # Loop to bring byte > 0x41
        while result[counter] <= 0x41:
            # counter2 = counter + 0x0F
            counter2_val = counter + 0x0F
            # Compute counter2_val // 3 (the magic multiply by 0x55555556)
            prod = 0x55555556 * counter2_val
            edx_val = (prod >> 32) & 0xFFFFFFFF
            if edx_val >= 0x80000000:
                edx_s = edx_val - 0x100000000
            else:
                edx_s = edx_val
            eax_sar2 = (counter2_val >> 31) if counter2_val >= 0 else -1
            ecx_div = edx_s - eax_sar2
            # result[counter] = ecx_div + result[counter] + 0x0A
            result[counter] = (result[counter] + ecx_div + 0x0A) & 0xFF

    return result


def keygen(name):
    """
    Generate serial for given name.
    Returns serial as a string.
    """
    result_bytes = get_serial(name)
    # Convert to string, stop at null byte
    serial = ''
    for b in result_bytes:
        if b == 0:
            break
        serial += chr(b)
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: The crackme checks serial == keygen(name) byte-for-byte.
    """
    expected = keygen(name)
    return serial == expected



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
