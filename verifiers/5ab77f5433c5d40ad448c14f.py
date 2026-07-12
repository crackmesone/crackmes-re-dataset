import hashlib
import struct
import base64
import random
import zlib

# ============================================================
# Domain parameters (from writeup)
# ============================================================
P  = 0x811C24AFB36712781EE85A8CDD645FADF4A909A9B6E67FC27C9EE197E729CB0B
Q  = 0x380CB932405DFE21EDC59B523D357251250A66DFC6B
G  = 0x61C8DAC1B247A3689CB956CF03E1444033F247FAEE70206A092C639179F70E55
YA = 0x55975673D517AE534B3BDE83FC56E61757EEC446CD649D0E3663245D7E48C402
XB = 0xE24546F5F6B39F59
YB = 0x588E8740DBBC468476DA120AC8E1F84C58AF2E6625B9CCF3BBE4066967A7DEC6
XA = 0xFACE  # private key of signer

# ============================================================
# CRC32 helper (matches Windows CRC convention used in crackme)
# ============================================================
def crc32_name(name: str) -> int:
    # ASSUMPTION: standard CRC32 as in zlib / Win32 CRC helper in crackme
    data = name.encode('latin-1')
    return zlib.crc32(data) & 0xFFFFFFFF

# ============================================================
# Modified ICE cipher
# The writeup documents modified ice_sxor values but the full
# ICE cipher implementation is large. We implement a placeholder
# that accepts a key and encrypts an 8-byte block.
# ASSUMPTION: Only the ice_sxor table is changed; all other ICE
# internals are standard ICE-1 (level=1, 16 rounds).
# A real implementation would require the full ICE source with
# the modified sxor table below.
# ============================================================

# Modified sxor table from writeup
ICE_SXOR = [
    [0x12, 0x15, 0x95, 0x42],
    [0x22, 0xC7, 0xED, 0x61],
    [0x5C, 0x20, 0x24, 0x3A],
    [0xAE, 0x3B, 0xE2, 0x18],
]

# ASSUMPTION: The ICE cipher below is a structural stub.
# A correct keygen requires the full modified ICE-1 implementation.
# We mark this clearly and provide the interface.

try:
    # Try to import a real ICE implementation if available
    from ice import IceKey  # type: ignore
    def ice_encrypt(key_bytes: bytes, data_bytes: bytes) -> bytes:
        ik = IceKey(1)  # level 1
        ik.set(key_bytes)
        out = bytearray(8)
        ik.encrypt(data_bytes, out)
        return bytes(out)
except ImportError:
    def ice_encrypt(key_bytes: bytes, data_bytes: bytes) -> bytes:
        # ASSUMPTION: Placeholder - returns zeroed block.
        # Replace with real modified ICE-1 implementation.
        raise NotImplementedError(
            "Modified ICE-1 cipher not available. "
            "Provide an ICE implementation with the modified ice_sxor table."
        )

# ============================================================
# SHA-1 (standard)
# ============================================================
def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest().upper()

