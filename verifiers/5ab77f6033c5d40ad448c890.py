# Night In Odessa by greedy_fly - keygen/verifier
# Based on solution by Demoth (keygen.cpp) and __s3r10u5__ writeup

def ror2(val):
    """16-bit rotate right by 2"""
    val = val & 0xFFFF
    return ((val >> 2) | (val << 14)) & 0xFFFF

def string_hash(name: str) -> int:
    """
    Compute hash of name string.
    Each byte is XORed with 0x6C then shifted right by 1 before hashing.
    The hash uses an Adler-32-like algorithm with mod 0xFFF1.
    """
    # Pre-process: xor each byte with 0x6C then shr 1
    data = bytearray()
    for ch in name.encode('ascii', errors='replace'):
        b = (ch ^ 0x6C) >> 1
        data.append(b & 0xFF)

    size = len(data)
    part1 = 1
    part2 = 0
    idx = 0

    while size != 0:
        block_size = min(size, 5552)
        size -= block_size
        while block_size != 0:
            block_size -= 1
            part1 += data[idx]
            part2 += part1
            idx += 1
        part2 %= 0xFFF1
        part1 %= 0xFFF1

    return ((part2 << 16) ^ 0x1C2A) | part1

def serial_to_dword(serial: str) -> int:
    """
    Convert serial string 'XXXXEXXXX' to a dword 0xXXXXXXXX.
    The 5th character (index 4) must be 'E'.
    First 4 hex chars -> high word, last 4 hex chars -> low word.
    Then bswap (little-endian to big-endian swap of 4 bytes).
    """
    hi_str = serial[0:4]
    lo_str = serial[5:9]
    hi = int(hi_str, 16)
    lo = int(lo_str, 16)
    combined = (hi << 16) | lo
    # bswap
    b0 = (combined >> 24) & 0xFF
    b1 = (combined >> 16) & 0xFF
    b2 = (combined >> 8) & 0xFF
    b3 = combined & 0xFF
    return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0

def serial_hash(serial_dword: int) -> int:
    """
    Recover the name hash from the serial dword.
    Inverse of getSerialByHash.
    
    From the disassembly:
      key2 (lo word of serial after bswap) = (hash_hi ^ 0x4DE2) << 1
        => hash_hi = (key2 >> 1) ^ 0x4DE2
      key1 (hi word of serial after bswap) = ror2(hash_lo + 0x7E) ^ 0x2EC9
        => ror2(hash_lo + 0x7E) = key1 ^ 0x2EC9
        => hash_lo + 0x7E = rol2(key1 ^ 0x2EC9)
        => hash_lo = rol2(key1 ^ 0x2EC9) - 0x7E
    
    Then: hash = (hash_hi << 16) ^ 0x1C2A | hash_lo
    """
    key1 = (serial_dword >> 16) & 0xFFFF  # hi word
    key2 = serial_dword & 0xFFFF          # lo word

    # Recover hash_hi from key2
    # key2 = (hash_hi ^ 0x4DE2) << 1  (16-bit)
    # So hash_hi ^ 0x4DE2 = key2 >> 1
    hash_hi = (key2 >> 1) ^ 0x4DE2
    hash_hi &= 0xFFFF

    # Recover hash_lo from key1
    # key1 = ror2(hash_lo + 0x7E) ^ 0x2EC9
    # ror2(hash_lo + 0x7E) = key1 ^ 0x2EC9
    # hash_lo + 0x7E = rol2(key1 ^ 0x2EC9)
    tmp = (key1 ^ 0x2EC9) & 0xFFFF
    # rol2 (rotate left by 2, 16-bit) is inverse of ror2
    hash_lo_plus_7e = ((tmp << 2) | (tmp >> 14)) & 0xFFFF
    hash_lo = (hash_lo_plus_7e - 0x7E) & 0xFFFF

    # Reconstruct hash: (hash_hi << 16) ^ 0x1C2A | hash_lo
    # ASSUMPTION: the reconstruction mirrors string_hash return: (part2<<16)^0x1C2A | part1
    return ((hash_hi << 16) ^ 0x1C2A) | hash_lo

def get_serial_by_hash(h: int) -> int:
    """
    From keygen.cpp:
      key1 = ror2((lo_word(hash) + 0x7E) & 0xFFFF) ^ 0x2EC9
      key2 = ((hi_word(hash) ^ 0x4DE2) << 1) & 0xFFFF
      serial_dword = (key1 << 16) | key2
    """
    key1 = (h & 0xFFFF)
    key1 = ror2((key1 + 0x7E) & 0xFFFF) ^ 0x2EC9
    key1 &= 0xFFFF

    key2 = (h >> 16) & 0xFFFF
    key2 = ((key2 ^ 0x4DE2) << 1) & 0xFFFF

    return (key1 << 16) | key2

def dword_to_serial(dword: int) -> str:
    """
    Convert dword to serial string 'XXXXEXXXX'.
    We need to reverse the bswap done in serial_to_dword.
    bswap is its own inverse.
    """
    # bswap
    b0 = (dword >> 24) & 0xFF
    b1 = (dword >> 16) & 0xFF
    b2 = (dword >> 8) & 0xFF
    b3 = dword & 0xFF
    swapped = (b3 << 24) | (b2 << 16) | (b1 << 8) | b0

    hi = (swapped >> 16) & 0xFFFF
    lo = swapped & 0xFFFF
    return '%04XE%04X' % (hi, lo)

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 6 or len(name) > 10:
        raise ValueError('Name must be 6 to 10 characters long')
    h = string_hash(name)
    serial_dword = get_serial_by_hash(h)
    return dword_to_serial(serial_dword)

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    Rules:
      - Name length: 6..10
      - Serial length: 9
      - Serial format: XXXXEXXXX (hex digits, 'E' at index 4)
      - serial_hash(serial_to_dword(serial)) == string_hash(name)
    """
    if len(name) < 6 or len(name) > 10:
        return False
    if len(serial) != 9:
        return False
    if serial[4] != 'E':
        return False
    # Validate hex chars
    try:
        int(serial[0:4], 16)
        int(serial[5:9], 16)
    except ValueError:
        return False

    name_h = string_hash(name)
    s_dword = serial_to_dword(serial)
    s_h = serial_hash(s_dword)
    return name_h == s_h


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
