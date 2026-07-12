import struct
import hashlib

# ASSUMPTION: This is a partial reconstruction based on the writeup fragments.
# The full algorithm involves:
# 1. A keyfile 'alarm.txt' containing 'wakeup!'
# 2. Name input (max 10 chars)
# 3. A 'Sleepy ID' derived from GetTickCount() % 100
# 4. Serial validation using CRC32, SHA1, and a modified MD5
# The writeup is truncated and does not provide full serial format/check details.

import binascii
import time

def crc32(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    return binascii.crc32(data) & 0xFFFFFFFF

def sha1_hex(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    return hashlib.sha1(data).hexdigest()

def md5_hex(data):
    if isinstance(data, str):
        data = data.encode('latin-1')
    # ASSUMPTION: The crackme uses a 'modified MD5' - we use standard MD5 as base
    return hashlib.md5(data).hexdigest()

# ASSUMPTION: Sleepy ID is GetTickCount() % 100 at runtime; for keygen we accept it as param
# ASSUMPTION: The serial format combines CRC32 of name, SHA1, and modified MD5 in some way
# The writeup mentions sprintf converting hex to ASCII for these hash outputs

def compute_sleepy_id():
    """Returns the Sleepy ID as computed by the crackme (GetTickCount % 100)."""
    tick = int(time.time() * 1000) & 0xFFFFFFFF
    return tick % 100

def verify(name, serial):
    """
    ASSUMPTION: Cannot fully verify without complete algorithm.
    The crackme checks:
    - Name length <= 10
    - alarm.txt must contain 'wakeup!'
    - Serial likely derived from CRC32(name), SHA1(name+sleepy_id), modified MD5
    This is a stub that cannot be fully implemented from the truncated writeup.
    """
    if len(name) > 10 or len(name) == 0:
        return False
    # ASSUMPTION: Cannot implement full check from available information
    # Partial checks we can reconstruct:
    crc = crc32(name)
    sha = sha1_hex(name)
    md = md5_hex(name)
    # ASSUMPTION: serial is some concatenation/transformation of these values
    # We cannot verify without the complete writeup
    raise NotImplementedError("Full serial verification algorithm not available from truncated writeup")

def keygen(name, sleepy_id=None):
    """
    Generate a serial for the given name.
    ASSUMPTION: sleepy_id is needed at runtime from the crackme.
    ASSUMPTION: Serial format = CRC32(name) + SHA1(name) + modifiedMD5(name+id) in some sprintf hex format.
    This is a partial reconstruction - the exact combination is unknown.
    """
    if len(name) > 10 or len(name) == 0:
        raise ValueError("Name must be 1-10 characters")
    
    if sleepy_id is None:
        sleepy_id = compute_sleepy_id()
    
    crc = crc32(name)
    # ASSUMPTION: CRC32 formatted as 8-char hex
    crc_str = "%08X" % crc
    
    # ASSUMPTION: SHA1 of name (possibly with sleepy_id appended)
    sha = sha1_hex(name + str(sleepy_id))
    # sha1 is 40 hex chars
    
    # ASSUMPTION: Modified MD5 of name (possibly with sleepy_id)
    md = md5_hex(name + str(sleepy_id))
    # md5 is 32 hex chars
    
    # ASSUMPTION: Serial is some combination - using CRC32-SHA1-MD5 as placeholder
    serial = "%s-%s-%s" % (crc_str, sha.upper(), md.upper())
    return serial


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
