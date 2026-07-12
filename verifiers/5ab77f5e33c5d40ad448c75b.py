# Reconstruction of GodsJiva Keygenme #1 serial algorithm
# Based on keygen ASM writeup by bundy
# Some parts are assumptions due to truncated writeup

def verify(name: str, serial: str) -> bool:
    generated = keygen(name)
    return generated == serial


def keygen(name: str) -> str:
    # Step 1: Uppercase the name
    name = name.upper()

    # Step 2: Pad name to 16 chars with '?' (0x3F) if shorter
    name_bytes = list(name.encode('ascii'))
    while len(name_bytes) < 16:
        name_bytes.append(0x3F)
    name_bytes = name_bytes[:16]

    # Step 3: Validate and transform each byte: must be in [0x20, 0x5F]
    # Then subtract 0x20 and AND with 0x3F
    transformed = []
    for b in name_bytes:
        if b > 0x5F or b < 0x20:
            raise ValueError(f"Bad name character: {chr(b)!r}")
        val = (b - 0x20) & 0x3F
        transformed.append(val)

    # Step 4: Pack transformed bytes into three 32-bit integers
    # using shifts as described in the ASM
    # Each 'word' (16-bit) is computed from groups of bytes
    # upd_name_1 = two words packed into a dword
    # Indices 0..15 in transformed[]

    t = transformed
    idx = 0

    # upd_name_1 part 1 (word): t[0]<<6 + t[1], shift<<4, t[2]>>2
    # eax = t[0]; eax = eax<<6 + t[1]; eax = eax<<4; eax += t[2]>>2
    part1_w1 = (((t[idx] << 6) + t[idx+1]) << 4) + (t[idx+2] >> 2)
    idx += 2  # after consuming t[0],t[1] and partial t[2]

    # upd_name_1 part 2: starts re-using t[2]
    # eax = t[2]; eax = eax<<6 + t[3]; eax = eax<<6 + t[4]; eax = eax<<2 + t[5]; eax += t[6]>>4 
    # ASSUMPTION: index continues from idx=2 for part2
    # From ASM: mov bl,[edx] (edx still at idx 2), shl eax,6, inc edx -> t[3], shl eax,6, inc edx -> t[4], shl eax,2, inc edx -> t[5], shr ebx,4 -> t[6]>>4
    # Actually re-read: after part1, edx was incremented to t[2] (0-indexed idx=2)
    # part1 used t[0], t[1], t[2] (partial shift)
    # then for part2: start at t[2] again (edx not incremented after shr ebx,2)
    # ASSUMPTION: edx points to t[2] at start of part2
    p2_idx = 2
    eax = t[p2_idx]; eax = (eax << 6) + t[p2_idx+1]; eax = (eax << 6) + t[p2_idx+2]
    eax = (eax << 2) + t[p2_idx+3]; eax = eax + (t[p2_idx+4] >> 4)
    part1_w2 = eax & 0xFFFF
    # After part2, edx points to t[6] (p2_idx+4)
    edx_after_part1 = p2_idx + 4  # = 6

    upd_name_1 = (part1_w1 & 0xFFFF) | ((part1_w2 & 0xFFFF) << 16)

    # upd_name_2 part 1: starts at edx=6
    # eax = t[6]; eax = eax<<6 + t[7]; eax = eax<<6 + t[8]
    i = edx_after_part1  # 6
    eax = t[i]; eax = (eax << 6) + t[i+1]; eax = (eax << 6) + t[i+2]
    up2_w1 = eax & 0xFFFF
    i += 3  # now i=9

    # upd_name_2 part 2:
    # eax = t[9]; eax = eax<<6 + t[10]; eax = eax<<4; eax += t[11]>>2
    # ASSUMPTION: same pattern as part1_w1
    eax = t[i]; eax = (eax << 6) + t[i+1]; eax = (eax << 4) + (t[i+2] >> 2)
    up2_w2 = eax & 0xFFFF
    i += 2  # consumed t[9],t[10], partial t[11]; edx points to t[11]

    upd_name_2 = (up2_w1 & 0xFFFF) | ((up2_w2 & 0xFFFF) << 16)
    edx_after_part2 = i  # = 11

    # upd_name_3 part 1: starts at edx=11
    # eax = t[11]; eax = eax<<6+t[12]; eax = eax<<6+t[13]; eax = eax<<2; eax += t[14]>>4
    i = edx_after_part2
    eax = t[i]; eax = (eax << 6) + t[i+1]; eax = (eax << 6) + t[i+2]
    eax = (eax << 2) + (t[i+3] >> 4)
    up3_w1 = eax & 0xFFFF
    i += 4  # consumed t[11]..t[14], edx at t[14]
    # ASSUMPTION: after shr ebx,4 edx is at t[14], not incremented

    # upd_name_3 part 2:
    # eax = t[14]; eax = eax<<6+t[15]; eax = eax<<6+t[16 - but we only have 16 chars 0-15]
    # ASSUMPTION: wraps or uses padded value; t has 16 elements (indices 0-15)
    # From ASM: mov bl,[edx]; add eax,ebx; shl eax,6; inc edx; mov bl,[edx]; add eax,ebx; shl eax,6; inc edx; mov bl,[edx]; add eax,ebx
    # Starting at t[14]: eax=t[14], <<6+t[15], <<6+t[16 - out of bounds]
    # ASSUMPTION: t[16] = 0 (array was padded to 16, index 16 doesn't exist, assume 0)
    t_extended = t + [0]  # extend with 0 for safety
    i = 14  # edx at t[14]
    eax = t_extended[i]; eax = (eax << 6) + t_extended[i+1]; eax = (eax << 6) + t_extended[i+2]
    up3_w2 = eax & 0xFFFF

    upd_name_3 = (up3_w1 & 0xFFFF) | ((up3_w2 & 0xFFFF) << 16)

    # Step 5: Multiply the three dwords as floats (fild/fmulp)
    mul_of_name = upd_name_1 * upd_name_2 * upd_name_3
    # Store as 64-bit little-endian
    import struct
    mul_bytes = struct.pack('<q', mul_of_name & 0xFFFFFFFFFFFFFFFF)

    # Step 6: XOR mul_of_name (8 bytes) with c3string
    # ASSUMPTION: c3string is a fixed 8-byte constant in the binary; exact value unknown
    # ASSUMPTION: Using placeholder - this is a CRITICAL UNKNOWN
    # The actual c3string would need to be extracted from the crackme binary
    c3string = b'C3STRNG!'  # ASSUMPTION: placeholder constant

    xor_data = bytes([mul_bytes[i] ^ c3string[i] for i in range(8)])

    # Step 7: Convert xor_data to serial string using nibble-based table lookup
    # From ASM: each byte is split into high nibble and low nibble
    # table lookup: if value < 0x10 use directly; else NOT and set a bitmask bit
    # ASSUMPTION: my_table maps nibbles to chars; exact table unknown
    # ASSUMPTION: The final serial is a hex-like string of the xor_data
    # Based on common patterns in crackmes of this era, serial is likely hex-encoded
    # with possible transformation
    # ASSUMPTION: simplistic fallback - hex encode xor_data
    serial = xor_data.hex().upper()
    # ASSUMPTION: actual formatting (dashes, length) unknown due to truncated writeup
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
