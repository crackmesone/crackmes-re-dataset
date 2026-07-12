import struct
import hashlib

# ============================================================
# PARTIAL RECOVERY of thigo keygenme2
# Based on the writeup by crisiscracker
# ============================================================
#
# Summary of the algorithm (from writeup):
#  1. Hash the name using a modified MD5 (custom init constants,
#     some constants/functions changed). The result is 16 bytes.
#  2. The first 16 chars of the serial are converted from hex string
#     to a bignum (MIRACL library, base 16), then exported as raw bytes.
#  3. A Blowfish cipher is initialized with the 16-byte hash as the key.
#  4. The 8 bytes (2 DWORDs) from step 2 are Blowfish-decrypted.
#  5. The decrypted bytes must spell 'Thig' + 'h' (first char 'T',
#     second char 'h'/'i'/'g', fourth char 'h', fifth char 'h').
#     The writeup says 4 first chars = 'Thig', 5th = 'h'.
#  6. The remaining part of the serial (chars 17..20+) is used in
#     additional checks (truncated writeup, unknown).
#
# ASSUMPTION: The modified MD5 uses init constants:
#   A=0x1324AD68, B=0x98765478, C=0xFDA85EC9, D=0x9645687A
#   Some internal MD5 constants/round functions may also be altered.
#   We cannot fully recover those changes from the writeup alone,
#   so we approximate using standard MD5 round structure with
#   only the init vector changed.
#
# ASSUMPTION: The Blowfish implementation is standard.
#
# ASSUMPTION: Serial chars 17+ are not fully described; we set them
#   to a placeholder.
# ============================================================

try:
    from Crypto.Cipher import Blowfish
    HAS_BLOWFISH = True
except ImportError:
    HAS_BLOWFISH = False

import struct

# --- Modified MD5 ---
# Standard MD5 per-round constants (T table)
import math

_T = [int(abs(math.sin(i + 1)) * (2**32)) & 0xFFFFFFFF for i in range(64)]

# ASSUMPTION: Only the init vector differs from standard MD5.
# Some per-round constants or shift amounts may also differ (not recoverable).
_INIT_A = 0x1324AD68
_INIT_B = 0x98765478
_INIT_C = 0xFDA85EC9
_INIT_D = 0x9645687A

_S = [
    [7, 12, 17, 22] * 4,
    [5,  9, 14, 20] * 4,
    [4, 11, 16, 23] * 4,
    [6, 10, 15, 21] * 4,
]

