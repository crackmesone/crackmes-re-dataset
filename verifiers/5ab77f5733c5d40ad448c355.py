#!/usr/bin/env python3
"""
Keygen for haspor's keygenme 1 V2.1
Based on Stardust's keygen.asm writeup.

The crackme takes an 8-byte hex serial (16 hex chars), computes a checksum,
mixes the serial+checksum bits into a 10-byte 'mixed_code', then encodes it
as 16 base-32 characters (from EncodeTable) separated by '-' every 4 chars.

Serial is the INPUT. The 'code' (output) is derived from the serial.
So verify() checks if code == keygen(serial).
"""

CodeTable1 = [
    0x00, 0x01, 0x03, 0x02, 0x06, 0x07, 0x05, 0x04,
    0x0C, 0x0D, 0x0F, 0x0E, 0x0A, 0x0B, 0x09, 0x08,
    0x08, 0x09, 0x0B, 0x0A, 0x0E, 0x0F, 0x0D, 0x0C,
    0x04, 0x05, 0x07, 0x06, 0x02, 0x03, 0x01, 0x00
]
CodeTable2 = [0x00, 0x0C, 0x08, 0x04]
EncodeTable = "23456789ABCDEFGHJKLMNPQRSTUWVXYZ"


def get_code(number):
    """Implements GetCode proc: returns ax (dl in low byte, dh in high byte)."""
    number = number & 0xFF
    bl = number
    bh = bl
    for _ in range(7):
        # ror bl,1
        bl = ((bl >> 1) | (bl << 7)) & 0xFF
        bh = (bh ^ bl) & 0xFF
    # dl = parity bit (lsb of bh)
    dl = bh & 1

    # Second nibble: CodeTable2[number & 3] << 4
    ah = number & 3
    cl = CodeTable2[ah]
    dl = dl | ((cl << 4) & 0xFF)

    # Third nibble: CodeTable1[(number >> 1) & 0x1F]
    ah2 = (number >> 1) & 0x1F
    dh = CodeTable1[ah2]

    # Fourth nibble: CodeTable1[(number >> 5) & 7] << 4
    al2 = (number >> 5) & 0x7
    cl2 = CodeTable1[al2]
    dh = dh | ((cl2 << 4) & 0xFF)

    # If bit0 of dl is set, xor dh with 0xC0
    if dl & 1:
        dh = (dh ^ 0xC0) & 0xFF

    # returns ax: al=dl, ah=dh
    return dl, dh


def compute_checksum(serial_bytes):
    """Compute 2-byte checksum from 8 serial bytes."""
    dl = 0
    dh = 0
    for b in serial_bytes:
        dl = (dl ^ b) & 0xFF
        al_ret, ah_ret = get_code(dl)
        # mov dl,dh; xor dl,al; mov dh,ah
        dl = (dh ^ b) & 0xFF  # ASSUMPTION: re-reading asm: dl=dh, xor dl,al (al=serial byte)
        # Actually from asm:
        # lodsb          -> al = serial[i]
        # xor dl,al      -> dl ^= al
        # invoke GetCode,dl -> returns ax: al=dl_result, ah=dh_result
        # mov dl,dh      -> dl = dh (old dh)
        # xor dl,al      -> dl ^= al (al still = serial byte)
        # mov dh,ah      -> dh = ah from GetCode
        # Let me redo this properly:
        pass
    # Redo with proper logic:
    dl = 0
    dh = 0
    for b in serial_bytes:
        dl = (dl ^ b) & 0xFF
        ret_al, ret_ah = get_code(dl)
        dl = dh
        dl = (dl ^ b) & 0xFF
        dh = ret_ah
    # checksum[0]=dh, checksum[1]=dl
    return dh, dl


