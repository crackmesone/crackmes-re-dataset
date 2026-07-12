import struct
import ctypes

def _ror32(val, n):
    val &= 0xFFFFFFFF
    return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

def compute_name_hash(name: str) -> int:
    """
    Hash algorithm from the crackme:
    1. Pad name bytes to multiple of 4
    2. XOR each 4-byte chunk into EDX, then ROR EDX by 16 (0x10)
    """
    name_bytes = name.encode('ascii', errors='replace')
    # Pad to multiple of 4
    padded = name_bytes + b'\x00' * ((4 - len(name_bytes) % 4) % 4)
    edx = 0
    for i in range(0, len(padded), 4):
        chunk = struct.unpack_from('<I', padded, i)[0]
        edx ^= chunk
        edx = _ror32(edx, 16)  # ROR EDX, 10h  (0x10 == 16 decimal)
    return edx & 0xFFFFFFFF

# ---------------------------------------------------------------------------
# The VERIFY logic is taken from solution 2 (the actual crackme check).
# The serial is 16 hex chars = two 8-hex-char halves.
# Let serial_hi = first 8 chars interpreted as hex (little-endian 32-bit printed with %.8X)
# Let serial_lo = next 8 chars
# The keygen does:
#   eax = random | hash_edx
#   push eax          -> serial_part1 (first 8 hex chars)
#   edx2 = ~hash_edx
#   push edx2         -> serial_part2 (next 8 hex chars)
#   wsprintfA with "%.8X%.8X"
#
# The verify (from solution 2 disassembly) does:
#   Read name -> compute hash -> edx (saved on stack)
#   Read serial (16 hex chars) into buffer at 0x403004
#   Manipulate the serial bytes:
#       esi = buf+8 (second 8 chars of serial string = chars 8..15)
#       edi = buf+16 (third 'slot', i.e. buf+0x10)
#       bl = [esi]  (first byte of second half of serial string)
#       copy 8 bytes from esi to edi (REP MOVS, ecx=8)
#       XOR byte at buf+0x0C with bl
#   Then call sub_4011A8 on buf (first 8 chars) -> call it hash_func
#   Then call sub_4011A8 on buf+0x14 (the moved+xored data) -> second result
#   NOT second_result
#   TEST first_result, NOT(second_result)  -> must be nonzero (i.e. first_result & ~second_result != 0)
#   AND NOT(second_result) with first_result  -> then SUB edx_from_stack  -> must be zero
#
# This is complex and sub_4011A8 is not shown. We cannot fully reconstruct verify without it.
# ASSUMPTION: sub_4011A8 converts the 8 hex-char string at the pointer to a 32-bit integer
#             (i.e. parses the hex string as a DWORD, big-endian as printed by %.8X)
# ASSUMPTION: The verify check reduces to:
#   part1 = int(serial[0:8], 16)
#   part2 = int(serial[8:16], 16)
#   (part1 & ~part2) - name_hash == 0   AND   (part1 & ~part2) != 0
# This is consistent with the keygen: part1 = rand|hash, part2 = ~hash
#   ~part2 = hash,  part1 & hash = (rand|hash) & hash = hash (when rand & hash may vary)
#   Actually (rand|hash) & hash = hash always, so (part1 & ~part2) == hash == name_hash

def _parse_hex_dword(s):
    """Parse an 8-char hex string (as printed by %.8X) to a 32-bit int."""
    return int(s, 16) & 0xFFFFFFFF

def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Serial must be exactly 16 uppercase hex characters.
    ASSUMPTION: sub_4011A8 parses the 8-char hex string to a DWORD.
    ASSUMPTION: check is (part1 & ~part2) == name_hash and (part1 & ~part2) != 0
    """
    if len(serial) != 16:
        return False
    try:
        part1 = _parse_hex_dword(serial[0:8])
        part2 = _parse_hex_dword(serial[8:16])
    except ValueError:
        return False

    name_hash = compute_name_hash(name)
    not_part2 = (~part2) & 0xFFFFFFFF
    combined = (part1 & not_part2) & 0xFFFFFFFF

    # Must be nonzero AND equal to name_hash
    if combined == 0:
        return False
    return combined == name_hash

def keygen(name: str) -> str:
    """
    Generate a valid serial for a given name.
    keygen logic from solution 1:
      part1 = random_val | name_hash
      part2 = ~name_hash
      serial = f"{part1:08X}{part2:08X}"
    We use a fixed 'random' value for reproducibility.
    """
    import random
    name_hash = compute_name_hash(name)
    if name_hash == 0:
        # ASSUMPTION: if hash is 0 the keygen still produces a serial but verify may fail
        # Use a nonzero random component to ensure combined != 0
        rand_val = random.randint(1, 0xFFFFFFFF)
    else:
        rand_val = random.randint(0, 0xFFFFFFFF)
    part1 = (rand_val | name_hash) & 0xFFFFFFFF
    part2 = (~name_hash) & 0xFFFFFFFF
    return f"{part1:08X}{part2:08X}"


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
