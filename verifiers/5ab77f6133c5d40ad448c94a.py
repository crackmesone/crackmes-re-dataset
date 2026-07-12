def _mod_buffer(name: str) -> list:
    """
    Build the 8-byte mod_buffer from the name:
    1. Copy first 8 bytes of name into mod_buffer.
    2. For each remaining character (index 8 onward), XOR mod_buffer[index & 7] with that character.
    """
    name_bytes = [ord(c) for c in name]
    mod = list(name_bytes[:8])  # first 8 characters
    # name must be at least 8 chars; loop starts at index 8 (9th char, 0-indexed)
    for i in range(8, len(name_bytes)):
        mod[i & 7] ^= name_bytes[i]
    return mod


def _hex_pairs_to_key_buffer(serial: str) -> list:
    """
    Convert the first 4 blocks of the serial (xxxx-xxxx-xxxx-xxxx) into 8 hex bytes.
    Non-hex characters (anything not 0-9, A-F, a-f) are treated as 0.
    Each block contributes 2 bytes: the block string is treated as two hex digits.
    ex: '1234' -> 0x12, 0x34
    """
    blocks = serial.split('-')
    key = []
    for block in blocks[:4]:
        # Each block is 4 hex chars => 2 bytes
        # Pair them: chars 0-1 form byte1, chars 2-3 form byte2
        for j in range(0, 4, 2):
            hi_char = block[j]   if j < len(block) else '0'
            lo_char = block[j+1] if j+1 < len(block) else '0'
            def hex_val(c):
                if '0' <= c <= '9':
                    return int(c, 16)
                if c in 'ABCDEFabcdef':
                    return int(c, 16)
                # ASSUMPTION: non-hex letters (other than A-F) are treated as 0
                return 0
            byte = (hex_val(hi_char) << 4) | hex_val(lo_char)
            key.append(byte)
    return key


CONST_BUFFER = [0x47, 0x56, 0x46, 0x40, 0x54, 0x44, 0x0C, 0x0C]
TORRES_BUFFER = [0x74, 0x6F, 0x72, 0x72, 0x65, 0x73, 0x34, 0x35]  # 'torres45'


def verify(name: str, serial: str) -> bool:
    """
    Validate name + serial according to mt3o's crackme algorithm.
    """
    # Name must be > 7 characters (at least 8)
    if len(name) <= 7:
        return False

    # Serial layout must be xxxx-xxxx-xxxx-xxxx-xxxx (exactly 24 chars)
    parts = serial.split('-')
    if len(parts) != 5:
        return False
    for p in parts:
        if len(p) != 4:
            return False

    # Build mod_buffer from name
    mod = _mod_buffer(name)

    # Build key_buffer from first 4 serial blocks
    key = _hex_pairs_to_key_buffer(serial)
    if len(key) != 8:
        return False

    # Checksum: sum of all key_buffer bytes must equal the numeric value
    # encoded in the last block of the serial.
    # The first character of the last block is ignored; remaining 3 chars form a hex number.
    last_block = parts[4]
    # ASSUMPTION: last 3 chars of last block represent the checksum as a 3-digit hex number
    try:
        checksum_in_serial = int(last_block[1:], 16)
    except ValueError:
        return False
    computed_checksum = sum(key) & 0xFFFF
    if computed_checksum != checksum_in_serial:
        return False

    # XOR all three buffers column-wise
    xor_buffer = [mod[i] ^ key[i] ^ CONST_BUFFER[i] for i in range(8)]

    # Each byte of xor_buffer is XORed with a constant and compared to a constant.
    # From the writeup: xor_buffer must equal torres_buffer.
    return xor_buffer == TORRES_BUFFER


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be longer than 7 characters.
    """
    if len(name) <= 7:
        raise ValueError('Name must be longer than 7 characters')

    mod = _mod_buffer(name)

    # key_buffer = torres_buffer XOR const_buffer XOR mod_buffer
    key = [TORRES_BUFFER[i] ^ CONST_BUFFER[i] ^ mod[i] for i in range(8)]

    # Convert key_buffer to 4 serial blocks (each byte -> 2 hex digits, uppercase)
    blocks = []
    for i in range(0, 8, 2):
        block = '{:02X}{:02X}'.format(key[i], key[i+1])
        blocks.append(block)

    # Compute checksum: sum of all 8 key bytes
    checksum = sum(key) & 0xFFFF
    # Last block: first char is arbitrary (use '0'), then 3 hex digits for checksum
    last_block = '0{:03X}'.format(checksum)
    blocks.append(last_block)

    return '-'.join(blocks)



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
