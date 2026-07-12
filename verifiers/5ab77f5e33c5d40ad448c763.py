# Partial reconstruction of exercise_crackme_fixed4good by badsector
# Based on writeup by bLaCk-eye describing:
#   RSA-256 decryption, ElGamal-64, CRT, CRC32, RC4
#
# The writeup is truncated and does not provide full details of all checks.
# What IS described:
#   1. Name >= 4 chars, serial == 256 hex chars (128 bytes as hex?)
#      Actually serial length must be 256 chars (0x100 = 256 chars checked)
#   2. Serial is processed as 4 blocks of 64 hex chars (16 bytes each)
#      via RSA-256: BigPowMod(block, exponent=0x65A4D, modulus=big_N)
#      modulus N = 0x9DF35894725AB126D91561BAD0336C12E9ABC87... (truncated in writeup)
#   3. Result is 64 bytes total
#   4. First 4 bytes of decrypted serial checked against CRC32 constant
#   5. RC4 key is the lyric string 0xA2 bytes
#   6. ElGamal-64 and CRT are mentioned but details not given
#   7. Anti-debug trick: reads PEB+0x30
#
# ASSUMPTION: The modulus N is only partially shown in the writeup ('9DF35894725AB126D91561BAD0336C12E9ABC87...')
# ASSUMPTION: The RSA exponent d = 0x65A4D
# ASSUMPTION: Serial input is 256 hex characters = 128 bytes, processed as 4x32-byte blocks
# ASSUMPTION: CRC32 constant, ElGamal parameters, CRT details are unknown
# ASSUMPTION: The final verification logic after decryption is not shown

import struct

# Known constants from writeup
RSA_EXPONENT = 0x65A4D  # decryption exponent d
# ASSUMPTION: modulus truncated in writeup - partial value shown
RSA_MODULUS_HEX = "9DF35894725AB126D91561BAD0336C12E9ABC87"  # TRUNCATED - unknown full value

RC4_KEY = ("There's a time to live, and a time to die\r\n"
           "When it's time to meet the maker\r\n"
           "There's time to live, but isn't it strange\r\n"
           "That as soon as you're born, you're dying")

def crc32_custom(data):
    """Standard CRC32"""
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF

def rc4_setkey(key_bytes):
    """RC4 key schedule"""
    S = list(range(256))
    j = 0
    klen = len(key_bytes)
    for i in range(256):
        j = (j + S[i] + key_bytes[i % klen]) % 256
        S[i], S[j] = S[j], S[i]
    return S

def rc4_crypt(S, data):
    """RC4 stream cipher"""
    S = list(S)  # copy
    i = j = 0
    out = []
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(byte ^ S[(S[i] + S[j]) % 256])
    return bytes(out)

def rsa_decrypt_block(block_bytes, d, n):
    """RSA decryption: m = c^d mod n"""
    # block_bytes is 16 bytes treated as big integer
    c = int.from_bytes(block_bytes, 'big')
    m = pow(c, d, n)
    # Output 16 bytes
    return m.to_bytes(16, 'big')

def verify(name, serial):
    """
    Attempt to verify name/serial.
    ASSUMPTION: Many parts of this are unknown due to truncated writeup.
    This is a PARTIAL reconstruction only.
    """
    # Check name length
    if len(name) < 4:
        return False
    
    # Check serial length = 256 chars
    if len(serial) != 256:
        return False
    
    # ASSUMPTION: serial is 256 hex chars = 128 bytes
    try:
        serial_bytes = bytes.fromhex(serial)
    except ValueError:
        return False
    
    if len(serial_bytes) != 128:
        return False
    
    # ASSUMPTION: RSA modulus is unknown (truncated in writeup)
    # Cannot perform real RSA decryption without full modulus
    # ASSUMPTION: N is some 128-bit number starting with 9DF35894725AB126D91561BAD0336C12E9ABC87...
    # We cannot complete the check without the full modulus
    # ASSUMPTION: partial modulus - this will be wrong
    N_hex = "9DF35894725AB126D91561BAD0336C12E9ABC870"  # ASSUMPTION: padded, unknown real value
    N = int(N_hex, 16)
    
    d = RSA_EXPONENT
    
    # Decrypt 4 blocks of 32 bytes each (the writeup says 128-bit blocks = 16 bytes,
    # processed 4 times from 256 hex chars / 4 = 64 hex chars per block = 32 bytes)
    # ASSUMPTION: block size is 32 bytes (256-bit) given RSA-256 designation
    decrypted = bytearray()
    for i in range(4):
        block = serial_bytes[i*32:(i+1)*32]
        c = int.from_bytes(block, 'big')
        m = pow(c, d, N)
        decrypted += m.to_bytes(32, 'big')
    
    # Now we have 128 bytes decrypted
    # ASSUMPTION: first 4 bytes checked against CRC32 constant (constant unknown)
    # The writeup says: "first 4 bytes of the decrypted serial are hashed using crc32 algo
    # and checked with a constant" - constant not given
    # ASSUMPTION: unknown CRC32 constant
    CRC32_CONST = 0xDEADBEEF  # ASSUMPTION: placeholder - real value unknown
    first4 = bytes(decrypted[:4])
    if crc32_custom(first4) != CRC32_CONST:
        pass  # ASSUMPTION: returning False here but constant unknown
    
    # RC4 setup with the lyric key
    rc4_key_bytes = RC4_KEY.encode('ascii')
    S = rc4_setkey(rc4_key_bytes)
    
    # ASSUMPTION: Some portion of decrypted data is RC4-decrypted
    # ASSUMPTION: ElGamal-64 check details unknown
    # ASSUMPTION: CRT details unknown
    
    # Cannot complete verification - algorithm only partially recovered
    # ASSUMPTION: returning False as we cannot do the full check
    return False  # ASSUMPTION: placeholder

def keygen(name):
    """
    Cannot generate valid serial without:
    - Full RSA modulus N
    - CRC32 constant  
    - ElGamal-64 parameters
    - CRT parameters
    - Full algorithm flow
    """
    # ASSUMPTION: keygen not implementable from available information
    raise NotImplementedError(
        "Cannot generate serial: RSA modulus, CRC32 constant, ElGamal parameters, "
        "and CRT parameters are not fully specified in the writeup."
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