def _left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def _md5_modified(message: bytes) -> bytes:
    """MD5 with custom init constants. Round functions/constants assumed standard.
    ASSUMPTION: Only IV changed; all other internals standard."""
    # Pre-processing: adding padding bits
    orig_len_bits = (len(message) * 8) & 0xFFFFFFFFFFFFFFFF
    message = bytearray(message)
    message.append(0x80)
    while len(message) % 64 != 56:
        message.append(0x00)
    message += struct_pack('<Q', orig_len_bits)

    a0, b0, c0, d0 = _INIT_A, _INIT_B, _INIT_C, _INIT_D

    for chunk_start in range(0, len(message), 64):
        chunk = message[chunk_start:chunk_start + 64]
        M = struct.unpack('<16I', bytes(chunk))
        A, B, C, D = a0, b0, c0, d0

        for i in range(64):
            if 0 <= i <= 15:
                F = (B & C) | ((~B) & D)
                g = i
            elif 16 <= i <= 31:
                F = (D & B) | ((~D) & C)
                g = (5 * i + 1) % 16
            elif 32 <= i <= 47:
                F = B ^ C ^ D
                g = (3 * i + 5) % 16
            else:
                F = C ^ (B | (~D))
                g = (7 * i) % 16
            F = (F + A + _T[i] + M[g]) & 0xFFFFFFFF
            s = _S[i // 16][i % 4]
            A = D
            D = C
            C = B
            B = (B + _left_rotate(F, s)) & 0xFFFFFFFF

        a0 = (a0 + A) & 0xFFFFFFFF
        b0 = (b0 + B) & 0xFFFFFFFF
        c0 = (c0 + C) & 0xFFFFFFFF
        d0 = (d0 + D) & 0xFFFFFFFF

    return struct.pack('<4I', a0, b0, c0, d0)

from struct import pack as struct_pack

def hash_name(name: str) -> bytes:
    """Compute the modified MD5 hash of the name."""
    return _md5_modified(name.encode('ascii', errors='replace'))

def blowfish_encrypt_8bytes(key: bytes, data: bytes) -> bytes:
    """Encrypt 8 bytes with Blowfish."""
    if not HAS_BLOWFISH:
        raise RuntimeError("pycryptodome not available; install it for Blowfish support")
    bf = Blowfish.new(key, Blowfish.MODE_ECB)
    return bf.encrypt(data)

def blowfish_decrypt_8bytes(key: bytes, data: bytes) -> bytes:
    """Decrypt 8 bytes with Blowfish."""
    if not HAS_BLOWFISH:
        raise RuntimeError("pycryptodome not available; install it for Blowfish support")
    bf = Blowfish.new(key, Blowfish.MODE_ECB)
    return bf.decrypt(data)

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Steps:
      1. Compute modified-MD5 hash of name (16 bytes) -> Blowfish key.
      2. We want the first 5 decrypted bytes to be b'Thigh'.
         So encrypt b'Thigh\x00\x00\x00' with Blowfish(hash).
         Those 8 bytes become the first 8 bytes of the serial payload.
      3. Encode those 8 bytes as 16 uppercase hex chars -> first 16 serial chars.
         ASSUMPTION: The bignum conversion stores bytes in little-endian DWORD pairs:
           serial_hex = hex(dword1_le) + hex(dword0_le) where bytes are two 4-byte LE words.
      4. Append at least 4 more chars (ASSUMPTION: unknown, use 'AAAA' placeholder).
    """
    h = hash_name(name)
    # The plaintext we want after decryption
    # 'Thig' for first 4, 'h' for 5th, rest can be anything
    plaintext = b'Thigh\x00\x00\x00'  # 8 bytes for one Blowfish block
    ciphertext = blowfish_encrypt_8bytes(h, plaintext)

    # The bignum format: first 16 serial chars are the hex representation.
    # From writeup: serial chars 'A1B1C1D1A2B2C2D2' -> bignum = 0xA2B2C2D2_A1B1C1D1
    # i.e., the second 8 hex chars (chars 9-16) are the HIGH dword,
    #        the first 8 hex chars (chars 1-8) are the LOW dword.
    # Both stored as big-endian hex strings in the serial.
    # So serial[0:8] hex -> dword0, serial[8:16] hex -> dword1
    # bignum value = dword1 << 32 | dword0  (little-endian dword order)
    # The raw bytes exported (base 256) = just the LE bytes of the bignum.
    # ciphertext bytes -> interpret as two LE dwords
    dword0 = struct.unpack('<I', ciphertext[0:4])[0]
    dword1 = struct.unpack('<I', ciphertext[4:8])[0]
    serial_part1 = '{:08X}{:08X}'.format(dword0, dword1)

    # ASSUMPTION: remaining serial chars (need at least 20 total) are unknown.
    # Use placeholder 'AAAA'.
    serial = serial_part1 + 'AAAA'
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.

    Returns True if the serial passes the known checks.
    ASSUMPTION: Only the first 16+check chars are verified here;
    additional checks from truncated writeup are not implemented.
    """
    if not name:
        return False
    if len(serial) < 20:
        return False

    h = hash_name(name)

    # Extract first 16 serial chars, parse as two LE dwords
    serial_hex = serial[:16]
    if len(serial_hex) != 16:
        return False
    try:
        dword0 = int(serial_hex[0:8], 16)
        dword1 = int(serial_hex[8:16], 16)
    except ValueError:
        return False

    ciphertext = struct.pack('<II', dword0, dword1)

    try:
        decrypted = blowfish_decrypt_8bytes(h, ciphertext)
    except RuntimeError:
        # ASSUMPTION: if blowfish not available, cannot verify
        return False

    # Check: first char == 'T', second char in {'h','i','g'}, fourth char == 'h', fifth == 'h'
    if decrypted[0:1] != b'T':
        return False
    if decrypted[1:2] not in (b'h', b'i', b'g'):
        return False
    if decrypted[3:4] != b'h':
        return False
    if decrypted[4:5] != b'h':
        return False

    # ASSUMPTION: further checks on serial[16:] not recovered from truncated writeup.
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
