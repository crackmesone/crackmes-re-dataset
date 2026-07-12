import struct
import ctypes

# Constants from the keygen source
INIT_CONSTANTS = b'135790dhsj475869'

def load_dwords(data):
    """Load 4 dwords from 16-byte data"""
    return list(struct.unpack_from('<4I', data))

def sub_math(a, b):
    """
    Implements the mystical subMath operation from the ASM.
    This is a 32-bit multiplication variant (likely modular multiplication).
    Based on the ASM code analysis - it appears to be a 64-bit multiply
    keeping only certain bits. This is a best-effort reconstruction.
    """
    # ASSUMPTION: subMath computes a kind of modular multiplication
    # The ASM splits into 16-bit halves and does cross-multiplications
    # This resembles a 32x32->64 bit multiply with specific bit extraction
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    
    a_lo = a & 0xFFFF
    a_hi = (a >> 16) & 0xFFFF
    b_lo = b & 0xFFFF
    b_hi = (b >> 16) & 0xFFFF
    
    # From ASM analysis:
    # esi = a_lo * b_lo
    esi = (a_lo * b_lo) & 0xFFFFFFFF
    
    # ecx = a_hi * b_lo + (esi >> 16)
    ecx = (a_hi * b_lo + (esi >> 16)) & 0xFFFFFFFF
    edi = ecx
    
    esi = esi & 0xFFFF
    ecx = ecx & 0xFFFF
    ecx = (ecx << 16) & 0xFFFFFFFF
    ecx = (ecx + esi) & 0xFFFFFFFF
    edx = ecx
    
    ecx = ecx & 0xFFFF
    edi = (edi >> 16) & 0xFFFF
    ecx = (ecx + edi) & 0xFFFFFFFF
    esi = ecx
    
    # Second half
    eax2 = a_lo
    ebx2 = b_hi
    eax2 = (eax2 * ebx2) & 0xFFFFFFFF
    edx2 = (edx >> 16) & 0xFFFF
    ecx2 = (ecx >> 16) & 0xFFFF  # but ecx was updated above
    # ASSUMPTION: following the ASM flow approximately
    eax2 = (eax2 + edx2 + ecx2) & 0xFFFFFFFF
    ecx = eax2
    esi2 = esi & 0xFFFF
    eax2 = eax2 & 0xFFFF
    eax2 = (eax2 << 16) & 0xFFFFFFFF
    esi2 = (esi2 + eax2) & 0xFFFFFFFF
    
    ebx2 = esi2
    edi2 = a_hi
    eax3 = b_hi  # from stack pop
    eax3 = (eax3 >> 16) if False else a_hi  # ASSUMPTION: reusing a_hi
    edi2 = (edi2 * eax3) & 0xFFFFFFFF  # ASSUMPTION
    esi3 = esi2 & 0xFFFF
    ecx3 = (ecx >> 16) & 0xFFFF
    edi2 = (edi2 + esi3 + ecx3) & 0xFFFFFFFF
    
    eax_final = edi2
    ebx2_hi = (ebx2 >> 16) & 0xFFFF
    edi2_hi = (edi2 >> 16) & 0xFFFF
    ebx2_hi = (ebx2_hi + edi2_hi) & 0xFFFFFFFF
    
    ecx_f = ebx2_hi
    eax_f = eax_final & 0xFFFF
    ebx_f = ebx2_hi & 0xFFFF
    ebx_f = (ebx_f << 16) & 0xFFFFFFFF
    ecx_f = (ecx_f >> 16) & 0xFFFF
    result = (eax_f + ebx_f + ecx_f) & 0xFFFFFFFF
    
    return result

def sub_fukk_buf(buf16):
    """
    subFukkBuf: operates on a 16-byte buffer.
    From the truncated ASM: uses constant 0x25F1CDB and does operations.
    ASSUMPTION: This is a cipher/hash step. We only have partial info.
    The function loads dwords from [esi] and applies transformations.
    Based on the constant 0x025F1CDB seen in the truncated writeup.
    """
    # ASSUMPTION: We reconstruct based on what's visible
    # The buffer is 16 bytes = 4 dwords
    dwords = list(struct.unpack_from('<4I', bytes(buf16)))
    
    MAGIC = 0x025F1CDB
    # ASSUMPTION: some rotation/XOR/multiply cipher on the 4 dwords
    # Since subFukkBuf is called with ESI pointing to szName+4 (16 bytes)
    # and uses lodsd (loads dword then advances esi), we guess it iterates
    for i in range(4):
        # ASSUMPTION: applies sub_math with MAGIC then some mixing
        dwords[i] = sub_math(dwords[i], MAGIC) & 0xFFFFFFFF
    
    result = bytearray(16)
    struct.pack_into('<4I', result, 0, *dwords)
    return result

