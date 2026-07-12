import ctypes

def hash_name(name: str):
    """
    Replicates hashName() from knightcm2.cpp using 32-bit signed arithmetic.
    Returns (hash1, hash2, hash3) as Python ints (may be negative).
    """
    def to_s32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    def to_u32(v):
        return v & 0xFFFFFFFF

    length = len(name)
    name_bytes = [ord(c) for c in name]

    # Determine hash2/hash3 initial value
    if (length & 1) != 0:
        # odd length
        mid = name_bytes[length // 2]
        h = mid & 0xFFFFFFFE
    else:
        # even length
        h = (name_bytes[length // 2 - 1] + name_bytes[length // 2]) // 2
        h = h & 0xFFFFFFFE

    hash2 = to_s32(h)
    hash3 = to_s32(h)

    # Sum chars from len/2+1 to len-1
    temp = 0
    for i in range(length // 2 + 1, length):
        temp += name_bytes[i]

    # kinda short rotr: (temp<<12 | temp>>4) & 0xffff
    temp = to_u32(temp)
    temp = ((temp << 12) | (temp >> 4)) & 0xFFFF
    temp = to_s32(temp)

    hash2 = to_s32(hash2 + temp)
    hash3 = to_s32(hash3 * temp)

    # Recalculate len
    length2 = (length // 2) - ((~(length & 1)) & 1)

    temp2 = 0
    for i in range(length2):
        temp2 += name_bytes[i] ^ 32

    temp2 = to_u32(temp2)
    temp2 = ((temp2 << 12) | (temp2 >> 4)) & 0xFFFF
    temp2 = to_s32(temp2)

    # ((temp2 * hash2) & 0xFFFF...) ^ hash2  -- the multiply is 32-bit
    val = to_s32(to_s32(temp2 * hash2) ^ hash2)

    # Simplification from comments:
    # hash1 = val ^ hash2
    # hash2 = hash2  (unchanged)
    # hash3 = hash3  (unchanged)
    hash1 = to_s32(val ^ hash2)
    # hash2 stays as is
    # hash3 stays as is

    return hash1, hash2, hash3


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Serial format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX (5 hex groups, each 5 hex digits)
    """
    if len(name) < 5:
        raise ValueError('Name is too short (min 5 chars)')

    def to_s32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    hash1, hash2, hash3 = hash_name(name)

    # Need to find key[1], key[2], key[3] such that:
    # hash3 == key[3] * key[2]
    # (key[1] - hash2) * key[1] == -hash3
    # key[3] + key[2] == hash2
    #
    # From keygen.asm:
    # Cycle1: find RS01[1] (= key[1] before >>12) in 0..0xFF such that:
    #   -hash3 == RS01[1] * (RS01[1] - hash2)
    # Cycle2: find RS01[2] in 0..0xFF such that:
    #   (hash2 - RS01[2]) * RS01[2] == hash3
    #   RS01[3] = hash2 - RS01[2]

    RS1 = None
    neg_hash3 = to_s32(-hash3)
    for a in range(0x100):
        val = to_s32(to_s32(a - hash2) * a)
        if val == neg_hash3:
            RS1 = a
            break

    if RS1 is None:
        raise ValueError('Could not find RS01[1] for name: ' + name)

    RS2 = None
    for a in range(0x100):
        val = to_s32(to_s32(hash2 - a) * a)
        if val == hash3:
            RS2 = a
            break

    if RS2 is None:
        raise ValueError('Could not find RS01[2] for name: ' + name)

    RS3 = to_s32(hash2 - RS2)

    # RR = (hash2 - 1) * RS1
    RR = to_s32(to_s32(hash2 - 1) * RS1)

    # RSUM = (hash1 / hash2) * 2  (signed integer division)
    import math
    # Python // does floor division, C does truncation toward zero
    def trunc_div(a, b):
        return int(a / b)  # truncation toward zero

    RSUM = to_s32(trunc_div(hash1, hash2) * 2)

    # RS01[4] = (RR + RSUM) / 2  (arithmetic shift right = truncation for positives, floor for negatives)
    RS4 = to_s32((to_s32(RR + RSUM)) >> 1)

    # RS01[0] = -((RSUM - RR) / 2)
    RS0 = to_s32(-to_s32(to_s32(RSUM - RR) >> 1))

    # Now pack into R[0..4]
    # R[0] = RS0 & 0xFFFFF
    R0 = RS0 & 0xFFFFF
    # R[1] = ((RS0 & 0xFFF00000) >> 20) | (RS1 << 12)
    R1 = (((RS0 & 0xFFF00000) >> 20) | ((RS1 & 0xFFFFF) << 12)) & 0xFFFFF
    # R[2] = (RS2 << 12) | ((RS4 & 0xFFF00000) >> 20)
    R2 = (((RS2 & 0xFF) << 12) | (((RS4 & 0xFFFFFFFFF) & 0xFFF00000) >> 20)) & 0xFFFFF
    # R[3] = RS3
    R3 = RS3 & 0xFFFFF
    # R[4] = RS4 & 0xFFFFF
    R4 = RS4 & 0xFFFFF

    serial = '%05X-%05X-%05X-%05X-%05X' % (R0, R1, R2, R3, R4)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair. Reimplements checkIt() from knightcm2.cpp.
    """
    if len(name) < 5:
        return False

    # Check serial length == 29
    code = serial
    if len(code) != 29:
        return False

    # checkPads: checks positions 5,11,17,23 are separators
    # !(BYTE)(~(code[11]|(code[5]<<4)^(code[5]>>4))) &&
    # !(BYTE)(((code[23]<<4)^(code[17])|(code[23]>>4))+1)
    # Essentially checks that dashes are at positions 5, 11, 17, 23
    # The original uses char arithmetic; the simplest interpretation is the dashes check
    # ASSUMPTION: The pad check is equivalent to checking '-' at positions 5,11,17,23
    if code[5] != '-' or code[11] != '-' or code[17] != '-' or code[23] != '-':
        return False

    # deHex: parse 5 hex groups of 5 chars each
    key = [0] * 5
    parts = code.split('-')
    if len(parts) != 5:
        return False
    for k, part in enumerate(parts):
        if len(part) != 5:
            return False
        for ch in part:
            if '0' <= ch <= '9':
                key[k] = (key[k] << 4) | (ord(ch) - 48)
            elif 'A' <= ch <= 'F':
                key[k] = (key[k] << 4) | (ord(ch) - 55)
            else:
                return False

    def to_s32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    hash1, hash2, hash3 = hash_name(name)

    # Unpack key values
    # key[4] ^= (key[2] << 20)
    key[4] = to_s32(key[4] ^ to_s32(key[2] << 20))
    # key[0] = -(key[0] ^ (key[1] << 20))
    key[0] = to_s32(-(to_s32(key[0] ^ to_s32(key[1] << 20))))
    # key[1] >>= 12
    key[1] = to_s32(to_s32(key[1]) >> 12)
    # key[2] >>= 12
    key[2] = to_s32(to_s32(key[2]) >> 12)

    if to_s32(key[3] * key[2]) != hash3:
        return False
    if to_s32(to_s32(key[1] - hash2) * key[1]) != to_s32(-hash3):
        return False

    def trunc_div(a, b):
        if b == 0:
            return 0
        return int(a / b)

    if to_s32(trunc_div(to_s32(key[0] + key[4]) * hash2, 2)) != hash1:
        return False
    if to_s32(key[3] + key[2]) != hash2:
        return False
    if to_s32(to_s32(hash2 - 1) * key[1] + key[0]) != key[4]:
        return False

    return True



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
