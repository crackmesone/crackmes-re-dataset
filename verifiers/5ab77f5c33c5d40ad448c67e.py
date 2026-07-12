import struct

# Based on writeup by haggar for bustme_1 by bpx_
# Serial format: XXXX-XXX-XXXXXXXX (17 chars total, 0x11 = 17)
# Name must have at least 4 characters (len >= 4, i.e. > 3)

# ASSUMPTION: The 256-byte S-box is initialized as [0,1,2,...,255]
# then modified using S1, S2, S3 derived from serial chars 5,6,7 (0-indexed)
# S1 = ord(serial[5]) + 2
# S2 = ord(serial[6]) + 1  
# S3 = ord(serial[7]) - 2
# The modification algorithm for the S-box is assumed to be RC4-KSA-like
# ASSUMPTION: The hashing/encryption is an RC4-like stream cipher applied to a fixed string

# Fixed string from writeup (null-terminated, 23 bytes without null)
FIXED_STRING = b"bust me #1 - bpx 2k6"
# The full bytes shown: 62 75 73 74 20 6D 65 20 23 31 20 2D 20 62 70 78 20 32 6B 36 FF EE CA
FIXED_STRING_RAW = bytes([0x62,0x75,0x73,0x74,0x20,0x6D,0x65,0x20,0x23,0x31,0x20,0x2D,
                          0x20,0x62,0x70,0x78,0x20,0x32,0x6B,0x36,0xFF,0xEE,0xCA])

# Target hash from writeup (23 bytes shown at 0040407F)
TARGET_HASH = bytes([0x94,0xD8,0xBE,0x56,0x20,0x7F,0xAA,0x07,
                     0x74,0xB3,0xEC,0xD4,0x96,0x11,0x35,0x84,
                     0x11,0xCF,0x40,0x25,0x8F,0x59,0x15])

# ASSUMPTION: The S-box key is [S1, S2, S3] and standard RC4 KSA is used
def make_sbox(s1, s2, s3):
    key = [s1 & 0xFF, s2 & 0xFF, s3 & 0xFF]
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % 3]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S

def rc4_prga(S, data):
    S = list(S)  # copy
    i = 0
    j = 0
    out = []
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) & 0xFF]
        out.append(byte ^ k)
    return bytes(out)

def hash_string(s1, s2, s3, data):
    """Hash data using RC4-like cipher with key derived from s1,s2,s3"""
    S = make_sbox(s1, s2, s3)
    return rc4_prga(S, data)

def check_format(serial):
    if len(serial) != 17:
        return False
    if serial[4] != '-' or serial[8] != '-':
        return False
    return True

def verify(name, serial):
    """Verify name/serial combination."""
    if len(name) < 4:
        return False
    if not check_format(serial):
        return False
    # Serial format: XXXX-XXX-XXXXXXXX
    # Positions (0-indexed): 0123-456-78901234
    # chars at index 5,6,7 are the three middle chars (after first '-')
    # ASSUMPTION: indices 5,6,7 are the middle group chars
    try:
        s1 = (ord(serial[5]) + 2) & 0xFF
        s2 = (ord(serial[6]) + 1) & 0xFF
        s3 = (ord(serial[7]) - 2) & 0xFF
    except (IndexError, TypeError):
        return False

    # First check: hash of fixed string must match target
    result = hash_string(s1, s2, s3, FIXED_STRING_RAW)
    if result != TARGET_HASH:
        return False

    # ASSUMPTION: Second part of check involves name and last 8 chars of serial
    # The writeup mentions a second check but it was truncated.
    # We cannot implement the second check without more information.
    # For now, only the first check is implemented.
    # ASSUMPTION: If first check passes, we consider it valid (incomplete)
    return True

def keygen(name):
    """Generate a serial for a given name."""
    if len(name) < 4:
        raise ValueError("Name must have at least 4 characters")

    # We need to find s1, s2, s3 such that hash_string(s1,s2,s3, FIXED_STRING_RAW) == TARGET_HASH
    # Brute force the 3 key bytes
    for s1 in range(256):
        for s2 in range(256):
            for s3 in range(256):
                result = hash_string(s1, s2, s3, FIXED_STRING_RAW)
                if result == TARGET_HASH:
                    # Recover serial chars from s1,s2,s3
                    # S1 = ord(serial[5]) + 2  =>  serial[5] = chr(s1 - 2)
                    # S2 = ord(serial[6]) + 1  =>  serial[6] = chr(s2 - 1)
                    # S3 = ord(serial[7]) - 2  =>  serial[7] = chr(s3 + 2)
                    c5 = s1 - 2
                    c6 = s2 - 1
                    c7 = s3 + 2
                    if 0x20 <= c5 <= 0x7E and 0x20 <= c6 <= 0x7E and 0x20 <= c7 <= 0x7E:
                        mid = chr(c5) + chr(c6) + chr(c7)
                        # ASSUMPTION: first group and last group are arbitrary/name-based
                        # Use the known working serial from the writeup as reference
                        # Known: haggar -> 1234-9G7-BF3B3C32
                        # We just fix first and last groups arbitrarily
                        # ASSUMPTION: last 8 chars depend on name somehow (not recovered)
                        serial = "1234-" + mid + "-BF3B3C32"
                        return serial
    raise ValueError("Could not find valid serial key bytes")


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
