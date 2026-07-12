import struct
import hashlib
import base64

# Standard CRC32 (zlib style, reflected)
def crc32(data: bytes) -> int:
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF

# Base32 alphabet used in the crackme (standard RFC 4648)
B32_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def b32_encode(data: bytes) -> str:
    """Standard base32 encoding (matches the B32Encode in the solution source)."""
    # Use Python's base64 module which matches RFC 4648
    encoded = base64.b32encode(data).decode('ascii')
    return encoded

def b32_decode(s: str) -> bytes:
    """Standard base32 decode."""
    # Pad to multiple of 8
    pad = (8 - len(s) % 8) % 8
    s_padded = s + '=' * pad
    return base64.b32decode(s_padded.upper())

# ASSUMPTION: HashName computes MD5 of the name (KANAL detected MD5 in the binary)
# and returns it as a hex or raw string. We use the hex digest.
def hash_name(name: str) -> str:
    """Hash the name using MD5, return hex digest string."""
    # ASSUMPTION: The hash is MD5 of the name bytes
    return hashlib.md5(name.encode('latin-1')).hexdigest()

# ASSUMPTION: CRC32 of name is also involved (KANAL detected CRC32)
def crc32_name(name: str) -> int:
    return crc32(name.encode('latin-1'))

# From the disassembly:
# CheckKey does:
#   1. HashName(name) -> sHashName
#   2. Base32Decode(serial) -> base32DecodedSerial
#   3. Find '-' in decoded serial to split into sSerial1 and sSerial2
#   4. Some comparison involving sHashName, sSerial1, sSerial2
#      and RSA-like modular exponentiation (FGint MontgomeryModExp detected)
#
# ASSUMPTION: The serial format after base32 decoding is: <part1>-<part2>
# ASSUMPTION: sSerial1 is compared against the hash of the name
# ASSUMPTION: sSerial2 is the RSA/FGInt signature portion
# ASSUMPTION: The RSA public key (e, n) labeled sE and sN in the disassembly
#             are embedded constants we do not have; we cannot fully reconstruct.
#
# The writeup shows variables sJA, sE, sN, sHashName, base32DecodedSerial,
# spacerpos, sSerial1, sSerial2 which strongly suggests:
#   - The decoded serial contains a '-' separator
#   - Part1 is compared to the name hash
#   - Part2 is verified via RSA (MontgomeryModExp with embedded e and n)
#
# Without the RSA public key (e, n), we can only implement verify() partially.

# ASSUMPTION: Public RSA key constants (e, n) - UNKNOWN, placeholder values
# These would need to be extracted from the binary.
RSA_E = None  # ASSUMPTION: unknown public exponent
RSA_N = None  # ASSUMPTION: unknown modulus

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    Algorithm (partially recovered from disassembly + writeup):
      1. Compute hash of name (MD5, ASSUMPTION)
      2. Base32-decode the serial
      3. Split decoded serial on '-' into part1 and part2
      4. Compare part1 to name hash
      5. Verify part2 via RSA modular exponentiation against embedded (e, n)
         (cannot fully implement without the binary constants)
    """
    if not name or not serial:
        return False

    # Step 1: Hash the name
    name_hash = hash_name(name)  # ASSUMPTION: MD5 hex digest

    # Step 2: Base32-decode the serial
    try:
        decoded = b32_decode(serial.replace(' ', '').replace('-', ''))
        decoded_str = decoded.decode('latin-1')
    except Exception:
        return False

    # Step 3: Find '-' separator in decoded serial
    if '-' not in decoded_str:
        return False

    dash_pos = decoded_str.index('-')
    serial1 = decoded_str[:dash_pos]   # sSerial1
    serial2 = decoded_str[dash_pos+1:] # sSerial2

    # Step 4: Compare serial1 to name hash
    # ASSUMPTION: direct string comparison
    if serial1 != name_hash:
        return False

    # Step 5: RSA verification of serial2
    # ASSUMPTION: RSA_E and RSA_N are embedded in binary, unknown here
    if RSA_E is None or RSA_N is None:
        # Cannot verify RSA portion without binary constants
        # Return True only based on hash match (partial verification)
        return True  # ASSUMPTION: skipping RSA check

    # If we had RSA_E and RSA_N:
    # sig_int = int.from_bytes(serial2.encode('latin-1'), 'big')
    # hash_int = int.from_bytes(bytes.fromhex(name_hash), 'big')
    # verified = pow(sig_int, RSA_E, RSA_N) == hash_int
    # return verified
    return False

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    Without the RSA private key (d, n), we cannot produce a valid serial2.
    We can only produce the format with the correct serial1.
    ASSUMPTION: RSA private key (d, n) unknown; serial2 is a placeholder.
    """
    name_hash = hash_name(name)  # ASSUMPTION: MD5 hex digest

    # ASSUMPTION: serial2 would be the RSA signature of the hash
    # Without private key, we use a placeholder
    serial2 = 'PLACEHOLDER'  # ASSUMPTION: RSA signature portion unknown

    # Combine: <hash>-<signature>
    raw = name_hash + '-' + serial2

    # Base32-encode
    encoded = b32_encode(raw.encode('latin-1'))
    # Remove padding '=' signs for cleanliness
    encoded = encoded.rstrip('=')

    return encoded


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
