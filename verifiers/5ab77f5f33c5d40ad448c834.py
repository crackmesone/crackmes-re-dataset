import string

# Characters allowed in serial blocks: digits 0-9 and uppercase A-Z
# That gives base-36 encoding
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def char_to_val(c):
    """Convert a serial character to its base-36 value."""
    c = c.upper()
    if c in string.digits:
        return int(c)
    elif c in string.ascii_uppercase:
        return ord(c) - ord('A') + 10
    else:
        raise ValueError(f'Invalid character: {c}')

def block_to_dword(block):
    """
    Convert a 6-character block to a dword number.
    DW = (((((((((x6*36)+x5)*36)+x4)*36)+x3)*36)+x2)*36)+x1
    where x1 is the first character and x6 is the last.
    Note: The writeup lists x6 down to x1, suggesting x1 is leftmost.
    """
    # The formula from the writeup:
    # DW=(((((((((x6*36)+x5)*36)+x4)*36)+x3)*36)+x2)*36)+x1
    # This processes from x6 to x1 (right to left inner, left to right outer)
    # ASSUMPTION: x1..x6 map to block[0]..block[5] (left to right)
    chars = [char_to_val(c) for c in block]
    # x1=chars[0], x2=chars[1], ..., x6=chars[5]
    x1, x2, x3, x4, x5, x6 = chars[0], chars[1], chars[2], chars[3], chars[4], chars[5]
    dw = ((((((((x6 * 36) + x5) * 36) + x4) * 36) + x3) * 36) + x2) * 36 + x1
    return dw

# ASSUMPTION: The serial has 7 blocks separated by '-', each block is 6 characters.
# The writeup says "xxxxxx-... probably it will 7 blocks"
# The example: PPPP / 200000-200000 only shows 2 blocks (the writeup says it's
# only acceptable for 'this proc' with this name/serial pair).
NUM_BLOCKS = 7
BLOCK_LEN = 6

def apply_block_transform(dw, block_num):
    """
    Apply block_num-dependent SHR/SHL/OR transformations.
    ASSUMPTION: The exact SHR/SHL/OR operations per block are unknown.
    The writeup says 'some block_num dependent SHR SHL OR' but gives no detail.
    We leave this as identity (no-op) since the operations are unspecified.
    """
    # ASSUMPTION: Identity transform - real transforms are unknown
    return dw

def verify(name, serial):
    """
    Verify a name/serial pair.
    Algorithm (from writeup):
    1. Split serial into 7 blocks by '-'
    2. Each block is 6 chars from [0-9A-Z]
    3. Convert each block to a dword via base-36 (x6..x1 formula)
    4. Each dword must be < 0x80000000
    5. Apply block_num-dependent SHR/SHL/OR to each dword
    6. XOR each transformed dword with corresponding NAME chars
    7. Each resulting dword must be divisible by (block_num + 3)
    """
    # Step 1: Split serial
    blocks = serial.upper().split('-')
    if len(blocks) != NUM_BLOCKS:
        return False
    
    for blk in blocks:
        if len(blk) != BLOCK_LEN:
            return False
        for c in blk:
            if c not in ALPHABET:
                return False
    
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    
    for i, blk in enumerate(blocks):
        block_num = i  # 0-indexed
        
        # Step 3: Convert block to dword
        try:
            dw = block_to_dword(blk)
        except ValueError:
            return False
        
        # Step 4: Must be < 0x80000000
        if dw >= 0x80000000:
            return False
        
        # Step 5: Apply SHR/SHL/OR transform
        dw = apply_block_transform(dw, block_num)
        
        # Step 6: XOR with NAME chars
        # ASSUMPTION: XOR each byte of the dword with the corresponding name char
        # cycling through name bytes. Exact XOR method unspecified.
        name_len = len(name_bytes)
        if name_len > 0:
            # ASSUMPTION: XOR the dword with name_bytes[block_num % name_len] as a byte
            xor_val = name_bytes[block_num % name_len]
            dw = dw ^ xor_val
        
        # Step 7: Must be divisible by (block_num + 3)
        divisor = block_num + 3
        if dw % divisor != 0:
            return False
    
    return True

def dword_to_block(dw):
    """
    Convert a dword back to a 6-character block using base-36 encoding.
    Inverse of block_to_dword.
    ASSUMPTION: We reconstruct x1..x6 by successive mod/div of 36.
    """
    chars = []
    val = dw
    for _ in range(BLOCK_LEN):
        chars.append(ALPHABET[val % 36])
        val //= 36
    # chars[0]=x1, chars[1]=x2, ..., chars[5]=x6
    # The formula is (((...x6*36+x5)*36+...)*36+x1)
    # So chars list is [x1,x2,...,x6] and that IS the block left-to-right
    return ''.join(chars)

def keygen(name):
    """
    Generate a valid serial for the given name.
    For each block i:
      - Choose dw such that dw XOR name_xor is divisible by (i+3)
      - dw < 0x80000000
      - dw is representable as a 6-char base-36 block
    """
    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    
    blocks = []
    for i in range(NUM_BLOCKS):
        block_num = i
        divisor = block_num + 3
        
        # ASSUMPTION: XOR with name_bytes[block_num % name_len]
        if len(name_bytes) > 0:
            xor_val = name_bytes[block_num % len(name_bytes)]
        else:
            xor_val = 0
        
        # We need: (dw XOR xor_val) % divisor == 0
        # Find smallest valid dw:
        # Let target = dw XOR xor_val; target % divisor == 0; dw = target XOR xor_val
        # Try target = divisor, 2*divisor, ... until dw < 0x80000000 and dw fits in 6 base36 chars
        max_val = 36**6 - 1  # max value for 6 base-36 chars
        
        found = False
        for multiplier in range(1, 0x80000000 // divisor + 1):
            target = multiplier * divisor
            dw = target ^ xor_val
            if dw < 0x80000000 and dw <= max_val and dw > 0:
                # Verify apply_block_transform is identity (assumption)
                # and block_to_dword(dword_to_block(dw)) == dw
                blk = dword_to_block(dw)
                check_dw = block_to_dword(blk)
                if check_dw == dw:
                    blocks.append(blk)
                    found = True
                    break
        
        if not found:
            # Fallback: use divisor itself as dw (XOR with 0)
            # ASSUMPTION: fallback
            dw = divisor
            blocks.append(dword_to_block(dw))
    
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
