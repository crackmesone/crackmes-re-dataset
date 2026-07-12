import struct

MASK32 = 0xFFFFFFFF

# ---------------------------------------------------------------------------
# 256-bit hash (sub_4011D0) - the writeup only says 'perform a 256bit hash
# on name'. The exact algorithm is NOT shown in the writeup text.
# ASSUMPTION: We do not know the real hash. We stub it and note the gap.
# ---------------------------------------------------------------------------

def _hash256(name: str) -> bytes:
    """
    ASSUMPTION: The real hash is a custom 256-bit (32-byte) hash implemented
    in sub_4011D0. The writeup does not document its internals.
    This stub returns 32 zero-bytes and will NOT produce valid serials.
    Replace with the real implementation when the binary is available.
    """
    # ASSUMPTION: unknown 256-bit hash algorithm
    raise NotImplementedError(
        "The 256-bit hash sub_4011D0 is not documented in the writeup. "
        "Reverse-engineer the binary to implement this function."
    )


# ---------------------------------------------------------------------------
# 'Play with the ASCII representation of the hash and obtain 4 dwords'
# (seg000:004015A3 --> seg000:00401662)
# ASSUMPTION: The hash bytes are converted to their hex-string ASCII
# representation (64 hex chars) and then the 4 dwords are parsed from
# that string somehow. The exact byte-to-dword mapping is not shown.
# A common approach: treat the hex string as 4 groups of 8 hex chars
# and convert each group to a 32-bit integer.
# ---------------------------------------------------------------------------

def _hash_to_dwords(name: str):
    """
    Returns (d1, d2, d3, d4) derived from the 256-bit name hash.
    ASSUMPTION: hex-string of hash split into 4 x 8-char groups, each
    parsed as a big-endian 32-bit hex value.
    """
    raw = _hash256(name)          # 32 bytes
    hex_str = raw.hex().upper()   # 64 hex chars
    # ASSUMPTION: split into 4 groups of 16 hex chars (= 8 bytes = 64 bits each)?
    # OR 4 groups of 8 hex chars (= 4 bytes = 32 bits each)?
    # The writeup says '4 dwords' (32-bit each) from a 256-bit hash string.
    # ASSUMPTION: 8 hex chars per dword, 4 dwords = 32 hex chars;
    # possibly only the first 32 chars of the 64-char hex string are used,
    # or all 64 chars are rearranged. We use the most natural split.
    # ASSUMPTION: 4 x 8 hex chars taken sequentially from the 64-char string
    d1 = int(hex_str[0:8],  16)
    d2 = int(hex_str[8:16], 16)
    d3 = int(hex_str[16:24],16)
    d4 = int(hex_str[24:32],16)
    return d1, d2, d3, d4


# ---------------------------------------------------------------------------
# Encryption / decryption of part_1
#
# Decryption (what the crackme does to the entered serial part_1):
#   for i in range(32):
#       part_1 = (0x487FD1B3 - part_1 * 0xB7845A5) & MASK32
#
# Encryption (what the keygen does to produce part_1 from the hash dword):
#   for i in range(32):
#       part_1 = ((0x487FD1B3 - part_1) * 0x1551A2D) & MASK32
#
# Correctness check from writeup: 0x1551A2D * 0xB7845A5 == 1 (mod 2^32)
# ---------------------------------------------------------------------------

assert (0x1551A2D * 0xB7845A5) & MASK32 == 1, "Inverse check failed"


def _encrypt_part1(plain: int) -> int:
    """Encrypt (hash dword d1 -> serial part_1)."""
    v = plain & MASK32
    for _ in range(32):
        v = ((0x487FD1B3 - v) * 0x1551A2D) & MASK32
    return v


def _decrypt_part1(cipher: int) -> int:
    """Decrypt (serial part_1 -> hash dword d1). Used for verify."""
    v = cipher & MASK32
    for _ in range(32):
        v = (0x487FD1B3 - v * 0xB7845A5) & MASK32
    return v


