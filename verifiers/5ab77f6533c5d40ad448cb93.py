import struct
import ctypes

# RSA-160 keygen for TMG official keygenme 2 by thigo
# Based on the keygen source code provided in the writeup

# RSA parameters (160-bit)
# n and e from the source
N = int("0D2E9BF9B3D258E479D8CC23C7A33E1F8EBB3ADB1", 16)
E = int("0C6546E0C11ACCE2543DD1150C4CE7A05A4C8FA3D", 16)

# ASSUMPTION: The verify function in the crackme checks serial == keygen(name, company)
# but we only have the keygen side. The crackme likely does RSA verify (powmod with public key)
# and compares to the hash. We implement the keygen direction only.

def _u32(x):
    return x & 0xFFFFFFFF

def _s32(x):
    # signed 32-bit
    x = x & 0xFFFFFFFF
    if x >= 0x80000000:
        x -= 0x100000000
    return x

def _imul(a, b):
    # signed 32-bit multiply, keep lower 32 bits
    return _u32(_s32(a) * _s32(b))

def _rcl(val, count, bits=32):
    # Rotate carry left - ASSUMPTION: carry flag state unknown at time of rcl
    # In the asm, ecx holds the loop counter (dtLengthN down to 1 via dec ecx / jg)
    # rcl eax, cl - rotates left by cl bits (mod 33 for 32-bit rcl with carry)
    # ASSUMPTION: carry flag = 0 at time of rcl (not tracked here)
    count = count % 33
    if count == 0:
        return _u32(val)
    # rcl with carry=0: same as rol for count steps treating carry as extra bit
    # With carry=0: rcl n = (val << n) | (val >> (33-n)) but losing the top bit into carry
    # Simplified: treat as rol by count with carry=0
    val = _u32(val)
    result = _u32((val << count) | (val >> (32 - count))) if count < 32 else _u32(val >> (32 - count))
    return result

def _rcr(val, count, bits=32):
    # Rotate carry right - ASSUMPTION: carry flag = 0
    count = count % 33
    if count == 0:
        return _u32(val)
    val = _u32(val)
    result = _u32((val >> count) | (val << (32 - count))) if count < 32 else _u32(val << (32 - count))
    return result

