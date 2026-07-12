# Reconstructed from writeup for keygenmev1 by pxor / d9a solution by ap0x
# ASSUMPTION: Several parts of the algorithm were truncated in the writeup.
# What is known:
#   1. Name is padded/repeated to 32 (0x20) chars
#   2. Serial must be exactly 17 chars long
#   3. Serial must have a '-' (0x2D) at position 9 (1-indexed), so format: XXXXXXXX-XXXXXXXX
#   4. Each half of the serial (around the '-') is parsed as a hex string (uppercase A-Z or 0-9)
#      chars < '0' or between ':' and 'A' or > 'Z' are rejected
#      digits 0-9: value = char - 0x30 (implicit from hex parse)
#      chars A-Z: value = char - 0x37
#      nibbles are accumulated: EBX = (EBX | nibble) ROL 4  => big-endian hex string to 32-bit
#   5. The actual comparison of computed serial vs computed name hash is TRUNCATED in writeup.
# ASSUMPTION: The two 8-char hex parts represent two 32-bit values derived from the name.

def _repeat_name_to_32(name):
    """Pad/repeat name to exactly 32 bytes as described in the writeup."""
    name_bytes = name.encode('ascii', errors='replace')
    n = len(name_bytes)
    if n == 0:
        return b'\x00' * 32
    result = bytearray()
    while len(result) < 32:
        result.extend(name_bytes)
    return bytes(result[:32])

def _rol32(val, r):
    val &= 0xFFFFFFFF
    r &= 31
    return ((val << r) | (val >> (32 - r))) & 0xFFFFFFFF

def _ror32(val, r):
    val &= 0xFFFFFFFF
    r &= 31
    return ((val >> r) | (val << (32 - r))) & 0xFFFFFFFF

def _parse_hex_part(s):
    """Parse an 8-char hex string (0-9, A-Z only) into a 32-bit int using the described algorithm.
    EBX starts at 0; for each char: nibble = char-0x30 (digit) or char-0x37 (A-Z); EBX = ROL4(EBX | nibble)
    """
    ebx = 0
    for ch in s:
        o = ord(ch)
        if 0x30 <= o <= 0x39:
            nibble = o - 0x30
        elif 0x41 <= o <= 0x5A:
            nibble = o - 0x37
        else:
            return None
        ebx = _rol32(ebx | nibble, 4)
    return ebx & 0xFFFFFFFF

# ASSUMPTION: The name hash function producing two 32-bit values is not fully shown.
# Based on the xlat table references and operations seen (XLAT, ROL, ADD, IMUL, NEG, NOT, ROR)
# we can only partially reconstruct. We implement a best-guess based on visible opcodes.

def _name_hash(name):
    """Compute two 32-bit hash values from the 32-byte padded name.
    ASSUMPTION: This is partially reconstructed. The exact xlat tables at 0x4031AB
    and 0x403163 are unknown. We approximate with identity (byte value).
    """
    padded = _repeat_name_to_32(name)
    
    # ASSUMPTION: hash1 and hash2 are computed over the padded name bytes
    # using the sequence of ops described in the writeup (ROL5, ADD, IMUL, NEG, etc.)
    # Without the xlat table contents we cannot be exact.
    
    h1 = 0
    h2 = 0
    for b in padded:
        # ASSUMPTION: approximate hash using visible ops
        eax = b
        eax = _rol32(eax, 5)
        eax = (eax + eax) & 0xFFFFFFFF
        eax = (eax * eax) & 0xFFFFFFFF
        eax = (-eax) & 0xFFFFFFFF  # NEG
        h1 = (h1 ^ eax) & 0xFFFFFFFF
    
    for b in padded:
        eax = b
        eax = (eax + eax) & 0xFFFFFFFF
        cl = eax & 0xFF
        eax = _rol32(eax, cl)
        eax = (~eax) & 0xFFFFFFFF  # NOT
        cl2 = (cl + (eax & 0xFF)) & 0xFF
        eax = _ror32(eax, cl2)
        eax = (eax + eax) & 0xFFFFFFFF
        h2 = (h2 ^ eax) & 0xFFFFFFFF
    
    return h1, h2

def _to_hex_part(val):
    """Convert 32-bit int to 8-char uppercase hex string using 0-9,A-F."""
    return format(val & 0xFFFFFFFF, '08X')

def verify(name, serial):
    """Verify name/serial pair."""
    if not name:
        return False
    # Serial must be 17 chars
    if len(serial) != 17:
        return False
    # 9th char (index 8) must be '-'
    if serial[8] != '-':
        return False
    part1 = serial[:8]
    part2 = serial[9:]
    # Each part must be valid hex (0-9, A-Z)
    v1 = _parse_hex_part(part1)
    v2 = _parse_hex_part(part2)
    if v1 is None or v2 is None:
        return False
    # ASSUMPTION: compare parsed serial parts against name hashes
    h1, h2 = _name_hash(name)
    return v1 == h1 and v2 == h2

def keygen(name):
    """Generate serial for given name.
    ASSUMPTION: relies on approximate hash; real hash requires xlat table contents.
    """
    h1, h2 = _name_hash(name)
    part1 = _to_hex_part(h1)
    part2 = _to_hex_part(h2)
    return part1 + '-' + part2


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