# ---------------------------------------------------------------------------
# XOR layers for parts 2, 3, 4  (symmetric: encryption == decryption)
#
# decrypt: part_2 = part_2 xor part_1
#          part_3 = part_3 xor part_2          (note: uses DECRYPTED part_2)
#          part_4 = part_4 xor part_3 xor part_2
#
# The writeup says 'decrypt dword 3 of serial' twice (likely typo for 4).
# For encryption (keygen) XOR is symmetric so same formulas apply.
# ---------------------------------------------------------------------------

def _xor_encrypt(d1, d2, d3, d4):
    """
    Given plain dwords (from hash), produce encrypted serial parts 2,3,4.
    XOR is symmetric so same operation for encrypt/decrypt.
    ASSUMPTION: the order matches the decryption chain exactly.
    """
    p1 = _encrypt_part1(d1)          # part_1 in serial
    p2 = (d2 ^ p1) & MASK32          # part_2
    p3 = (d3 ^ p2) & MASK32          # part_3  (uses encrypted p2? or plain d2?)
    # ASSUMPTION: the XOR chain uses the *serial* (encrypted) values of the
    # previous part, because during decryption the crackme operates on the
    # serial values in order:
    #   dec_p2 = serial_p2 xor serial_p1   => serial_p2 = d2 xor p1
    #   dec_p3 = serial_p3 xor dec_p2      => serial_p3 = d3 xor d2  ... ambiguous
    # Most natural reading: chain uses the *decrypted* previous part.
    # During keygen we work backwards or forwards symmetrically.
    # Re-reading: 'part_2 = part_2 xor part_1'  after decrypting part_1
    # means dec_part2 = serial_part2 XOR dec_part1  => serial_part2 = dec_part2 XOR dec_part1
    # Similarly serial_part3 = d3 XOR d2
    # and serial_part4 = d4 XOR d3 XOR d2
    p3 = (d3 ^ d2) & MASK32
    p4 = (d4 ^ d3 ^ d2) & MASK32
    return p1, p2, p3, p4


def _xor_decrypt(p1_enc, p2_enc, p3_enc, p4_enc):
    """
    Given serial parts, recover plain dwords for comparison.
    """
    d1 = _decrypt_part1(p1_enc)
    # serial_p2 = d2 XOR p1  =>  d2 = serial_p2 XOR p1  (p1 = dec_part1 = d1)
    d2 = (p2_enc ^ d1) & MASK32
    # serial_p3 = d3 XOR d2  =>  d3 = serial_p3 XOR d2
    d3 = (p3_enc ^ d2) & MASK32
    # serial_p4 = d4 XOR d3 XOR d2  =>  d4 = serial_p4 XOR d3 XOR d2
    d4 = (p4_enc ^ d3 ^ d2) & MASK32
    return d1, d2, d3, d4


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Returns serial in the format '%lX-%lX-%lX-%lX'.
    """
    d1, d2, d3, d4 = _hash_to_dwords(name)
    p1, p2, p3, p4 = _xor_encrypt(d1, d2, d3, d4)
    return '{:X}-{:X}-{:X}-{:X}'.format(p1, p2, p3, p4)


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Serial must be in the format 'XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX' (hex).
    """
    parts = serial.strip().split('-')
    if len(parts) != 4:
        return False
    try:
        p1, p2, p3, p4 = [int(x, 16) & MASK32 for x in parts]
    except ValueError:
        return False

    # Decrypt serial back to dwords
    d1_dec, d2_dec, d3_dec, d4_dec = _xor_decrypt(p1, p2, p3, p4)

    # Get expected dwords from name hash
    try:
        d1_exp, d2_exp, d3_exp, d4_exp = _hash_to_dwords(name)
    except NotImplementedError:
        raise

    return (d1_dec == d1_exp and d2_dec == d2_exp and
            d3_dec == d3_exp and d4_dec == d4_exp)



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
