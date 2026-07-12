# Reconstruction of 'Assassination by BSwap' serial validation algorithm
# Based on the writeup by kao
#
# Key facts from the writeup:
# 1. Name and serial must be >= 3 chars (but there's a bug that makes any length work)
# 2. Special case: if name == 'BSwap', instant win
# 3. Serial bytes (except first) are decremented by 4 before hashing:
#    for i in range(1, name_len): serial[i] -= 4
# 4. Both name and serial are passed through a hashing function.
#    The hashing function takes 3 values: buf[0..3], buf[4..7], buf[8..11] as 32-bit ints
# 5. The final hashed name bytes must equal the final hashed serial bytes.
#
# The hash function operates with ecx=0x1e (30 iterations) and uses
# three 32-bit words (A=buf[0:4], B=buf[4:8], C=buf[8:12]).
# The writeup says the NAME hash function is 'way longer' but 'they look similar'.
# The author's approach was: reverse the serial hash, produce serial from name hash output.
# Since the name and serial hash functions appear to be the same (or very similar),
# and the check compares byte-by-byte, the easiest keygen strategy is:
# compute hash(name), then find serial bytes such that hash(serial_modified) == hash(name)
# BUT since we can't fully invert the hash, we use a simpler approach:
# if name_hash == serial_hash, and both use same function, set serial_modified = name,
# then reverse the -4 transformation.
#
# ASSUMPTION: The name hash and serial hash functions are identical.
# ASSUMPTION: The comparison is over the first N bytes where N = name_len.
# ASSUMPTION: Buffers are zero-padded to at least 12 bytes.
# ASSUMPTION: The serial_modified buffer is name_len bytes (indices 0..name_len-1),
#             with index 0 unchanged and indices 1..name_len-1 having -4 applied.

import struct
import ctypes

def _u32(x):
    return x & 0xFFFFFFFF

def _s32(x):
    return ctypes.c_int32(x).value

def _bswap32(x):
    x = _u32(x)
    return ((x & 0xFF) << 24) | ((x & 0xFF00) << 8) | ((x & 0xFF0000) >> 8) | ((x >> 24) & 0xFF)

def hash_function(buf):
    """
    Implements the hash function shown in the writeup.
    buf is a bytearray of at least 12 bytes (zero-padded).
    Returns (eax, ebx, edi) as 32-bit unsigned ints stored back into buf.
    """
    # Load three 32-bit words from buffer
    A = struct.unpack_from('<I', buf, 0)[0]  # arg_0_buffer
    B = struct.unpack_from('<I', buf, 4)[0]  # arg_4_BufPlus4
    C = struct.unpack_from('<I', buf, 8)[0]  # arg_8_bufPlus8

    ecx = 0x1e
    edi = C
    eax = B
    ebx = A
    edx = 0

    ebx_init = _u32(A - 4)  # sub ebx, 4 at start
    ebx = ebx_init

    for _ in range(ecx):
        # add edi, eax
        edi = _u32(edi + eax)
        # add eax, ebx
        eax = _u32(eax + ebx)
        # xchg eax, edi
        eax, edi = edi, eax
        # xchg eax, ebx
        eax, ebx = ebx, eax
        # lea eax, [edx+edx]
        eax = _u32(edx + edx)
        # mov edx, [arg_0_buffer]; sub edx, 4
        edx = _u32(A - 4)
        # xor eax, ebx
        eax = _u32(eax ^ ebx)
        # xor eax, edx
        eax = _u32(eax ^ edx)
        # mov edi, eax; sub edi, edx; xor edi, ebx
        edi = _u32(eax - edx)
        edi = _u32(edi ^ ebx)
        # mov ebx, eax; xor edi, eax
        ebx = eax
        edi = _u32(edi ^ eax)
        # bswap ebx
        ebx = _bswap32(ebx)
        # mov esi, ebx; and esi, 0xFFFFFF00; bswap esi; mov ebx, esi
        esi = _u32(ebx & 0xFFFFFF00)
        esi = _bswap32(esi)
        ebx = esi
        # imul ebx, edi
        ebx = _u32(_s32(ebx) * _s32(edi))
        # add ebx, edx
        ebx = _u32(ebx + edx)
        # mov edx, eax; neg edx
        edx = _u32(-_s32(eax))
        # xor ebx, edx
        ebx = _u32(ebx ^ edx)
        # add edi, ebx
        edi = _u32(edi + ebx)
        # loop

    # sub edx, edx  => edx = 0 (clears edx, not relevant to output)
    # Result stored back:
    # bSerialBuffer = eax, bSerialPlus4 = ebx, bSerialPlus8 = edi
    result = bytearray(12)
    struct.pack_into('<I', result, 0, eax)
    struct.pack_into('<I', result, 4, ebx)
    struct.pack_into('<I', result, 8, edi)
    return result

def make_buf(s):
    """Pad string bytes to 12-byte buffer."""
    b = bytearray(s.encode('latin-1'))
    b = b[:12]
    while len(b) < 12:
        b.append(0)
    return b

def verify(name, serial):
    """
    Returns True if the serial is valid for the given name.
    """
    # Special case
    if name == 'BSwap':
        return True

    # Length check (must be >= 3 each)
    if len(name) < 3 or len(serial) < 3:
        return False

    name_len = len(name)

    # Step 8: modify serial buffer - subtract 4 from each byte except first
    serial_bytes = bytearray(serial.encode('latin-1'))
    for i in range(1, name_len):
        if i < len(serial_bytes):
            serial_bytes[i] = (serial_bytes[i] - 4) & 0xFF

    # Pad both to 12 bytes
    name_buf = make_buf(name)
    serial_buf = bytearray(serial_bytes[:12])
    while len(serial_buf) < 12:
        serial_buf.append(0)

    # Hash both
    # ASSUMPTION: name hash function is the same as serial hash function
    name_hashed = hash_function(name_buf)
    serial_hashed = hash_function(serial_buf)

    # Compare first name_len bytes
    # ASSUMPTION: comparison is byte-by-byte for name_len bytes
    cmp_len = min(name_len, 12)
    return name_hashed[:cmp_len] == serial_hashed[:cmp_len]

def keygen(name):
    """
    Generate a serial for the given name.
    Strategy: since hash(name_buf) must equal hash(serial_modified_buf),
    set serial_modified = name (so they hash identically),
    then reverse the -4 transformation to get the actual serial.
    """
    if name == 'BSwap':
        return 'BSwap'

    # ASSUMPTION: serial_modified == name bytes means hashes match
    # Reverse: serial[i] = serial_modified[i] + 4 for i in 1..name_len-1
    serial_bytes = bytearray(name.encode('latin-1'))
    for i in range(1, len(serial_bytes)):
        serial_bytes[i] = (serial_bytes[i] + 4) & 0xFF

    return serial_bytes.decode('latin-1')


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
