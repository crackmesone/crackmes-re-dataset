# Reverse-engineered from naive_crackme by yanisto
# Based on solution writeups from crackmes.de
#
# The crackme reads up to 8 bytes from stdin into a buffer at 0x80483ba.
# That buffer is part of a larger memory region starting at 0x804800c.
# A checksum is computed over the region 0x804800c..0x8048418 (exclusive)
# by XOR-folding 32-bit dwords into EBX and summing into ECX.
# The valid checksum (EBX after the loop) must equal 0x19160493.
#
# The checksum region is ~0x40C bytes long and is mostly fixed program bytes.
# The password buffer sits at 0x80483ba within that region.
# Offset of password buffer within checksum region: 0x80483ba - 0x804800c = 0x3ae
# The password is read as 8 bytes (dl=8 in sys_read), but newline counts.
# So effective password bytes are up to 7 printable chars + newline.
#
# We cannot fully reconstruct the fixed bytes of the region without the
# original binary, so we cannot compute the exact required password.
# However, we document the algorithm and provide a verify stub.

import struct

# ASSUMPTION: The fixed bytes of the checksum region (all bytes except
# the 8 password bytes at offset 0x3ae..0x3b5) are unknown without the
# binary. We mark the fixed XOR-sum of all other dwords as UNKNOWN_FIXED_XOR.
# From the writeup, with an empty/newline-only input the computed EBX was
# 0xCC9080CD (seen in register dump after the read). But that was with
# ald's ptrace interference possibly changing memory. We cannot determine
# the exact fixed contribution without the binary.

# ASSUMPTION: The password buffer is zero-padded to 8 bytes after the
# newline (sys_read returns the raw bytes including '\n').

# The checksum algorithm (from 0x8048454):
# EBX = 0, ECX = 0
# ESI = 0x804800c
# loop:
#   EAX = DWORD at [ESI]; ESI += 4
#   EBX ^= EAX
#   ECX += EBX  (note: add ebx,ecx is actually add ecx,ebx meaning ECX += EBX)
#   if ESI <= 0x8048418: continue
# return (EBX in ebx, ECX in ecx)
# Valid condition: EBX == 0x19160493

TARGET_EBX = 0x19160493
REGION_START = 0x804800c
REGION_END   = 0x8048418  # exclusive upper bound (jbe means <= so last load at 0x8048414)
PASS_OFFSET  = 0x80483ba - REGION_START  # = 0x3ae
REGION_SIZE  = REGION_END - REGION_START  # = 0x40c bytes

def compute_checksum(region_bytes):
    """Compute EBX after the XOR-accumulation loop over the region."""
    ebx = 0
    ecx = 0
    # Loop loads dwords from offset 0; ESI starts at REGION_START
    # Loop condition: jbe (unsigned <=) 0x8048418, meaning continue while ESI <= 0x8048418
    # After lods ESI is incremented by 4, so last load is at ESI=0x8048414 (loads 0x8048414..0x8048417)
    # Then ESI becomes 0x8048418, compare 0x8048418 <= 0x8048418 => true => one more iteration?
    # ASSUMPTION: loop runs while (ESI after increment) <= 0x8048418,
    # meaning the last dword loaded starts at 0x8048414.
    size = REGION_END - REGION_START  # 0x40c bytes = 259 dwords + remainder
    num_dwords = (REGION_END - REGION_START) // 4
    for i in range(num_dwords):
        offset = i * 4
        dword = struct.unpack_from('<I', region_bytes, offset)[0]
        ebx = (ebx ^ dword) & 0xFFFFFFFF
        ecx = (ecx + ebx) & 0xFFFFFFFF
    return ebx, ecx

def verify(name, serial):
    """
    The crackme is serial-only (no name field used).
    'serial' should be the password string (without trailing newline).
    
    ASSUMPTION: We don't have the original binary bytes for the fixed
    part of the checksum region. This function cannot be fully implemented
    without those bytes. We document the algorithm only.
    """
    # ASSUMPTION: fixed_region is the binary content of 0x804800c..0x80483ba
    # and 0x80483c2..0x8048418 -- unknown without the binary.
    # If we had it, we would:
    #   1. Build the full region buffer
    #   2. Insert password bytes at PASS_OFFSET (padded/truncated to 8 bytes with newline)
    #   3. Compute checksum
    #   4. Check EBX == 0x19160493
    raise NotImplementedError(
        "Cannot verify without the original binary's fixed memory bytes. "
        "The algorithm is: XOR-fold all dwords in 0x804800c..0x8048414 into EBX; "
        "password is 7 chars + newline at offset 0x3ae; valid if EBX == 0x19160493."
    )

def keygen(name):
    """
    To generate a valid serial we would need to:
    1. Obtain fixed_bytes = all bytes of region except the 8 password bytes.
    2. Compute current EBX from fixed bytes (password bytes = 0).
    3. Determine what 8 bytes at PASS_OFFSET make EBX == TARGET_EBX.
    
    The XOR is associative, so:
      EBX_with_pass = EBX_fixed XOR (contribution of two password dwords)
    We need: EBX_fixed XOR pass_dword0 XOR (EBX_fixed XOR pass_dword0 XOR pass_dword1) == TARGET_EBX
    i.e., EBX_fixed XOR pass_dword0 XOR EBX_fixed XOR pass_dword0 XOR pass_dword1 == TARGET_EBX
    Simplifies to: pass_dword1 == TARGET_EBX  (if pass_dword0 cancels)
    
    ASSUMPTION: This simplification may be wrong depending on intermediate EBX state.
    Without the binary we cannot compute EBX_fixed.
    """
    # ASSUMPTION: placeholder - cannot generate without binary
    raise NotImplementedError(
        "Keygen requires the original binary to extract fixed checksum region bytes."
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
