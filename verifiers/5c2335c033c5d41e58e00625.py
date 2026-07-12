import struct

# CRC32 lookup table as shown in the writeup (partial - only first portion shown)
# ASSUMPTION: This is the standard CRC32 lookup table (polynomial 0xEDB88320)
# The writeup shows values matching the standard CRC32 table
def _build_crc32_table():
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

CRC32_TABLE = _build_crc32_table()


def _compute_username_hash(username: str) -> int:
    """
    Implements the hash routine described in the writeup.
    From the pseudocode:
        unsigned long xLong = 0xffffffff;  # ASSUMPTION: writeup says 0xffffff but likely 0xffffffff (CRC32 init)
        unsigned int x = 0xff;
        for i in range(len(username)):
            pos = username[i] ^ x
            code = table[pos] ^ (xLong >> 8)   # ASSUMPTION: xLong>>8 based on shr eax,8 and the pseudocode
            xLong = code >> 8
            x = code & 0xff
        code = ~code & 0xffffffff
    """
    # ASSUMPTION: initial value is 0xffffffff (standard CRC32), writeup pseudocode says 0xffffff which may be a typo
    xLong = 0xFFFFFFFF
    x = 0xFF
    code = xLong

    for ch in username:
        b = ord(ch) if isinstance(ch, str) else ch
        pos = b ^ x
        # ASSUMPTION: the table lookup XORs with xLong (which is code>>8 from previous iteration)
        # From asm: eax = table[pos] ^ ebx, where ebx = eax>>8 from previous step
        # And xLong tracks the full 32-bit value, x tracks lower byte
        code = CRC32_TABLE[pos] ^ xLong
        xLong = code >> 8
        x = code & 0xFF

    code = (~code) & 0xFFFFFFFF
    return code


def _compute_username_hash_v2(username: str) -> int:
    """
    Alternative interpretation closer to the writeup pseudocode literal:
        xLong = 0xffffff, x = 0xff
        pos = user[i] ^ x
        code = table[pos] ^ (0x00000000 + xLong)  <- xLong is code>>8
        xLong = code >> 8
        x = (unsigned char)code
    This is essentially CRC32 with init=0xffffffff.
    """
    # ASSUMPTION: treating as standard CRC32
    crc = 0xFFFFFFFF
    for ch in username:
        b = ord(ch) if isinstance(ch, str) else ch
        crc = CRC32_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return (~crc) & 0xFFFFFFFF


def _build_serial_part1(code: int) -> str:
    """
    Build the 64-character binary string (first part of serial).
    From the writeup loop:
        for i in 0..31:
            pos = 31 - i
            bit_from_code = (code >> pos) & 1
            # pass[i] must satisfy: (pass[i] ^ bit_from_code) & 1 == 0
            # i.e., pass[i] & 1 == bit_from_code
            # pass[i] is '0' (0x30) or '1' (0x31)
            # '0' & 1 = 0, '1' & 1 = 1
            # So pass[i] = '1' if bit is 1, '0' if bit is 0
    The loop says i <= 31 (so 0..31, 32 iterations) but part1 must be 64 chars.
    ASSUMPTION: the loop actually runs 64 times (i <= 63), covering all 64 bits
    or the code is a 64-bit value and the loop runs 64 iterations.
    The writeup says strlen must be 64 and loop runs 31 times - this is inconsistent.
    ASSUMPTION: loop runs 64 times (0..63), pos = 63-i, using 64-bit code.
    """
    # ASSUMPTION: we use 32-bit code but build 32 chars, then pad to 64
    # OR the loop is 0..63 with a 64-bit value
    # Going with 32-bit, 32 chars interpretation first, then pad with zeros to 64
    # ASSUMPTION: first 32 chars encode the hash bits, remaining 32 chars are zeros
    result = []
    for i in range(32):
        pos = 31 - i
        bit = (code >> pos) & 1
        result.append('1' if bit else '0')
    # ASSUMPTION: pad remaining 32 characters with '0' to reach length 64
    result += ['0'] * 32
    return ''.join(result)


def _build_serial_part1_64bit(code: int) -> str:
    """
    ASSUMPTION: loop runs 64 times with 64-bit extended code
    """
    result = []
    for i in range(64):
        pos = 63 - i
        bit = (code >> pos) & 1
        result.append('1' if bit else '0')
    return ''.join(result)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.
    Serial format: <64-char-binary-string>-<unsigned_long>
    The second part after '-' is converted via strtoul - ASSUMPTION: it's the hash value itself
    or some fixed/derived value.
    ASSUMPTION: The second part is the hash value in decimal.
    """
    code = _compute_username_hash_v2(name)
    part1 = _build_serial_part1(code)
    # ASSUMPTION: part2 is the hash value itself (the writeup mentions strtoul on the second part
    # but doesn't clearly state what it should equal)
    part2 = str(code)
    return f"{part1}-{part2}"


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given username.
    """
    if '-' not in serial:
        return False

    # Find the LAST '-' (strrchr behavior)
    last_dash = serial.rfind('-')
    part1 = serial[:last_dash]
    part2_str = serial[last_dash + 1:]

    # Part1 must be exactly 64 characters
    if len(part1) != 64:
        return False

    # Part2 must be parseable as unsigned long
    try:
        part2_val = int(part2_str, 10)  # ASSUMPTION: decimal (strtoul default base or base 10)
    except ValueError:
        return False

    # Compute expected hash from username
    code = _compute_username_hash_v2(name)

    # Check each bit of part1 against corresponding bit of code
    # Loop: for i in 0..31, pos=31-i, check (part1[i] ^ (code>>pos)) & 1 == 0
    for i in range(32):
        pos = 31 - i
        code_bit = (code >> pos) & 1
        # part1[i] should be '0' or '1'
        if i >= len(part1):
            return False
        char_val = ord(part1[i])
        if (char_val ^ code_bit) & 1 != 0:
            return False

    # ASSUMPTION: remaining 32 chars of part1 (indices 32..63) must have LSB = 0
    # i.e., they must be even ASCII values; '0'=0x30 (even), '1'=0x31 (odd)
    # So positions 32..63 must all be '0'
    for i in range(32, 64):
        if (ord(part1[i])) & 1 != 0:
            return False

    # ASSUMPTION: part2 is compared to code value
    # The writeup is truncated so we cannot be sure what part2 is checked against
    # ASSUMPTION: part2 must equal the hash
    if part2_val != code:
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
