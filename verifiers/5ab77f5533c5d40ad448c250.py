import random
import hashlib

# NOTE: This is a partial reconstruction. The full algorithm requires:
# 1. snefru hash implementation
# 2. serpent block cipher implementation
# 3. RSA and Paillier crypto
# We reconstruct the logic as described, marking missing pieces.

# --- mathExt helpers ---
def extEuclideanAlg(a, b):
    if b == 0:
        return 1, 0, a
    else:
        x, y, gcd = extEuclideanAlg(b, a % b)
        return y, x - y * (a // b), gcd

def modInvEuclid(a, m):
    x, y, gcd = extEuclideanAlg(a, m)
    if gcd == 1:
        return x % m
    else:
        return None

# --- ASSUMPTION: snefru returns a tuple of 4 x 32-bit integers ---
# The real snefru implementation is not provided. We cannot replicate it.
# Placeholder that would need to be replaced with a real snefru impl.
def snefru(data):
    # ASSUMPTION: snefru hash returning 4 x 32-bit words
    # This is a placeholder - real snefru must be used for correct output
    raise NotImplementedError('snefru hash implementation required')

# --- ASSUMPTION: serpent block cipher with 16-byte key ---
# The real serpent implementation is not provided here in full.
# Placeholder class.
class serpent_cipher:
    def __init__(self, key):
        # ASSUMPTION: standard serpent cipher with given key
        raise NotImplementedError('serpent cipher implementation required')
    def blockEncrypt(self, src, srcOff, dst, dstOff):
        raise NotImplementedError
    def blockDecrypt(self, src, srcOff, dst, dstOff):
        raise NotImplementedError

# --- Constants from keygen ---
PAILLIER_P = 0xA7A519EED3D56F9A1663AA807CA84D5152379B5AF31BE5CED5BF09C72A283B19
SERPENT_KEY = b'\xD5\xA8\x23\x18\x6C\xE3\xA6\x19\xFF\x35\x72\xFB\x7A\x78\x43\x23'

RSA_D = 0x33bad48c12e689c0498df34b9c3b0e407a2b54ff2c5a3e686880b738cd4c3da8b6da6075de038f8da58514975a74d78a4c4c837a6102dd1e15bc69432dad6003
RSA_N = 0xa50ae80cb59d8e7b29302af422250b87db8a48f96b0bc10e4069bce73a5e68bfe242e6642a40541d7399eb4dfc98cd91810209b505776cb283110b1728eefaf3

def genKey(name):
    """
    Full keygen as described in solution:
    1. snefru(name) -> 128-bit hash as 4 x 32-bit words
    2. Assemble as 128-bit big-endian integer (paillierDec)
    3. Paillier encrypt with p = PAILLIER_P, n = p^2
    4. Serialize paillierEnc to 64-byte big-endian
    5. Serpent encrypt each 16-byte block with SERPENT_KEY
    6. Deserialize to integer rsaEnc
    7. RSA decrypt: rsaDec = pow(rsaEnc, RSA_D, RSA_N)
    8. Return hex string of rsaDec
    """
    # ASSUMPTION: snefru returns list/tuple of 4 uint32 values
    h = snefru(name)
    snefruRes = h.finalize()

    paillierDec = (snefruRes[3]) | (snefruRes[2] << (32 * 1)) | (snefruRes[1] << (32 * 2)) | (snefruRes[0] << (32 * 3))

    p = PAILLIER_P
    n = p ** 2
    # Paillier encryption: (p+1)^m * r^p mod n, r random
    paillierEnc = (pow(p + 1, paillierDec, n) * pow(random.randrange(n), p, n)) % n

    serpentEnc = bytearray(0x40)
    serpentDec = bytearray(0x40)
    tmp = paillierEnc
    for i in reversed(range(0x40)):
        serpentEnc[i] = tmp & 0xFF
        tmp >>= 8

    # ASSUMPTION: serpent_cipher is a working Serpent block cipher implementation
    c = serpent_cipher(SERPENT_KEY)
    c.blockEncrypt(serpentEnc, 0x00, serpentDec, 0x00)
    c.blockEncrypt(serpentEnc, 0x10, serpentDec, 0x10)
    c.blockEncrypt(serpentEnc, 0x20, serpentDec, 0x20)
    c.blockEncrypt(serpentEnc, 0x30, serpentDec, 0x30)

    rsaEnc = 0
    for i in range(0x40):
        rsaEnc <<= 8
        rsaEnc |= serpentDec[i]

    if rsaEnc >= n:
        return genKey(name)  # retry with different random r

    rsaDec = pow(rsaEnc, RSA_D, RSA_N)
    return '{:x}'.format(rsaDec)

def paillierDecrypt(p, p_minus_1, n, key):
    """Paillier decryption as described in solution."""
    a = modInvEuclid(p, p_minus_1)
    b = pow(pow(key, a, p), p, n)
    ret = (((key % n) * modInvEuclid(b, n)) % n - 1) // p
    return ret

def verify(name, serial):
    """
    Verify by generating a valid serial and comparing.
    NOTE: Because the keygen is probabilistic (random Paillier blinding),
    we cannot directly verify a given serial without the crackme's check logic.
    ASSUMPTION: The crackme verifies by running the inverse operations:
      1. RSA encrypt serial (public key operations - not given)
      2. Serpent decrypt
      3. Paillier decrypt
      4. Compare to snefru(name)
    Without the RSA public key (e) and the crackme's exact check, we cannot implement verify.
    """
    # ASSUMPTION: We attempt to generate a serial and compare
    # This is only valid if we have working snefru and serpent implementations
    raise NotImplementedError(
        'verify() requires snefru and serpent implementations, and the crackme RSA public key (e) is not given.'
    )

def keygen(name):
    """
    Generate a valid serial for the given name.
    Requires working snefru and serpent implementations.
    """
    if isinstance(name, str):
        name = name.encode()
    return genKey(name)


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
