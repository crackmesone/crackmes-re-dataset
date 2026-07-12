import struct

def _prepare_buffer(name):
    # Take up to 40 bytes of name, work in a bytearray of 0x29 bytes
    buf = bytearray(0x29)
    name_bytes = name.encode('ascii', errors='replace')[:0x28]
    for i, b in enumerate(name_bytes):
        buf[i] = b
    name_len = len(name_bytes)

    # If name length < 8, pad with '0','1','2',... up to length 8
    if name_len < 8:
        pad_count = 8 - name_len
        for i in range(pad_count):
            buf[name_len + i] = ord('0') + i
        # name is now effectively 8 bytes
        # name_len for further ops treated as 8? No: the asm uses eax (original len)
        # but the loop fills ecx=8-eax bytes starting at Buffer+eax
        # After fill, we continue; eax still holds original name_len
        # But name_big label is jumped to, meaning all code below uses Buffer as-is
        effective_len = name_len  # eax not changed after fill
    else:
        effective_len = name_len

    # loop_hash1: for ecx=4 down to 1, i=0..3
    # lodsb from Buffer[0..3], add Buffer[ecx+3] i.e. Buffer[4..7], store back
    # ecx starts at 4, so indices: ecx=4->buf[4+3]=buf[7], ecx=3->buf[6], ecx=2->buf[5], ecx=1->buf[4]
    # esi and edi both start at Buffer[0], so reads and writes are to same positions sequentially
    # BUT: esi advances as we read, edi advances as we write -- they are the same pointer!
    # So buf[0] += buf[7], buf[1] += buf[6], buf[2] += buf[5], buf[3] += buf[4]
    # (ecx goes 4,3,2,1 -> buf[ecx+3] = buf[7],buf[6],buf[5],buf[4])
    # All values are byte (mod 256)
    tmp = bytearray(buf)  # copy to read from before modification? No, edi==esi, in-place
    # Actually edi==esi (same pointer), so writes affect subsequent reads
    # i=0: read buf[0], bl=buf[4+3]=buf[7], buf[0]=(buf[0]+buf[7])&0xff
    # i=1: read buf[1] (already modified? no, buf[1] not yet written), bl=buf[3+3]=buf[6], buf[1]=(buf[1]+buf[6])&0xff
    # i=2: read buf[2], bl=buf[2+3]=buf[5], buf[2]=(buf[2]+buf[5])&0xff
    # i=3: read buf[3], bl=buf[1+3]=buf[4], buf[3]=(buf[3]+buf[4])&0xff
    for i in range(4):
        ecx = 4 - i  # ecx counts down: 4,3,2,1
        buf[i] = (buf[i] + buf[ecx + 3]) & 0xff

    # mov eax, dword ptr [Buffer]; mov dword ptr [Buffer+4], eax
    # copies buf[0..3] to buf[4..7]
    dword0 = bytes(buf[0:4])
    buf[4] = dword0[0]
    buf[5] = dword0[1]
    buf[6] = dword0[2]
    buf[7] = dword0[3]

    # loop_hash2: xor buf[0..7] with TheQ = "PhroZenQ"
    TheQ = b"PhroZenQ"
    for i in range(8):
        buf[i] ^= TheQ[i]

    return buf


def _ror32(value, count):
    count = count & 31
    return ((value >> count) | (value << (32 - count))) & 0xffffffff


def _ror8(value, count):
    count = count & 7
    return ((value >> count) | (value << (8 - count))) & 0xff


def keygen(name):
    """Generate serial for a given name. Returns None if no serial found (rare edge case)."""
    buf = _prepare_buffer(name)

    # bruteforce loop: find cl (0..254) such that ror32(buf[1..4], cl) & 0xff == cl
    # buf[1..4] is the 32-bit value at offset 1 (little-endian)
    val_b1 = struct.unpack_from('<I', buf, 1)[0]
    val_b5 = struct.unpack_from('<I', buf, 5)[0]
    cl_found = None
    for cl in range(256):
        rotated = _ror32(val_b1, cl)
        if (rotated & 0xff) == cl:
            cl_found = cl
            break

    if cl_found is None:
        return None

    cl = cl_found
    # match:
    eax = _ror32(val_b1, cl)
    eax = eax ^ val_b5
    # ror eax, cl where cl = buf[0]
    cl2 = buf[0]
    eax = _ror32(eax, cl2)
    # serial is eax as unsigned int
    return str(eax & 0xffffffff)


def verify(name, serial):
    """Verify that serial matches the name."""
    expected = keygen(name)
    if expected is None:
        return False
    try:
        return int(serial) == int(expected)
    except ValueError:
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
