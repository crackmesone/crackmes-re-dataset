import hashlib
import base64
import struct

# ASSUMPTION: The custom checksum (VA 00456220) operating on MD5/SHA1 hash bytes
# is not fully described. We assume it XORs/folds the hash bytes into a fixed-size
# value. The exact operation is unknown - marked below.

# ASSUMPTION: The custom crypto (VA 004560FC) uses name-to-hex conversion to derive
# a key, then encrypts the decoded serial bytes. Since the encryption routine detail
# is not given, we implement a plausible XOR-based scheme as a placeholder.

# ASSUMPTION: Base32 encoding used here is standard RFC 4648 Base32.

def md5_of_name(name: str) -> bytes:
    return hashlib.md5(name.encode('latin-1')).digest()

def sha1_of_name(name: str) -> bytes:
    return hashlib.sha1(name.encode('latin-1')).digest()

def name_to_hex_key(name: str) -> int:
    """Convert name to hex and derive integer key as described in step 11.
    ASSUMPTION: Concatenate hex bytes of name chars, take lower 32 bits of sum.
    The actual ASM instructions on this value are unknown."""
    val = 0
    for ch in name:
        val = (val * 256 + ord(ch)) & 0xFFFFFFFF
    return val

def custom_checksum(hash_bytes: bytes) -> bytes:
    """Custom checksum at VA 00456220.
    ASSUMPTION: Folds hash bytes into 8-byte output by XOR with rotation.
    The real algorithm is not described in the writeup."""
    # ASSUMPTION: Simple fold - XOR pairs of 8 bytes
    out = bytearray(8)
    for i, b in enumerate(hash_bytes):
        out[i % 8] ^= b
    return bytes(out)

def custom_encrypt(data: bytes, key: int) -> bytes:
    """Custom crypto at VA 004560FC.
    ASSUMPTION: XOR each byte with successive bytes derived from the key.
    The real encryption algorithm is not described in detail."""
    result = bytearray()
    k = key
    for b in data:
        k = (k * 0x8088405 + 1) & 0xFFFFFFFF  # ASSUMPTION: LCG key schedule
        result.append(b ^ (k & 0xFF))
    return bytes(result)

def custom_decrypt(data: bytes, key: int) -> bytes:
    """Inverse of custom_encrypt (XOR is self-inverse with same keystream)."""
    return custom_encrypt(data, key)  # XOR is symmetric

def base32_encode(data: bytes) -> str:
    """Standard Base32 encoding."""
    return base64.b32encode(data).decode('ascii')

def base32_decode(s: str) -> bytes:
    """Standard Base32 decoding."""
    # Pad to multiple of 8
    pad = (8 - len(s) % 8) % 8
    return base64.b32decode(s + '=' * pad)

def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    Serial format: BASE32PART1-BASE32PART2
    """
    # Step 1: Check for '-' separator
    if '-' not in serial:
        return False
    
    dash_idx = serial.index('-')
    part1_b32 = serial[:dash_idx]
    part2_b32 = serial[dash_idx+1:]
    
    if not part1_b32 or not part2_b32:
        return False
    
    # Steps 5-6: Base32 decode both parts
    try:
        part1_decoded = base32_decode(part1_b32)
        part2_decoded = base32_decode(part2_b32)
    except Exception:
        return False
    
    # Steps 7-8: Get MD5 and SHA1 of name
    md5_hash = md5_of_name(name)
    sha1_hash = sha1_of_name(name)
    
    # Steps 9-10: Custom checksum of MD5 and SHA1
    chk_md5 = custom_checksum(md5_hash)
    chk_sha1 = custom_checksum(sha1_hash)
    
    # Steps 11-12: Get name-derived key and encrypt decoded serial parts
    key = name_to_hex_key(name)
    enc_part1 = custom_encrypt(part1_decoded, key)
    enc_part2 = custom_encrypt(part2_decoded, key)
    
    # Steps 13-14:
    # Compare SHA1 checksum to encrypted part1
    # Compare MD5 checksum to encrypted part2
    # ASSUMPTION: Comparison is byte-by-byte equality (length must match too)
    if len(enc_part1) != len(chk_sha1):
        # ASSUMPTION: truncate/pad to min length for comparison
        cmp_len = min(len(enc_part1), len(chk_sha1))
        ok1 = enc_part1[:cmp_len] == chk_sha1[:cmp_len]
    else:
        ok1 = enc_part1 == chk_sha1
    
    if len(enc_part2) != len(chk_md5):
        cmp_len = min(len(enc_part2), len(chk_md5))
        ok2 = enc_part2[:cmp_len] == chk_md5[:cmp_len]
    else:
        ok2 = enc_part2 == chk_md5
    
    return ok1 and ok2

def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    
    From the writeup summary:
    - part1 of serial (before '-') comes from SHA1 checksum (2nd checksum)
    - part2 of serial (after '-') comes from MD5 checksum (1st checksum)
    
    Process:
    1. Compute MD5 and SHA1 checksums of name
    2. Apply custom_checksum to each
    3. Decrypt the checksums using the name-derived key
    4. Base32 encode the results
    """
    md5_hash = md5_of_name(name)
    sha1_hash = sha1_of_name(name)
    
    chk_md5 = custom_checksum(md5_hash)
    chk_sha1 = custom_checksum(sha1_hash)
    
    key = name_to_hex_key(name)
    
    # Decrypt to get the pre-encryption values that when encrypted give the checksums
    # Since encrypt is XOR-based (symmetric), decrypt == encrypt
    pre_part1 = custom_decrypt(chk_sha1, key)  # part1 from SHA1 checksum
    pre_part2 = custom_decrypt(chk_md5, key)   # part2 from MD5 checksum
    
    part1_b32 = base32_encode(pre_part1)
    part2_b32 = base32_encode(pre_part2)
    
    # Remove padding '=' for cleaner serial
    part1_b32 = part1_b32.rstrip('=')
    part2_b32 = part2_b32.rstrip('=')
    
    return f"{part1_b32}-{part2_b32}"


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
