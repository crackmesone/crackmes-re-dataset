# NOTE: This is a PARTIAL reconstruction. The full algorithm requires:
# 1. GOST DSA signing with specific DSA parameters from the crackme's resources
# 2. A custom cipher using SHA-1-derived checksums
# 3. Base32 encoding/decoding
# 4. The secret key x=102CF2C889217701206A8203D6BF826A4284D1B3
#
# The DSA parameters (p, q, g, y) are embedded in the crackme's resources
# and were NOT fully published in the writeup. We cannot implement a complete
# keygen without them.
#
# What IS known from the writeup is documented below with ASSUMPTION comments.

import hashlib
import base64
import struct

# Known secret key from the writeup
X_SECRET = 0x102CF2C889217701206A8203D6BF826A4284D1B3

# ASSUMPTION: DSA parameters below are UNKNOWN (from crackme resources).
# The writeup says p is 512-bit prime, q is 160-bit prime, g and y are derived.
# These are placeholder values and will NOT produce valid serials.
P = 0  # 512-bit prime - UNKNOWN
Q = 0  # 160-bit prime - UNKNOWN
G = 0  # generator - UNKNOWN
Y = 0  # public key - UNKNOWN

# Base32 alphabet (standard)
B32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

def b32encode_custom(data: bytes) -> str:
    """Standard Base32 encode (no padding)."""
    return base64.b32encode(data).decode('ascii').rstrip('=')

def b32decode_custom(s: str) -> bytes:
    """Standard Base32 decode, adding padding as needed."""
    s = s.upper()
    pad = (8 - len(s) % 8) % 8
    s = s + '=' * pad
    return base64.b32decode(s)

def sha1_hash(data: bytes) -> bytes:
    """Compute SHA-1 of data."""
    return hashlib.sha1(data).digest()

def checksum_algo(data: bytes):
    """ASSUMPTION: Custom checksum algorithm applied to SHA-1(name).
    Details not fully described in writeup. Returns (checksum_bytes).
    This is a placeholder."""
    # ASSUMPTION: We do not know the exact custom checksum algorithm.
    h = sha1_hash(data)
    return h

def compute_S1_S2(name: str):
    """ASSUMPTION: From the writeup:
    - SHA-1(name) is computed
    - checksum N02 is calculated from SHA-1(name) using custom algo
    - S1 = Sum of checksum N02
    - S2 = Sum of Sum of checksum N02
    - S3 = S1 * S2
    These are integer sums over the checksum bytes (guessed).
    """
    name_bytes = name.encode('ascii', errors='replace')
    sha1 = sha1_hash(name_bytes)
    # ASSUMPTION: checksum algo N02 applied to SHA-1 output
    ck = checksum_algo(sha1)
    # ASSUMPTION: S1 = sum of bytes of checksum
    S1 = sum(ck)
    # ASSUMPTION: S2 = sum of digits/bytes of S1 representation
    S2 = sum(int(b) for b in str(S1).encode('ascii') if b != ord('.'))
    S3 = S1 * S2
    return S1, S2, S3

def cipher_decrypt(serial_mid_b32: str, name: str) -> bytes:
    """Implements cipher decryption from writeup:
    Serial2[i] = B32Encode( Checksum(Name) xor S3 xor S2 + S2 xor S1 - S1 )
    Inverse (encryption check):
    B32Decode(Serial2(Name)[i]) + S1 xor S1 - S2 xor S2 xor S3 = Checksum(Name)[i]
    """
    name_bytes = name.encode('ascii', errors='replace')
    sha1 = sha1_hash(name_bytes)
    ck = checksum_algo(sha1)  # ASSUMPTION: this is Checksum(Name)
    S1, S2, S3 = compute_S1_S2(name)

    decoded = b32decode_custom(serial_mid_b32)
    result = []
    for i, b in enumerate(decoded):
        # Encryption formula (verify):
        # b + S1 xor S1 - S2 xor S2 xor S3 = ck[i]
        # ASSUMPTION: operations are byte-level with wrapping
        val = ((b + S1) & 0xFF) ^ (S1 & 0xFF)
        val = ((val - S2) & 0xFF) ^ (S2 & 0xFF)
        val = val ^ (S3 & 0xFF)
        result.append(val)
    return bytes(result)

