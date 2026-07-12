# UCF Crackme2 by j0b - Partial reverse engineering
# Based on the writeup by Ak Kort [SOS group]
#
# The crackme involves:
# 1. A decryption step using a 256-byte CRC32-based key table (not relevant to key validation directly)
# 2. A keyfile checksum validation
#
# The keyfile checksum algorithm (from the writeup disassembly):
#   - First compute CRC32 of keyfile bytes [0..0xFF] (256 bytes) -> stored as starting value
#   - Then perform 0xFD outer iterations, each iterating over the keyfile bytes
#     with a complex inner loop involving mul, rol, xor, not operations
#   - Final ebx must equal 0xA69EC24E
#
# ASSUMPTION: The keyfile is exactly 256 bytes (0x100 bytes).
# ASSUMPTION: CRC32 table used is the standard CRC32 polynomial table (as hinted by the writeup).
# ASSUMPTION: The 'name' (username) is embedded in the keyfile somehow, but the exact format
#             is not described in the writeup. We treat the keyfile as a raw 256-byte blob.
# ASSUMPTION: The inner loop logic is reconstructed from the disassembly fragment as best as possible.
#             The exact loop structure is ambiguous from the writeup.

import struct

TARGET_CHECKSUM = 0xA69EC24E

def make_crc32_table():
    """Build standard CRC32 lookup table."""
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        table.append(crc & 0xFFFFFFFF)
    return table

CRC32_TABLE = make_crc32_table()

def crc32_bytes(data, init=0xFFFFFFFF):
    """Compute CRC32 over data bytes."""
    crc = init
    for b in data:
        crc = CRC32_TABLE[(crc ^ b) & 0xFF] ^ ((crc >> 8) & 0x00FFFFFF)
    return crc ^ 0xFFFFFFFF

def rol32(val, count):
    """Rotate left 32-bit value."""
    count = count & 31
    val = val & 0xFFFFFFFF
    return ((val << count) | (val >> (32 - count))) & 0xFFFFFFFF if count else val

def compute_keyfile_checksum(keyfile_bytes):
    """
    Reconstruct the checksum algorithm from the disassembly:

    ; cx = 0x100, si = start of keyfile (256 bytes)
    ; call crc32 -> eax stored at [01B2]
    ;
    ; outer loop: cx = 0xFD
    ;   si = start of keyfile
    ;   ebx = [01B2]  (initial crc32)
    ;   inner loop (uses lodsb / lodsw):
    ;     al = [si], si++
    ;     cx = sign_extend(al)
    ;     ax = [si], si += 2  (lodsw advances by 2)
    ;     eax = ax * cx  (16-bit mul, result in dx:ax -> we use 32-bit eax)
    ;     cl = [si]  (note: si not advanced here, but loop decrements ecx)
    ;     rol eax, cl
    ;     xor ebx, eax
    ;     cx = sign_extend(al)  (al from earlier lodsb)
    ;     rol ebx, cl
    ;     not eax
    ;     loop back to rol eax,cl  (inner loop count = cx from movsx cx,al)
    ;   sub si, 2
    ;   loop outer
    ;
    ; ASSUMPTION: This reconstruction of the inner/outer loop nesting is approximate.
    # The writeup says the algorithm is complex and the full details are truncated.
    """
    # ASSUMPTION: keyfile is exactly 256 bytes
    if len(keyfile_bytes) < 256:
        keyfile_bytes = keyfile_bytes + bytes(256 - len(keyfile_bytes))
    keyfile_bytes = bytes(keyfile_bytes[:256])

    # Step 1: CRC32 of first 256 bytes
    # ASSUMPTION: CRC32 uses standard algorithm with init=0
    init_crc = crc32_bytes(keyfile_bytes, init=0xFFFFFFFF)
    ebx = init_crc & 0xFFFFFFFF

    # Step 2: 0xFD outer iterations
    # ASSUMPTION: outer loop iterates 0xFD=253 times over keyfile bytes
    # ASSUMPTION: inner loop structure reconstructed from disassembly fragment
    for outer in range(0xFD):
        si = 0  # index into keyfile
        eax = ebx  # ASSUMPTION: eax starts as ebx each outer iteration

        while si < len(keyfile_bytes) - 2:
            al = keyfile_bytes[si]
            si += 1
            # movsx cx, al -> sign extend byte to 16-bit
            cx_val = al if al < 128 else al - 256

            # lodsw -> ax = word at [si], si += 2
            if si + 1 < len(keyfile_bytes):
                ax = struct.unpack_from('<H', keyfile_bytes, si)[0]
                si += 2
            else:
                break

            # mul cx -> eax = ax * cx (16x16 -> 32)
            eax = (ax * (cx_val & 0xFFFF)) & 0xFFFFFFFF

            # cl = [si] (byte at current si, si not advanced)
            if si < len(keyfile_bytes):
                cl = keyfile_bytes[si] & 0xFF
            else:
                break

            # inner loop count = abs(cx_val) or cx_val & 0xFFFF
            # ASSUMPTION: inner loop uses the original cx from movsx
            inner_count = cx_val & 0xFFFF
            if inner_count == 0:
                inner_count = 1  # avoid infinite loop

            for _ in range(inner_count & 0xFFFF):
                # rol eax, cl
                eax = rol32(eax, cl)
                # xor ebx, eax
                ebx = (ebx ^ eax) & 0xFFFFFFFF
                # rol ebx, al  (al = the lodsb byte)
                ebx = rol32(ebx, al)
                # not eax
                eax = (~eax) & 0xFFFFFFFF
                # loop decrements and goes back to rol eax,cl

        # sub si, 2 at end of outer iteration (no effect on our Python index)

    return ebx

def verify(name, serial):
    """
    ASSUMPTION: The keyfile is constructed by embedding the name in some way.
    The writeup does not specify the exact keyfile format.
    We treat 'serial' as a hex string representing the 256-byte keyfile.
    Returns True if the computed checksum equals 0xA69EC24E.
    """
    try:
        if isinstance(serial, str):
            # Try to interpret serial as hex-encoded keyfile
            keyfile = bytes.fromhex(serial)
        elif isinstance(serial, (bytes, bytearray)):
            keyfile = bytes(serial)
        else:
            return False
    except Exception:
        return False

    checksum = compute_keyfile_checksum(keyfile)
    return checksum == TARGET_CHECKSUM

def keygen(name):
    """
    ASSUMPTION: Cannot fully implement keygen without knowing:
    1. Exact keyfile format and where name is placed
    2. The fast search algorithm described (but truncated) in the writeup
    The writeup describes a search over last 8 bytes of the keyfile.
    """
    # ASSUMPTION: name bytes go at start of keyfile, rest is zeros
    # ASSUMPTION: we brute-force the last 4 bytes to hit the target
    import os

    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    # Build base keyfile: name + zeros to fill 248 bytes, then 8 bytes to search
    base = bytearray(248)
    for i, b in enumerate(name_bytes[:248]):
        base[i] = b

    # ASSUMPTION: brute-force last 8 bytes (this is practically infeasible for full search)
    # As the writeup describes, they used distributed computing / optimized search
    # We just return None indicating keygen is not feasible without the full algorithm
    # ASSUMPTION: returning placeholder
    raise NotImplementedError(
        "Keygen requires the full search algorithm described in the writeup, "
        "which was truncated. The checksum algorithm reconstruction is also approximate."
    )


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
