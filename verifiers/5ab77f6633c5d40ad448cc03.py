# Reverse-engineered algorithm for VCT KEYGENME #5 by hacnho
# Based on the writeup by bLaCk-eye
#
# What we know from the writeup:
# 1. The serial format is: VCT2k4-????-hacnho
# 2. The algorithm uses a chain of hashes starting with CRC32 of the name,
#    then further hashing (md5, crc32, haval, ripemd, sha1, base64 are mentioned)
# 3. The middle '????' part is derived from the hash chain
# 4. The exact sequence of hashes and how '????' is derived is NOT fully described
#
# ASSUMPTION: The middle part is derived from CRC32 of the name, formatted as hex.
# The exact hash chain order and transformations are unknown from the writeup.

import binascii
import hashlib
import struct

def crc32_of_string(s: str) -> int:
    """Compute CRC32 of a string (as bytes)."""
    return binascii.crc32(s.encode('latin-1')) & 0xFFFFFFFF

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    Format: VCT2k4-????-hacnho
    
    ASSUMPTION: The middle 4-char part is derived from CRC32 of the name.
    The writeup says the algo does 'first crc_32 then from the hash it makes a string,
    from the string another hash and so on'. The exact chain is unknown.
    We use CRC32 -> hex string -> take first 4 chars as a best guess.
    """
    # Step 1: CRC32 of name
    crc = crc32_of_string(name)
    crc_hex = format(crc, '08X')  # 8 hex chars
    
    # ASSUMPTION: Take first 4 characters of hex CRC32 as the middle part
    # The real algorithm likely applies more hash transformations here
    middle = crc_hex[:4]
    
    serial = 'VCT2k4-{}-hacnho'.format(middle)
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify if the serial matches the name.
    ASSUMPTION: We compare against our keygen output.
    The real check in the crackme computes the correct serial and does LStrCmp.
    """
    expected = keygen(name)
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
