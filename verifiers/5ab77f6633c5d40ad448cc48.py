# Partial reconstruction of crackme.happytown.vc.0039
# The writeup was truncated and the full algorithm cannot be fully recovered.
# What is visible is a complex hash/mixing function operating on 4x32-bit state words
# derived from some input (likely name/serial split into DWORD chunks).
# Several sub-functions are reconstructed from the x86 assembly.

import struct

def rotr32(val, n):
    """Rotate right 32-bit"""
    val &= 0xFFFFFFFF
    n &= 31
    return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

def rotl32(val, n):
    """Rotate left 32-bit"""
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def sub_00401B40(edx, esi):
    """Rotate left edx by esi bits (32-bit)"""
    # mov ecx, 0x20 - esi; shr eax, cl (eax=edx); shl edx, cl (cl=esi); or eax, edx
    # This is rotl32(edx, esi)
    return rotl32(edx, esi)

def sub_00401B60(a, b, c, d):
    """(a XOR b) OR (c XOR d)"""
    # xor eax(a), ecx(b); xor ecx(c), edx(d); or eax, ecx
    return ((a ^ b) | (c ^ d)) & 0xFFFFFFFF

def sub_00401B80(a, b, c, d):
    """(~d AND b) OR (~c) OR a"""
    # eax=d; not eax; and eax,b (ecx=b); not ecx(c); or eax,ecx; or eax,a
    # args on stack: [esp+4]=a, [esp+8]=b, [esp+0xc]=c, [esp+0x10]=d
    eax = (~d) & 0xFFFFFFFF
    eax = eax & b & 0xFFFFFFFF
    ecx = (~c) & 0xFFFFFFFF
    eax = (eax | ecx) & 0xFFFFFFFF
    eax = (eax | a) & 0xFFFFFFFF
    return eax

def sub_00401BA0(a, b, c, d):
    """(~d AND a) XOR (~c AND b)"""
    # eax=d; not eax; and eax,a; not ecx(c); and ecx,b; xor eax,ecx
    eax = (~d) & a & 0xFFFFFFFF
    ecx = (~c) & b & 0xFFFFFFFF
    return (eax ^ ecx) & 0xFFFFFFFF

def sub_00401BC0(a, b, c, d):
    """(~a XOR b) OR (~d XOR c)"""
    eax = (~a) & 0xFFFFFFFF
    eax = (eax ^ b) & 0xFFFFFFFF
    ecx = (~d) & 0xFFFFFFFF
    ecx = (ecx ^ c) & 0xFFFFFFFF
    return (eax | ecx) & 0xFFFFFFFF

def u32(x):
    return x & 0xFFFFFFFF

# ASSUMPTION: The name is used to derive a 4-DWORD state and the serial
# is checked against a transformed version of that state.
# The full ht_hash function was truncated so we cannot fully reconstruct it.

def ht_hash_partial(state, key):
    """
    Partial reconstruction of ht_hash.
    state: list of 4 uint32 [w0, w1, w2, w3]
    key:   list of 3 uint32 [k0, k1, k2] (from the second struct)
    Returns modified state (partial - loop logic incomplete due to truncation).
    """
    edi, esi, ebp, ebx = state[0], state[1], state[2], state[3]
    k0, k1, k2 = key[0], key[1], key[2]

    # ASSUMPTION: loop counter and exact mixing not fully recoverable from truncated writeup
    # The visible code does operations like:
    # round_val = sub_00401B40((edi & 5), (edi & 0x18))
    # then mixing with state words and constants 0x32f1e4b, 0x596807cd, 0xde6f723a

    # Partial round 1 (first visible block)
    shift_val = u32(edi & 0x18)
    and_val = u32(edi & 5)
    r1 = sub_00401B40(and_val, shift_val)
    r1 = u32(r1 + edi)

    tmp = u32(~ebp + k0)
    tmp = u32(tmp + ebx)
    tmp2 = u32(esi + edi)
    tmp3 = tmp & tmp2
    r1 = r1 ^ tmp3

    f1 = sub_00401B60(edi, esi, ebp, ebx)
    r1 = u32(r1 | (u32(f1 + ebp)))
    # xor with some key word
    # ASSUMPTION: using k1 here based on pattern
    r1 = r1 ^ k1

    r1 = sub_00401B40(r1, 0)  # shift amount unknown
    edi = r1

    tmp_sum = u32(ebx + ebp + esi)
    edi_new = u32(tmp_sum + edi + 0x32f1e4b)
    edi_new = u32(edi_new ^ edi)

    # ASSUMPTION: return partial state; full algorithm not recoverable
    return [edi_new, esi, ebp, ebx]


def name_to_dwords(name):
    """Convert name string to list of uint32 values."""
    # ASSUMPTION: name is padded/chunked into 4-byte little-endian DWORDs
    padded = name.encode('latin-1')
    while len(padded) % 4 != 0:
        padded += b'\x00'
    return [struct.unpack_from('<I', padded, i)[0] for i in range(0, len(padded), 4)]


def serial_to_dwords(serial):
    """Convert serial string to list of uint32 values."""
    # ASSUMPTION: serial is dash-separated hex groups e.g. XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    try:
        parts = serial.replace('-', '').strip()
        # 4 DWORDs = 32 hex chars
        if len(parts) < 32:
            parts = parts.ljust(32, '0')
        return [int(parts[i*8:(i+1)*8], 16) for i in range(4)]
    except Exception:
        return [0, 0, 0, 0]


def verify(name, serial):
    """
    ASSUMPTION: The algorithm is not fully recoverable from the truncated writeup.
    This is a placeholder that always returns False unless the algorithm is completed.
    """
    # ASSUMPTION: full ht_hash algorithm needed; only partial is reconstructed
    if not name or not serial:
        return False

    name_dwords = name_to_dwords(name)
    serial_dwords = serial_to_dwords(serial)

    # ASSUMPTION: initial state comes from name-derived values
    # pad name_dwords to at least 4
    while len(name_dwords) < 4:
        name_dwords.append(0)

    state = name_dwords[:4]

    # ASSUMPTION: key comes from serial or some fixed derivation
    key = serial_dwords[:3] if len(serial_dwords) >= 3 else [0, 0, 0]

    # ASSUMPTION: result state is compared against serial_dwords
    result = ht_hash_partial(state, key)

    # Cannot complete verification - algorithm truncated
    # ASSUMPTION: first DWORD of result must match first DWORD of serial
    return result[0] == serial_dwords[0]


def keygen(name):
    """
    ASSUMPTION: Cannot generate valid serial without full algorithm.
    Returns a placeholder.
    """
    # ASSUMPTION: keygen not implementable from partial writeup
    return 'UNKNOWN-ALGORITHM-INCOMPLETE'



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
