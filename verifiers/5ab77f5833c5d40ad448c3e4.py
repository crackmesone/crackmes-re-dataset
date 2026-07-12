import sys

def verify(name: str, serial: str) -> bool:
    # Step 1: compute v3 = sum of ASCII values of name characters (including newline in original)
    # The original reads chars and sums them; we simulate with the name string + newline
    v3 = 0
    for ch in name:
        v3 += ord(ch)
    v3 += ord('\n')  # original loop includes the newline character

    # Step 2: parse serial as integer (the original accumulates digit by digit)
    # serial must be all digits, and result < 0xFFFF
    if not serial.isdigit():
        return False
    v4 = 0
    for ch in serial:
        v4 = v4 + ord(ch) - 48
        v4 *= 10
    if v4 >= 0xFFFF:
        return False
    v5 = v4  # saved but not used further in the check

    # Step 3: compute the global-like constants
    # dword_4077F8 = 3*51+102 = 255
    # dword_4077F0 = 255
    # dword_4077F8 = 255*255+127 = 65152  -> this is dword_4077F4 = 65152
    # dword_4077F8 = 65152+384 = 65536
    # dword_4077F0 = 255+1=256; 256<<7 = 32768
    # dword_4077F4 = 65152+375+10 = 65537
    dword_4077F8_val = 3
    dword_4077F8_val *= 51
    dword_4077F8_val += 102  # = 255
    dword_4077F0_val = dword_4077F8_val  # = 255
    dword_4077F8_val = 255 * dword_4077F0_val
    dword_4077F8_val += 127  # = 65152
    dword_4077F4_val = dword_4077F8_val  # = 65152
    dword_4077F8_val = dword_4077F4_val + 384  # = 65536
    dword_4077F0_val += 1  # 256
    dword_4077F0_val <<= 7  # 32768
    dword_4077F4_val += 375
    dword_4077F4_val += 10  # 65537
    # dword_4077F8_val = 65536

    # Step 4: compute v7 = v4 // 10 (count of 10s subtracted)
    v7 = 0
    v8 = v4
    while v8 >= 10:
        v8 -= 10
        v7 += 1
    v4 = v7  # now v4 = original_serial_int // 10

    # Step 5: big bitwise loop
    # v9 computed from v4 and constant 0x3B1=945
    # loop: v10 = 1, 2, 4, ... while v10 < dword_4077F8_val (65536)
    v9 = 0
    v10 = 1
    while v10 < dword_4077F8_val:
        cond_a = (v10 & v4) == v10
        cond_b = (v10 & 0x3B1) == v10
        if cond_a and cond_b:
            v9 |= 2 * v10
        else:
            if (not cond_a and not cond_b) or ((v10 & v9) == v10):
                if cond_a or cond_b:
                    v9 |= v10
            else:
                v9 ^= (v10 | 2 * v10)
        v10 *= 2

    v4 = v9

    # Step 6: determine v11, v12, v13 based on v9 vs 0x36F=879
    if v9 >= 0x36F:
        v11 = 879
        v12 = v4
        v13 = 0
    else:
        v11 = v4
        v12 = 879
        v13 = 1

    # Step 7: second bitwise loop
    v14 = v12
    v15 = 1
    while v15 < dword_4077F8_val:
        cond_c = (v15 & v11) == v15
        cond_d = (v15 & v14) == v15
        if not cond_c or cond_d:
            if cond_c and cond_d:
                v14 ^= v15
        else:
            # (v15 & v11)==v15 and (v15 & v14)!=v15
            v16 = 0
            v17 = v15
            while v17 < dword_4077F8_val:
                v16 |= v17
                if v14 & v17:
                    v14 ^= v16
                    break
                v17 *= 2
        v15 *= 2

    if v13:
        v14 = -v14
    v4 = v14

    # Step 8: recompute globals (same formula as before gives same values)
    # dword_4077F8_val -= 32768 => 65536-32768=32768
    dword_4077F8_val -= 32768  # 32768
    dword_4077F0_val = dword_4077F8_val  # 32768
    dword_4077F4_val = dword_4077F8_val  # 32768
    dword_4077F4_val += 32768  # 65536
    dword_4077F4_val += 1      # 65537
    dword_4077F8_val = dword_4077F4_val - 1  # 65536

    # Step 9: loop with bit 4 check
    v18 = 0
    v19 = 1
    v20 = 0
    while v19 < dword_4077F8_val:
        if v19 & 4:
            v21 = v4 << v20
            v22 = 0
            v23 = 1
            while v23 < dword_4077F8_val:
                ca = (v23 & v18) == v23
                cb = (v23 & v21) == v23
                if ca and cb:
                    v22 |= 2 * v23
                else:
                    if (not ca and not cb) or ((v23 & v22) == v23):
                        if ca or cb:
                            v22 |= v23
                    else:
                        v22 ^= (v23 | 2 * v23)
                v23 *= 2
            v18 = v22
        v19 *= 2
        v20 += 1

    v24 = v18 & 0xFFFFFFFF
    v25 = 0
    while v25 < 2:
        if v24 & 1:
            v24 >>= 1
            v24 |= dword_4077F0_val
        else:
            v24 >>= 1
        v25 += 1
    v4 = v24

    # Step 10: recompute globals again
    dword_4077F8_val *= 4
    dword_4077F8_val = (dword_4077F8_val & 0xFFFFFFFF) >> 2
    dword_4077F8_val -= 32768  # back to 32768? 65536*4>>2=65536; 65536-32768=32768
    dword_4077F0_val = dword_4077F8_val
    dword_4077F4_val = dword_4077F8_val
    dword_4077F4_val += 32768
    dword_4077F4_val += 1
    dword_4077F8_val = dword_4077F4_val - 1  # 65536 again

    # Step 11: loop with 0x2A mask
    v26 = 0
    v27 = 1
    v28 = 0
    while v27 < dword_4077F8_val:
        ca = bool(v27 & 0x2A)
        cb = bool(v27 & v4)
        if not ca and not cb:
            pass  # neither
        elif ca and cb:
            pass  # both: neither branch taken
        else:
            # exactly one of ca, cb
            v26 |= v27
        v27 *= 2
        v28 += 1

    v29 = v26
    v30 = 0
    while v30 < 1:
        v29 *= 2
        if dword_4077F8_val & v29:
            v29 ^= dword_4077F4_val
        v30 += 1

    # Step 12: recompute globals (same as step 3)
    dword_4077F8_val2 = 3
    dword_4077F8_val2 *= 51
    dword_4077F8_val2 += 102  # 255
    dword_4077F0_val2 = dword_4077F8_val2
    dword_4077F8_val2 = 255 * dword_4077F0_val2
    dword_4077F8_val2 += 127  # 65152
    dword_4077F4_val2 = dword_4077F8_val2
    dword_4077F8_val2 = dword_4077F4_val2 + 384  # 65536
    dword_4077F0_val2 += 1
    dword_4077F0_val2 <<= 7  # 32768
    dword_4077F4_val2 += 375
    dword_4077F4_val2 += 10  # 65537

    # Step 13: count v31 = v29 // 2
    v31 = 0
    v32 = v29
    while v32 >= 2:
        v32 -= 2
        v31 += 1
    v4 = v31

    return v31 == v3


def keygen(name: str) -> str:
    # Compute v3
    v3 = sum(ord(c) for c in name) + ord('\n')

    # We need to find a serial string such that after parsing, v31 == v3
    # The serial parsing: v4 starts at 0, for each digit d: v4 = (v4 + d) * 10
    # So the final v4 = N * 10 (where N is the numeric value but scaled by trailing *10)
    # Actually the parsed value is: if serial = "d1d2d3", v4 = ((d1*10+d2)*10+d3)*10
    # i.e., numeric_value * 10
    # We need to search over possible serial numeric values

    # Brute-force: try serial integers from 0 to 9999 (v4 < 0xFFFF after parsing)
    # parsed v4 = numeric * 10
    for numeric in range(1000):  # v4 = numeric*10 < 65535
        serial_int = numeric
        v4 = numeric * 10
        if v4 >= 0xFFFF:
            break
        serial_str = str(serial_int)
        if verify(name, serial_str):
            return serial_str
    return None



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
