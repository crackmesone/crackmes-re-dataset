import struct
import hashlib

# The writeup shows a DLL that implements MD5 hashing (custom MD5 implementation)
# with standard MD5 initialization constants:
#   A = 0x67452301, B = 0xEFCDAB89, C = 0x98BADCFE, D = 0x10325476
# The md5_mod function hashes the name using this MD5 implementation.
# The serial generation/validation logic beyond the MD5 call is TRUNCATED
# in the writeup, so we can only partially reconstruct the algorithm.

# ASSUMPTION: The crackme computes MD5 of the name, then derives the serial
# from the MD5 digest in some way (e.g., hex string, partial bytes, formatted).
# The exact serial format and comparison logic is NOT shown in the truncated writeup.

def md5_of_name(name: str) -> bytes:
    """Compute standard MD5 of the name bytes.
    The assembly implements a standard MD5 with canonical init constants,
    so Python's hashlib.md5 should produce the same result."""
    return hashlib.md5(name.encode('latin-1')).digest()


def verify(name: str, serial: str) -> bool:
    """
    Verify the serial for the given name.
    ASSUMPTION: The serial is the uppercase hex string of MD5(name).
    The writeup shows MD5 is computed but the serial comparison/format
    is truncated, so this is a best-guess.
    """
    digest = md5_of_name(name)
    # ASSUMPTION: serial format is uppercase hex of MD5 digest
    expected = digest.hex().upper()
    return serial.upper() == expected


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: serial = MD5(name) as uppercase hex.
    """
    digest = md5_of_name(name)
    # ASSUMPTION: serial is uppercase hex representation of MD5 digest
    return digest.hex().upper()



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