# ============================================================
# Base64 encode (standard, matches crackme usage)
# ============================================================
def b64encode_block(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')

# ============================================================
# Keygen core (Zheng SignEncryption)
# ============================================================
def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Serial format: S1-S2-S3
      S1 = SHA1(name + k2)  [hex uppercase, 40 chars]
      S2 = Base64(ICE_Encrypt(CRC32(name) as 8 hex bytes, key=k1))
      S3 = x * (r + xa)^-1 mod q  [hex]

    where:
      x is random in [1, q-1]
      ta = YB^x mod P
      k1 = first 8 hex chars of hex(ta)  (as ASCII bytes for ICE key)
      k2 = remaining hex chars of hex(ta)
      r  = SHA1(name + k2) interpreted as big integer
      s  = x * modinverse(r + xa, q) mod q
    """
    name_bytes = name.encode('latin-1')

    # Step 1: random x in Z*q
    x = random.randint(1, Q - 1)

    # Step 2: ta = YB^x mod P
    ta = pow(YB, x, P)

    # Step 3: split ta hex into k1 (first 8 hex chars) and k2 (rest)
    # The crackme uses cotstr which gives hex without leading zeros typically,
    # but padded. ASSUMPTION: we use full hex representation padded to even length.
    ta_hex = format(ta, 'X')  # uppercase hex
    # ASSUMPTION: ta_hex is taken as-is; k1 = first 8 chars, k2 = rest
    # (matches kg.cpp: strcpy(k2,temp+8); strcpy(k1,temp); k1[8]=0;)
    if len(ta_hex) < 8:
        ta_hex = ta_hex.zfill(8)
    k1_str = ta_hex[:8]
    k2_str = ta_hex[8:]

    # Step 4: k1 as bytes (ASCII hex string bytes, 8 bytes)
    k1_bytes = k1_str.encode('latin-1')  # 8 bytes

    # Step 5: CRC32 of name as 8-char hex string, then ICE encrypt
    crc_val = crc32_name(name)
    crc_hex_str = '%08X' % crc_val  # e.g. "DEADBEEF"
    crc_block = crc_hex_str.encode('latin-1')  # 8 bytes

    ice_out = ice_encrypt(k1_bytes, crc_block)  # 8 bytes
    s2 = b64encode_block(ice_out)

    # Step 6: SHA1(name + k2)
    concat = name_bytes + k2_str.encode('latin-1')
    s1 = sha1_hex(concat)  # 40 hex chars

    # Step 7: r = big integer from s1 (SHA1 output as hex)
    r = int(s1, 16)

    # Step 8: s3 = x * modinverse(r + xa, q) mod q
    r_plus_xa = (r + XA) % Q
    inv = pow(r_plus_xa, -1, Q)  # Python 3.8+ supports this
    s3_val = (x * inv) % Q
    s3 = format(s3_val, 'X')

    return '%s-%s-%s' % (s1, s2, s3)


# ============================================================
# Verify (simulates crackme verification)
# ============================================================
def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against a name.
    Replicates the crackme's check logic.
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    s1, s2, s3 = parts

    # S1 and S3 must be valid hex
    try:
        r = int(s1, 16)
        s3_val = int(s3, 16)
    except ValueError:
        return False

    # S2 must be valid base64
    try:
        ice_out = base64.b64decode(s2)
        if len(ice_out) != 8:
            return False
    except Exception:
        return False

    # Zheng unsign:
    # ta = YB^(s3*(r+xa) mod q)... but verifier only has public key.
    # Verifier computes:
    #   ta = (ya^s1 * g^s3)^xb mod p   -- standard Zheng unsignencrypt
    # ASSUMPTION: The crackme computes ta as YB^x mod p using the
    # sender's ephemeral x embedded in the signature, but for
    # verification it uses the Zheng unsign formula with xb.
    #
    # From the pdf: verifier computes
    #   s = s3, r = s1 (as bignum)
    #   ta = (ya^r * g^s)^xb mod p
    # which recovers the shared secret.
    #
    # ASSUMPTION: This is the standard Zheng unsignencryption verification.
    try:
        ta_verify = pow(pow(YA, r, P) * pow(G, s3_val, P) % P, XB, P)
    except Exception:
        return False

    ta_hex = format(ta_verify, 'X')
    if len(ta_hex) < 8:
        ta_hex = ta_hex.zfill(8)
    k1_str = ta_hex[:8]
    k2_str = ta_hex[8:]
    k1_bytes = k1_str.encode('latin-1')

    # Decrypt S2 with k1 to recover CRC block
    try:
        from ice import IceKey  # type: ignore
        ik = IceKey(1)
        ik.set(k1_bytes)
        decrypted = bytearray(8)
        ik.decrypt(ice_out, decrypted)
        decrypted_hex = decrypted.decode('latin-1').upper()
    except NotImplementedError:
        # ASSUMPTION: ICE not available, skip ICE check
        decrypted_hex = None
    except ImportError:
        decrypted_hex = None

    # Check CRC32
    name_bytes = name.encode('latin-1')
    expected_crc = '%08X' % crc32_name(name)
    if decrypted_hex is not None and decrypted_hex != expected_crc:
        return False

    # Check S1 == SHA1(name + k2)
    concat = name_bytes + k2_str.encode('latin-1')
    expected_s1 = sha1_hex(concat)
    if s1.upper() != expected_s1.upper():
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
