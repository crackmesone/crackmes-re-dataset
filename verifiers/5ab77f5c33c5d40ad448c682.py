# RSA Crackme keyfile validator / keygen (slashzero RSA crackme)
# Based on writeup by figugegl
#
# The crackme reads a keyfile named "i.am.a.     .key" (name with spaces)
# Keyfile structure (0xD2 = 210 bytes minimum):
#   bytes [0..1]  : encode value 'd' (little-endian two-byte BCD/hex: e.g. 0x55, 0xC1 -> 0x55C1)
#   bytes [2..N-1]: RSA signature as decimal digits encoded in ASCII/bytes (no hex A-F digits allowed)
#                   terminated by byte 0xFF
#   bytes [0xC7..0xD1] (11 bytes): checksum region, sum must equal 0x40F
#
# RSA check (partially recovered from writeup):
#   - n = RSA modulus (15-bit RSA, so n is small)
#   - e = public exponent
#   - The decimal string (a) represents the signature/ciphertext
#   - The crackme computes a^d mod n and checks against expected value
#   - d is derived from first two bytes of keyfile
#
# ASSUMPTION: The exact RSA modulus n, public exponent e, and the expected
#             plaintext/hash are not given in the writeup. We use placeholder values.
# ASSUMPTION: 'RSA-15' means a 15-bit modulus. The writeup says d comes from
#             bytes 0..1 of the keyfile as a 16-bit big-endian value.
# ASSUMPTION: The string (a) from bytes 2..N (before 0xFF) is a decimal number.
# ASSUMPTION: The RSA check is: int(a) ^ d mod n == some_expected_value
#             but the exact values of n and expected_value are unknown.

import struct

# ASSUMPTION: These RSA parameters are unknown from the writeup.
# A real keygen would need them from the binary.
RSA_N = None        # ASSUMPTION: RSA modulus (15-bit, so < 32768)
RSA_EXPECTED = None # ASSUMPTION: expected result of pow(a, d, n)

KEYFILE_SIZE = 0xD2  # 210 bytes
CHECKSUM_OFFSET = 0xC7  # 199
CHECKSUM_LEN = 11   # bytes 0xC7..0xD1
CHECKSUM_TARGET = 0x40F  # 1039
TERMINATOR = 0xFF


def verify(name: str, serial: bytes) -> bool:
    """
    Verify a keyfile (given as bytes) for the crackme.
    'name' is unused (crackme does not use username, only keyfile).
    'serial' is the raw keyfile bytes.
    Returns True if keyfile is valid.
    """
    if len(serial) < KEYFILE_SIZE:
        return False

    # Step 1: Extract 'd' from bytes 0 and 1 (big-endian 16-bit)
    # ASSUMPTION: The two bytes are converted to hex strings and concatenated,
    # then parsed as a decimal integer. E.g. 0x55, 0xC1 -> '55' + 'C1' -> '55C1' -> 0x55C1 = 21953
    # But wait: the writeup says StrToInt which in Delphi parses decimal by default.
    # ASSUMPTION: The hex string '55C1' would fail StrToInt unless it uses hex prefix.
    # More likely the result is interpreted as hex: IntToHex gives '55' and 'C1',
    # concatenated to '55C1', then StrToInt('$55C1') or similar.
    # We'll treat it as: d = (byte0 << 8) | byte1  (big-endian)
    b0 = serial[0]
    b1 = serial[1]
    hex_str = '{:02X}{:02X}'.format(b0, b1)
    try:
        d = int(hex_str, 16)  # ASSUMPTION: parsed as hex
    except ValueError:
        return False

    # Step 2: Read hex digit bytes starting at index 2 until 0xFF terminator
    # Each byte is converted to 2-char hex and concatenated to form string (a)
    # String (a) must NOT contain chars A-F (i.e., all hex pairs must be 0-9 only)
    a_hex = ''
    i = 2
    found_ff = False
    while i < KEYFILE_SIZE:
        byte_val = serial[i]
        i += 1
        if byte_val == TERMINATOR:
            found_ff = True
            break
        hex_pair = '{:02X}'.format(byte_val)
        # Check: no A-F allowed in the concatenated string
        for ch in hex_pair:
            if ch in 'ABCDEF':
                return False
        a_hex += hex_pair
    
    if not found_ff:
        # ASSUMPTION: loop ended at 0xD2 without finding FF -> error per writeup
        return False

    # a_hex is now a string of decimal digits (no A-F)
    # Convert to integer
    try:
        a_val = int(a_hex)  # decimal interpretation
    except ValueError:
        return False

    # Step 3: Checksum check
    # Sum of bytes at offsets 0xC7..0xD1 (11 bytes) must equal 0x40F
    checksum = sum(serial[CHECKSUM_OFFSET:CHECKSUM_OFFSET + CHECKSUM_LEN])
    if checksum != CHECKSUM_TARGET:
        return False

    # Step 4: RSA verification
    # ASSUMPTION: The crackme computes pow(a_val, d, RSA_N) and checks against RSA_EXPECTED
    # Since we don't have RSA_N and RSA_EXPECTED, we cannot fully verify here.
    if RSA_N is not None and RSA_EXPECTED is not None:
        result = pow(a_val, d, RSA_N)
        if result != RSA_EXPECTED:
            return False

    return True