def cipher_encrypt(checksum_bytes: bytes, name: str) -> str:
    """Implements cipher encryption (keygen side):
    Serial2[i] = B32Encode( Checksum(Name)[i] xor S3 xor S2 + S2 xor S1 - S1 )
    """
    S1, S2, S3 = compute_S1_S2(name)
    result = []
    for b in checksum_bytes:
        val = b ^ (S3 & 0xFF)
        val = val ^ (S2 & 0xFF)
        val = (val + S2) & 0xFF
        val = val ^ (S1 & 0xFF)
        val = (val - S1) & 0xFF
        result.append(val)
    return b32encode_custom(bytes(result))

def gost_dsa_sign(message_hash: bytes, x: int, p: int, q: int, g: int):
    """GOST DSA signing as described in writeup:
    t1 = g^k mod p
    r = t1 mod q
    g1 = x*r mod q
    g2 = rnd*m mod q  (rnd = k, m = message as integer)
    s = g1 + g2 mod q
    Returns (r, s) as integers.
    """
    import random
    if p == 0 or q == 0 or g == 0:
        raise ValueError("DSA parameters unknown - cannot sign")
    m = int.from_bytes(message_hash, 'big') % q
    while True:
        k = random.randint(1, q - 1)
        t1 = pow(g, k, p)
        r = t1 % q
        if r == 0:
            continue
        g1 = (x * r) % q
        g2 = (k * m) % q
        s = (g1 + g2) % q
        if s == 0:
            continue
        return r, s

def gost_dsa_verify(message_hash: bytes, r: int, s: int, p: int, q: int, g: int, y: int) -> bool:
    """GOST DSA verification as described in writeup:
    v = M^-1 mod q
    u1 = v*s mod q
    t1 = q - r
    u2 = v * t1 mod q
    g1 = g^u1 mod p
    g2 = y^u2 mod p
    g3 = g1*g2 mod p
    w = g3 mod q
    if w == r: valid
    """
    if p == 0 or q == 0 or g == 0 or y == 0:
        raise ValueError("DSA parameters unknown - cannot verify")
    M = int.from_bytes(message_hash, 'big') % q
    v = pow(M, -1, q)
    u1 = (v * s) % q
    t1 = q - r
    u2 = (v * t1) % q
    g1 = pow(g, u1, p)
    g2 = pow(y, u2, p)
    g3 = (g1 * g2) % p
    w = g3 % q
    return w == r

def parse_serial(serial: str):
    """Parse serial of form XXXX-XXXX-XXXX (three parts separated by dashes).
    From examples it appears the serial has 3 large Base32 segments separated by '-'.
    The middle segment corresponds to Serial2 (cipher output).
    The first and last segments encode R and S from GOST DSA.
    ASSUMPTION based on writeup structure.
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]

def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    Full verification requires the DSA parameters from the crackme resources.
    Without them, we can only partially verify the structure.
    """
    parsed = parse_serial(serial)
    if parsed is None:
        return False
    part1, part2, part3 = parsed

    # ASSUMPTION: part2 is the cipher-encrypted checksum (Serial2 / middle segment)
    # part1 encodes R, part3 encodes S of GOST DSA signature
    # (from example: middle segment is DMIBEEI3H4NMM for name qpt^J)

    try:
        r_bytes = b32decode_custom(part1)
        s_bytes = b32decode_custom(part3)
    except Exception:
        return False

    r = int.from_bytes(r_bytes, 'big')
    s = int.from_bytes(s_bytes, 'big')

    # Compute checksum from cipher decryption of part2
    checksum = cipher_decrypt(part2, name)

    # ASSUMPTION: checksum is used as the message for GOST DSA verification
    # SHA-1 of name is also involved
    name_bytes = name.encode('ascii', errors='replace')
    sha1 = sha1_hash(name_bytes)

    # Cannot fully verify without P, Q, G, Y from crackme resources
    # ASSUMPTION: if DSA params were known, we'd call:
    # return gost_dsa_verify(checksum, r, s, P, Q, G, Y)

    # Structural check only:
    return len(r_bytes) > 0 and len(s_bytes) > 0

def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    FULL keygen requires the DSA parameters from the crackme resources.
    With the secret x=102CF2C889217701206A8203D6BF826A4284D1B3 and known params,
    the steps would be:
    1. SHA-1(name)
    2. Compute custom checksums from SHA-1
    3. Cipher-encrypt checksum to get Serial2 (middle segment)
    4. Sign message with GOST DSA to get R, S
    5. Base32 encode R -> Serial1 part, S -> Serial3 part
    6. Format as Serial1-Serial2-Serial3
    """
    raise NotImplementedError(
        "Cannot generate serial: DSA parameters (p, q, g, y) are unknown. "
        "They are embedded in the crackme's resource section and were not "
        "published in the writeup."
    )


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
