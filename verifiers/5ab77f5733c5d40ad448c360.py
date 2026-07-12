# Reconstruction of l0calh0st Keyfileme #1 keygen
# Based on the Delphi source (Project2.dpr) provided in the solution writeup.
#
# Algorithm:
#   1. Treat the name as a big integer (big-endian base-256 / raw bytes).
#   2. Compute m = name^D mod N  (RSA-like private-key operation)
#   3. The key file contains three 16-byte AES-ECB blocks encrypted with key
#      'l0cah0st\'s KFM1':
#        block1  = AES_ECB_enc(key, cn)            where cn is a fixed 16-byte constant
#        block2  = AES_ECB_enc(key, m[0:16])
#        block3  = AES_ECB_enc(key, m[16:32])
#   4. The name must be 1..30 chars and m must not contain any 0x00 byte.
#
# ASSUMPTION: The Delphi FGInt library converts the name string to a big integer
#             by treating it as a big-endian base-256 number (raw bytes).
# ASSUMPTION: EncryptStringECB encrypts one 16-byte block with AES-128 in ECB mode
#             using the key decoded from the hex string '6C306361683073742773204B464D3100'
#             which is b'l0cah0st\'s KFM1\x00'  (16 bytes).
# ASSUMPTION: FGIntModExp and FGIntToBase256String use standard big-endian
#             big-integer representation without leading zero padding.
#             The result m is zero-padded / truncated to 32 bytes for the key file.

import struct
from Crypto.Cipher import AES  # pip install pycryptodome

# RSA-like parameters from the source
N_HEX = 'A91BF2409387C0DB996DF10E29F77A46A64D3B2DDB4F74279641C94C881AE991'
D_HEX = '487EC980737E6BE7F843506691091DAA7F1D640D1707FA333A1DF1E2CA29674D'

N = int(N_HEX, 16)
D = int(D_HEX, 16)

# Fixed 16-byte constant cn (from source: #$5B#$32#$83#$D6#$41#$6F#$F0#$15#$D4#$7B#$2B#$10#$A4#$91#$4D#$F9)
CN = bytes([0x5B, 0x32, 0x83, 0xD6, 0x41, 0x6F, 0xF0, 0x15,
            0xD4, 0x7B, 0x2B, 0x10, 0xA4, 0x91, 0x4D, 0xF9])

# AES key from hex string '6C306361683073742773204B464D3100'
AES_KEY = bytes.fromhex('6C306361683073742773204B464D3100')  # b"l0cah0st's KFM1\x00


def aes_ecb_enc(key: bytes, plaintext: bytes) -> bytes:
    """Encrypt exactly 16 bytes with AES-128-ECB."""
    assert len(plaintext) == 16
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(plaintext)


def aes_ecb_dec(key: bytes, ciphertext: bytes) -> bytes:
    """Decrypt exactly 16 bytes with AES-128-ECB."""
    assert len(ciphertext) == 16
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(ciphertext)


def name_to_fgint(name: str) -> int:
    """Convert name string to big integer (big-endian raw bytes)."""
    # ASSUMPTION: direct raw byte interpretation, big-endian
    raw = name.encode('latin-1')
    return int.from_bytes(raw, 'big')


def fgint_to_base256(m: int, length: int = 32) -> bytes:
    """Convert big integer back to big-endian bytes, padded/truncated to length."""
    # ASSUMPTION: result is big-endian, padded with leading zeros to 'length' bytes
    byte_len = (m.bit_length() + 7) // 8
    raw = m.to_bytes(byte_len, 'big')
    # Pad on the left or truncate to desired length
    if len(raw) < length:
        raw = b'\x00' * (length - len(raw)) + raw
    elif len(raw) > length:
        raw = raw[-length:]
    return raw


def keygen(name: str) -> bytes:
    """
    Generate the keyfile content for the given name.
    Returns the raw bytes to write to <computername>.key
    Returns None if the name is invalid or produces a bad serial (contains 0x00).
    """
    if not (1 <= len(name) <= 30):
        return None

    # Compute m = name^D mod N  (RSA private-key operation)
    c = name_to_fgint(name)
    m_int = pow(c, D, N)

    # Convert m to 32 bytes (two 16-byte blocks)
    ab = fgint_to_base256(m_int, 32)

    # Check: no 0x00 bytes allowed in m
    if b'\x00' in ab:
        return None  # Not valid serial for that name

    block1 = ab[0:16]
    block2 = ab[16:32]

    keyfile = (aes_ecb_enc(AES_KEY, CN) +
               aes_ecb_enc(AES_KEY, block1) +
               aes_ecb_enc(AES_KEY, block2))
    return keyfile


def verify(name: str, serial: bytes) -> bool:
    """
    Verify a keyfile (serial as raw bytes) against the given name.
    Mirrors what the crackme does when reading the .key file:
      - Decrypt each 16-byte block with AES-ECB
      - First block must equal CN
      - Remaining blocks form ab = m (big-endian, 32 bytes)
      - Verify that name^D mod N == ab  (i.e. ab^E mod N == name, but E is unknown)
      ASSUMPTION: verification checks ab^? mod N == c; since we only have D we
                  re-derive and compare.
    """
    if not (1 <= len(name) <= 30):
        return False
    if len(serial) < 48 or len(serial) % 16 != 0:
        return False

    # Decrypt blocks
    dec_blocks = []
    for i in range(0, len(serial), 16):
        dec_blocks.append(aes_ecb_dec(AES_KEY, serial[i:i+16]))

    # First block must equal CN
    if dec_blocks[0] != CN:
        return False

    # Reconstruct ab from remaining blocks
    ab = b''.join(dec_blocks[1:])
    if b'\x00' in ab:
        return False

    # Compare against expected keyfile
    expected = keygen(name)
    if expected is None:
        return False
    return serial == expected

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