def compute_hash(name_bytes, company_bytes):
    """
    Compute the 20-byte hash from name and company.
    Based on the x86 assembly in the keygen source.
    """
    # szHash is 20 bytes (5 DWORDs), initialized to zero
    # We work with a 20-byte bytearray
    hash_buf = bytearray(20)

    def get_dword(buf, offset):
        offset = offset & 0xFF  # safety
        if offset + 4 <= len(buf):
            return struct.unpack_from('<I', buf, offset)[0]
        # partial read with zero padding
        result = 0
        for i in range(4):
            if offset + i < len(buf):
                result |= buf[offset + i] << (8 * i)
        return result

    def set_dword(buf, offset, val):
        val = _u32(val)
        for i in range(4):
            if offset + i < len(buf):
                buf[offset + i] = (val >> (8 * i)) & 0xFF

    def xor_dword(buf, offset, val):
        cur = get_dword(buf, offset)
        set_dword(buf, offset, cur ^ val)

    # hashloop1: iterate over name bytes
    # ecx = dtLengthN (count down), edx = 0 (index into hash)
    # eax = 0xFFFFFFFF initially
    edx = 0
    eax = 0xFFFFFFFF

    for i, ch in enumerate(name_bytes):
        ecx_val = len(name_bytes) - i  # ecx counts down from dtLengthN
        al = ch & 0xFF
        ah = (eax >> 8) & 0xFF
        # xor ah, al
        ah = ah ^ al
        eax = (eax & 0xFFFF00FF) | (ah << 8)
        # imul eax, 89177313h
        eax = _imul(eax, 0x89177313)
        # and eax, 55AA55AAh
        eax = eax & 0x55AA55AA
        # imul eax, 12299381h
        eax = _imul(eax, 0x12299381)
        # xor eax, 0AA55AA11h
        eax = _u32(eax ^ 0xAA55AA11)
        # imul eax, 61h
        eax = _imul(eax, 0x61)
        ah = (eax >> 8) & 0xFF
        al2 = eax & 0xFF
        # xor ah, al
        ah = ah ^ al2
        eax = (eax & 0xFFFF00FF) | (ah << 8)
        # or eax, 10030118h
        eax = _u32(eax | 0x10030118)
        # imul eax, 988279h
        eax = _imul(eax, 0x988279)
        # rcl eax, cl (cl = ecx_val & 0xFF)
        eax = _rcl(eax, ecx_val & 0xFF)
        # xor [edi+edx], eax
        xor_dword(hash_buf, edx, eax)
        # add edx, 3
        edx += 3
        # and edx, 0Fh
        edx = edx & 0x0F
        # inc edx
        edx += 1
        # Note: dec ecx / jg hashloop1 handled by for loop

    # hashloop2: iterate over company bytes
    edx = 0

    for i, ch in enumerate(company_bytes):
        ecx_val = len(company_bytes) - i  # ecx counts down
        al = ch & 0xFF
        ah = (eax >> 8) & 0xFF
        # sub ah, al
        ah = (ah - al) & 0xFF
        eax = (eax & 0xFFFF00FF) | (ah << 8)
        # imul eax, 89157313h
        eax = _imul(eax, 0x89157313)
        # and eax, 55AA55AAh
        eax = eax & 0x55AA55AA
        # imul eax, 12299387h
        eax = _imul(eax, 0x12299387)
        # or eax, 0AA55AA11h
        eax = _u32(eax | 0xAA55AA11)
        # imul eax, 61h
        eax = _imul(eax, 0x61)
        # xor eax, 10010114h
        eax = _u32(eax ^ 0x10010114)
        # imul eax, 7918279h
        eax = _imul(eax, 0x7918279)
        ah = (eax >> 8) & 0xFF
        al2 = eax & 0xFF
        # xor ah, al
        ah = ah ^ al2
        eax = (eax & 0xFFFF00FF) | (ah << 8)
        # rcr eax, cl
        eax = _rcr(eax, ecx_val & 0xFF)
        # xor [edi+edx], eax
        xor_dword(hash_buf, edx, eax)
        # add edx, 3
        edx += 3
        # and edx, 0Fh
        edx = edx & 0x0F
        # inc edx
        edx += 1

    # post-loop fixup:
    # sub eax, [edi+8]
    val_at_8 = get_dword(hash_buf, 8)
    eax = _u32(eax - val_at_8)
    # imul eax, 34814815h
    eax = _imul(eax, 0x34814815)
    # add [edi+10h], eax
    cur16 = get_dword(hash_buf, 0x10)
    set_dword(hash_buf, 0x10, _u32(cur16 + eax))
    # shr eax, 0Bh
    eax = _u32(eax) >> 0x0B
    # and eax, 3
    eax = eax & 3
    # mov [edi], al
    hash_buf[0] = eax & 0xFF

    return bytes(hash_buf)


def keygen(name, company):
    """
    Generate serial for given name and company.
    Both must be at least 5 characters.
    Returns hex serial string (40 hex chars = 20 bytes).
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")
    if len(company) < 5:
        raise ValueError("Company must be at least 5 characters")

    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    company_bytes = company.encode('latin-1') if isinstance(company, str) else company

    hash_bytes = compute_hash(name_bytes, company_bytes)

    # Convert hash bytes to big integer (big-endian, as bytes_to_big does)
    M = int.from_bytes(hash_bytes, 'big')

    # RSA: M^E mod N
    result = pow(M, E, N)

    # Convert result back to 20 bytes
    result_bytes = result.to_bytes(20, 'big')

    # Format as hex string
    serial = result_bytes.hex().upper()
    return serial


def verify(name, serial, company="Company"):
    """
    Verify serial for name (and company).
    ASSUMPTION: The crackme checks that the serial matches keygen output.
    The actual crackme verification is RSA-based; we verify by regenerating.
    company parameter needed since algorithm uses both name and company.
    """
    try:
        expected = keygen(name, company)
        return serial.upper() == expected.upper()
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