def compute_serial(name):
    """
    Reconstructed keygen algorithm from keygen.asm:
    
    1. Copy name bytes: szName+4 overlapping copy of szName (16 bytes from name+4)
       Actually: copies szName to szName+4 (16 bytes), so szName+4..+20 = first 16 chars of name
    2. Load 4 dwords from '135790dhsj475869' as ebx,ecx,edx,edi
    3. XOR szName+4 buffer with [ebx,ecx,edx,edi] in rotating pattern, call subFukkBuf each time
       Repeat 7 times with rotating key order
    4. Serial = wsprintf("%lu", dword at szName+4), then truncate to 4 chars
    """
    # Prepare name buffer - pad/truncate to 32 bytes (0x20)
    name_bytes = name.encode('ascii', errors='replace')[:0x20]
    name_buf = bytearray(0x20)
    name_buf[:len(name_bytes)] = name_bytes
    
    # The overlapping copy: esi=szName, edi=szName+4, ecx=0x10 (16 bytes)
    # This copies bytes 0..15 of name to positions 4..19
    # Result: positions 4..19 contain first 16 bytes of name
    work = bytearray(0x20)
    work[:len(name_bytes)] = name_bytes
    # rep movsb: copy 16 bytes from work[0..15] to work[4..19]
    for i in range(16):
        work[4 + i] = work[i]  # overlapping, done byte by byte in order
    
    # Load initial constants from '135790dhsj475869'
    const_bytes = b'135790dhsj475869'
    ebx, ecx, edx, edi = struct.unpack_from('<4I', const_bytes)
    
    # Working buffer is work[4..19] (16 bytes)
    buf = bytearray(work[4:20])
    
    def xor_buf(buf, k0, k1, k2, k3):
        dwords = list(struct.unpack_from('<4I', bytes(buf)))
        dwords[0] = (dwords[0] ^ k0) & 0xFFFFFFFF
        dwords[1] = (dwords[1] ^ k1) & 0xFFFFFFFF
        dwords[2] = (dwords[2] ^ k2) & 0xFFFFFFFF
        dwords[3] = (dwords[3] ^ k3) & 0xFFFFFFFF
        result = bytearray(16)
        struct.pack_into('<4I', result, 0, *dwords)
        return result
    
    # Round 1: XOR with (ebx, ecx, edx, edi)
    buf = xor_buf(buf, ebx, ecx, edx, edi)
    buf = sub_fukk_buf(buf)
    
    # Round 2: XOR with (ecx, edx, edi, ebx)
    buf = xor_buf(buf, ecx, edx, edi, ebx)
    buf = sub_fukk_buf(buf)
    
    # Round 3: XOR with (edx, edi, ebx, ecx)
    buf = xor_buf(buf, edx, edi, ebx, ecx)
    buf = sub_fukk_buf(buf)
    
    # Round 4: XOR with (edi, ebx, ecx, edx)
    buf = xor_buf(buf, edi, ebx, ecx, edx)
    buf = sub_fukk_buf(buf)
    
    # Round 5: XOR with (ebx, ecx, edx, edi)
    buf = xor_buf(buf, ebx, ecx, edx, edi)
    buf = sub_fukk_buf(buf)
    
    # Round 6: XOR with (ecx, edx, edi, ebx)
    buf = xor_buf(buf, ecx, edx, edi, ebx)
    buf = sub_fukk_buf(buf)
    
    # Round 7: XOR with (edx, edi, ebx, ecx)
    buf = xor_buf(buf, edx, edi, ebx, ecx)
    # Note: no subFukkBuf call after the last XOR before wsprintf
    
    # Serial = wsprintf("%lu", dword at buf[0]) then take first 4 chars
    val = struct.unpack_from('<I', bytes(buf))[0]
    serial_str = str(val)  # %lu equivalent
    serial_str = serial_str[:4]  # szSerial[4] = 0 truncates to 4 chars
    
    return serial_str

def keygen(name):
    return compute_serial(name)

def verify(name, serial):
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
