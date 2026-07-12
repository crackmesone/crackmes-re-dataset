# Reverse-engineered keygen for zugo_keygenme_1
# Based on the assembly writeup by maxtreme / tRUE-TEAM
# 
# The algorithm has several stages:
# 1. MakeCrypto: processes the username into a 0x44-byte Buffer1
#    (appears to be an MD5 or custom hash - truncated in writeup)
# 2. A weighted sum loop over Buffer1[0..0x3F]
# 3. Several arithmetic transforms to produce EBP and ESI
# 4. A loop (8 iterations) picking chars from Buffer1 via modulo
# 5. Another loop (0x32 iterations) of: ESI = (0x487FD1B3 - EDX) * 0x1551A2D
# 6. Eliminate() converts 3 Temp buffers to integers
# 7. XOR chain to produce 4 serial parts
# 8. Format: "%lX-%lX-%lX-%lX"
#
# ASSUMPTION: MakeCrypto is an MD5 hash of the username.
#   The real MakeCrypto is a custom routine (writeup truncated).
#   We use Python's hashlib.md5 as a stand-in, taking the 16-byte
#   digest and padding with zeros to 0x44 bytes.
# ASSUMPTION: Change() stores a single byte from Buffer1 into Temp buffers
#   (picks Buffer1[esi], Buffer1[esi+1], Buffer1[esi+2] into Temp1,2,3)
# ASSUMPTION: Eliminate() converts the Temp buffer (which holds a hex-ASCII
#   string produced by Change) into a 32-bit integer via wsprintf "%0.8X".
#   Looking at the code, Change() is called with push 1 and a pointer into
#   Buffer1, suggesting it copies 1 byte. Eliminate() likely reads the byte
#   value stored in Temp as an integer.

import hashlib
import struct

def make_crypto(name: str) -> bytes:
    # ASSUMPTION: MakeCrypto produces 0x44 bytes; we use MD5 padded to 0x44
    raw = name.encode('latin-1')
    digest = hashlib.md5(raw).digest()  # 16 bytes
    buf = bytearray(digest)
    buf += b'\x00' * (0x44 - len(buf))
    return bytes(buf[:0x44])

def to_int32(v):
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def to_uint32(v):
    return v & 0xFFFFFFFF

def generate(name: str):
    buf1 = make_crypto(name)

    # Weighted sum: edx starts at 2, ecx=0x40 iterations
    # sum += buf1[i] * (i+2)  (signed byte * int)
    esi = 0
    edx = 2
    for i in range(0x40):
        byte_val = struct.unpack('b', bytes([buf1[i]]))[0]  # MOVSX (signed)
        esi += byte_val * edx
        edx += 1

    esi = to_int32(esi)

    # IMUL ESI, ESI, 0x5B6A10EE
    esi = to_int32(esi * 0x5B6A10EE)

    # EBP = 0x0548BA781 - ESI (32-bit)
    ebp = to_uint32(0x548BA781 - esi)

    # XOR EBP, 0x1054BD97
    ebp = to_uint32(ebp ^ 0x1054BD97)

    # SUB EBP, 0xB7845A5
    ebp = to_uint32(ebp - 0xB7845A5)

    ebx = ebp & 0xFFFF  # low 16 bits

    # Loop 8 times picking chars from Buffer1
    # ASSUMPTION: Temp1, Temp2, Temp3 accumulate last-picked byte values
    esi2 = 0
    edi2 = 0
    temp1_byte = 0
    temp2_byte = 0
    temp3_byte = 0
    for _ in range(8):
        # EAX = (ESI+1) * EBX - EDI + ESI
        eax = to_int32((esi2 + 1) * to_int32(ebx) - edi2 + esi2)
        # IDIV 0x14
        remainder = eax % 20  # Python % always non-negative for positive divisor
        # But we need signed division remainder matching x86 IDIV
        # x86 IDIV: remainder has same sign as dividend
        if eax < 0:
            remainder = -((-eax) % 20)
            if remainder != 0:
                remainder = eax - (eax // 20) * 20  # ASSUMPTION: signed mod
        esi2 = remainder  # EDX = remainder after IDIV

        idx0 = esi2 % len(buf1)
        idx1 = (esi2 + 1) % len(buf1)
        idx2 = (esi2 + 2) % len(buf1)
        temp1_byte = buf1[idx0]
        temp2_byte = buf1[idx1]
        temp3_byte = buf1[idx2]
        edi2 += 1

    # Second loop: 0x32 iterations
    # ESI = (0x487FD1B3 - EDX) * 0x1551A2D
    edx_val = to_uint32(ebp)
    for _ in range(0x32):
        esi_val = to_uint32(0x487FD1B3 - edx_val)
        esi_val = to_uint32(esi_val * 0x1551A2D)
        edx_val = esi_val
    final_esi = esi_val

    # Eliminate: convert Temp byte to 32-bit int
    # ASSUMPTION: Eliminate() returns the byte value in Temp as an integer
    t1 = temp1_byte
    t2 = temp2_byte
    t3 = temp3_byte

    # XOR chain
    xor_addr = to_uint32(t1 ^ ebp)
    part1 = final_esi
    part2 = xor_addr
    ebx2 = to_uint32(t2 ^ ebp ^ xor_addr)
    part3 = ebx2
    part4 = to_uint32(t3 ^ ebp ^ ebx2)

    serial = "%X-%X-%X-%X" % (part1, part2, part3, part4)
    return serial

def verify(name: str, serial: str) -> bool:
    expected = generate(name)
    return serial.upper() == expected.upper()

def keygen(name: str) -> str:
    return generate(name)


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