def mix_code(serial_bytes, checksum_hi, checksum_lo):
    """
    MixCode: scrambles 64 serial bits + 16 checksum bits into 80-bit mixed_code.
    The checksum word is: checksum = (checksum_hi << 8) | checksum_lo
    # ASSUMPTION: The bit-interleaving masks (3108904h and 258410C1h) determine
    # exactly which bit positions in mixed_code[0..3] and mixed_code[4..7] come
    # from the checksum vs serial. The last 16 bits (mixed_code[8..9]) hold
    # the serial bits that were displaced by checksum insertion.
    """
    serial_int = int.from_bytes(serial_bytes, 'little')
    serial_lo = serial_int & 0xFFFFFFFF
    serial_hi = (serial_int >> 32) & 0xFFFFFFFF
    checksum_word = (checksum_hi << 8) | checksum_lo

    CHECK_MASK1 = 0x03108904  # bits 0-31 that are checksum positions in mixed_code[0..3]
    CHECK_MASK2 = 0x258410C1  # bits 0-31 that are checksum positions in mixed_code[4..7]

    mixed_lo = 0
    mixed_hi = 0
    mixed_extra = 0  # 16-bit

    esi = 1
    bx = 0x80  # checksum bit pointer (ror each iteration)
    cx = 1     # extra bit pointer (rol each iteration)
    bx = bx & 0xFFFF
    cx = cx & 0xFFFF

    # First 32 iterations (serial_lo / mixed_lo)
    for i in range(32):
        if esi & CHECK_MASK1:  # this bit position is a checksum slot
            if bx & checksum_word:
                mixed_lo |= esi
            if esi & serial_lo:
                mixed_extra |= cx
            # ror bx,1
            bx = ((bx >> 1) | (bx << 15)) & 0xFFFF
            cx = ((cx << 1) | (cx >> 15)) & 0xFFFF
        else:  # normal serial bit
            if esi & serial_lo:
                mixed_lo |= esi
        esi = ((esi << 1) & 0xFFFFFFFF)

    esi = 1
    # Second 32 iterations (serial_hi / mixed_hi)
    for i in range(32):
        if esi & CHECK_MASK2:
            if bx & checksum_word:
                mixed_hi |= esi
            if esi & serial_hi:
                mixed_extra |= cx
            bx = ((bx >> 1) | (bx << 15)) & 0xFFFF
            cx = ((cx << 1) | (cx >> 15)) & 0xFFFF
        else:
            if esi & serial_hi:
                mixed_hi |= esi
        esi = ((esi << 1) & 0xFFFFFFFF)

    # Pack into 10 bytes (little-endian)
    mixed_bytes = (
        list(mixed_lo.to_bytes(4, 'little')) +
        list(mixed_hi.to_bytes(4, 'little')) +
        list(mixed_extra.to_bytes(2, 'little'))
    )
    return mixed_bytes


def encode_string(mixed_bytes):
    """
    EncodeString: read 80 bits (10 bytes), group into 5-bit values,
    map each to EncodeTable char, insert '-' every 4 chars.
    """
    # Read bits from mixed_bytes, LSB first within each byte
    bits = []
    for byte in mixed_bytes:
        for bit in range(8):
            bits.append((byte >> bit) & 1)
    # Group into 16 groups of 5 bits
    chars = []
    for g in range(16):
        val = 0
        for b in range(5):
            val |= bits[g * 5 + b] << b
        chars.append(EncodeTable[val])
    # Insert '-' every 4 chars
    result = ''
    for i, c in enumerate(chars):
        if i > 0 and i % 4 == 0:
            result += '-'
        result += c
    return result


def convert_hex_string(hex_str):
    """Convert 16-char hex string to 8 bytes."""
    if len(hex_str) != 16:
        raise ValueError("Serial must be exactly 16 hex characters")
    hex_str = hex_str.upper()
    for c in hex_str:
        if c not in '0123456789ABCDEF':
            raise ValueError("Serial must use only 0-9 and A-F")
    # Convert pairs to bytes
    return bytes(int(hex_str[i:i+2], 16) for i in range(0, 16, 2))


def keygen(serial_hex):
    """Given a 16-char hex serial, produce the code string."""
    serial_bytes = convert_hex_string(serial_hex)
    cs_hi, cs_lo = compute_checksum(serial_bytes)
    mixed = mix_code(serial_bytes, cs_hi, cs_lo)
    code = encode_string(mixed)
    return code


def verify(serial_hex, code):
    """Verify that code matches the serial."""
    try:
        expected = keygen(serial_hex)
        return expected == code
    except ValueError:
        return False



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
