import struct

def _compute_serial(name: str):
    """
    Implements the key-generation algorithm from the keygen assembly source.
    Returns the serial as an integer, or None if the brute-force loop fails.
    """
    THE_Q = b'PhroZenQ'

    # Step 1: take up to 8 bytes of name, pad with '0','1','2',... if shorter than 8
    buf = bytearray(name.encode('latin-1', errors='replace')[:8])
    name_len = len(buf)
    if name_len < 8:
        fill_char = ord('0')
        for i in range(8 - name_len):
            buf.append(fill_char + i)
    # buf is now exactly 8 bytes

    # Step 2: loop_hash1
    # ecx goes 4..1 (loop_hash1: mov ecx,4 ... loop)
    # for i in 0..3: buf[i] = buf[i] + buf[i + 4]
    # (esi/edi both start at Buffer, lodsb reads buf[0..3], bl = buf[ecx+3] where ecx starts at 4)
    # iteration 1: ecx=4, al=buf[0], bl=buf[4+3-1]? Let's trace carefully:
    # mov ecx,4 -> loop counts from 4 down to 1
    # lodsb -> al = buf[0], then buf[1], buf[2], buf[3]
    # mov bl, byte ptr [Buffer+ecx+3]:
    #   ecx=4: bl = buf[7], ecx=3: bl=buf[6], ecx=2: bl=buf[5], ecx=1: bl=buf[4]
    # add al,bl; stosb -> writes back to same position
    # So buf[0] += buf[7], buf[1] += buf[6], buf[2] += buf[5], buf[3] += buf[4]
    # (all mod 256)
    new_buf = bytearray(8)
    for i in range(4):
        ecx = 4 - i  # ecx starts at 4, decrements each iteration
        al = buf[i]
        bl = buf[ecx + 3]  # ecx=4->buf[7], ecx=3->buf[6], ecx=2->buf[5], ecx=1->buf[4]
        new_buf[i] = (al + bl) & 0xFF
    new_buf[4:8] = buf[4:8]
    buf = new_buf

    # Step 3: mov eax, dword ptr [Buffer]; mov dword ptr [Buffer+4], eax
    # copies bytes 0..3 into bytes 4..7
    buf[4] = buf[0]
    buf[5] = buf[1]
    buf[6] = buf[2]
    buf[7] = buf[3]

    # Step 4: loop_hash2 - XOR each byte with TheQ
    for i in range(8):
        buf[i] ^= THE_Q[i]

    # At this point buf[0..7] is the 8-byte hash.
    # The serial is derived as:
    #   buf[0] = buf[0]  (single byte, used as rotation amount later)
    #   buf[1..4] = dword at buf+1
    #   buf[5..8] = dword at buf+5  (but buf is only 8 bytes, so buf[5..7] + buf[0] padded)
    # Actually buf+5 as dword: bytes 5,6,7 and then wraps? 
    # ASSUMPTION: dword at buf+5 uses bytes buf[5], buf[6], buf[7], and buf[0] (wrap) - but
    # the assembly just reads memory linearly; buf has 0x29 bytes allocated so bytes beyond 7 are 0.
    # We'll treat buf[8] = 0 for the dword at buf+5.

    # Build the two dwords
    # dword at buf+1: bytes buf[1], buf[2], buf[3], buf[4] (little-endian)
    dword_buf1 = struct.unpack_from('<I', bytes(buf), 1)[0]
    # dword at buf+5: bytes buf[5], buf[6], buf[7], buf[8=0]
    buf_ext = bytes(buf) + b'\x00'  # extend to handle buf+5 dword
    dword_buf5 = struct.unpack_from('<I', buf_ext, 5)[0]

    # Step 5: brute-force loop
    # xor ecx,ecx -> cl=0
    # loop: ebx = ror32(dword_buf1, cl); if bl == cl -> match; cl++; if cl==0 -> fail
    def ror32(val, n):
        n = n & 31
        return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

    cl = 0
    found_cl = None
    while True:
        ebx = ror32(dword_buf1, cl)
        if (ebx & 0xFF) == cl:
            found_cl = cl
            break
        cl = (cl + 1) & 0xFF
        if cl == 0:
            return None  # no_match

    # match:
    # eax = ror32(dword_buf1, cl)
    eax = ror32(dword_buf1, found_cl)
    # xor eax, dword at buf+5
    eax ^= dword_buf5
    # cl = buf[0]
    cl2 = buf[0]
    # ror eax, cl
    eax = ror32(eax, cl2)
    return eax


def verify(name: str, serial) -> bool:
    """
    Verify a name/serial pair.
    serial can be int or string (decimal).
    """
    try:
        serial_int = int(serial)
    except (TypeError, ValueError):
        return False
    result = _compute_serial(name)
    if result is None:
        return False
    # The crackme displays the serial as an unsigned int via SetDlgItemInt with bSigned=0
    return (result & 0xFFFFFFFF) == (serial_int & 0xFFFFFFFF)


def keygen(name: str):
    """
    Generate the serial for the given name.
    Returns the serial as a decimal string, or None if generation fails (~1% of names).
    """
    result = _compute_serial(name)
    if result is None:
        return None
    return str(result & 0xFFFFFFFF)



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