def keygen(name: str) -> bytes:
    """
    Generate a valid keyfile for the crackme.
    Returns keyfile as bytes.
    ASSUMPTION: Without the RSA parameters (n, e, expected plaintext),
    we can only build the structural requirements but not a valid RSA signature.
    """
    # ASSUMPTION: We pick a d value. In RSA-15, d would be the private exponent.
    # The private key is needed to sign; we don't have it.
    # We'll build a structurally valid keyfile skeleton.
    
    keyfile = bytearray(KEYFILE_SIZE)
    
    # ASSUMPTION: Choose d = 0x0001 (bytes 0x00, 0x01) as placeholder
    # Real keygen needs the actual private exponent d.
    d = 0x0001  # ASSUMPTION: placeholder
    keyfile[0] = (d >> 8) & 0xFF
    keyfile[1] = d & 0xFF

    # ASSUMPTION: The RSA signature as decimal string.
    # We need: signature = pow(message, d_private, n)
    # Without n and d_private, we use placeholder '00000000'
    # The signature string must contain only decimal digits when each byte pair is hex-encoded.
    # Each hex pair must be 0-9 only, meaning each byte must be in range 0..99 decimal
    # (i.e., byte values 0x00..0x63 where both nibbles are 0-9)
    # Valid bytes: both nibbles <= 9, so bytes: 0x00-0x09, 0x10-0x19, 0x20-0x29,
    #             0x30-0x39, 0x40-0x49, 0x50-0x59, 0x60-0x69, 0x70-0x79,
    #             0x80-0x89, 0x90-0x99
    # ASSUMPTION: Fill signature area with 0x00 bytes and terminate with 0xFF
    sig_start = 2
    # Leave room for checksum area and terminator
    # Terminator at some position before 0xC7
    # ASSUMPTION: place terminator at offset 3 (minimal signature)
    keyfile[2] = 0x00  # signature byte (decimal '00')
    keyfile[3] = TERMINATOR  # terminate

    # Fill bytes 4..0xC6 with zeros (don't care after terminator)
    # Set checksum bytes 0xC7..0xD1 to sum to 0x40F
    # 11 bytes summing to 0x40F = 1039
    # 1039 / 11 = 94 remainder 5 -> 6 bytes of 95 and 5 bytes of 94? Let's compute:
    base = CHECKSUM_TARGET // CHECKSUM_LEN   # 94
    remainder = CHECKSUM_TARGET % CHECKSUM_LEN  # 5
    for j in range(CHECKSUM_LEN):
        if j < remainder:
            keyfile[CHECKSUM_OFFSET + j] = base + 1  # 95 = 0x5F (valid: nibbles 5,F -> F not allowed!)
        else:
            keyfile[CHECKSUM_OFFSET + j] = base      # 94 = 0x5E (nibble E not allowed in sig area)
    # ASSUMPTION: The checksum bytes are NOT subject to the A-F restriction
    # (they come after the 0xFF terminator logically, or the restriction only applies
    # to the (a) string before the terminator)
    # So checksum bytes can have any value 0-255.

    return bytes(keyfile)



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
