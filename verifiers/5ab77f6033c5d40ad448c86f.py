import hashlib
import base64
import struct

# ASSUMPTION: Based on the writeup mentioning MD5 and Base64 are used in the serial validation,
# and that the check involves name/serial fields in a dialog box.
# The writeup is truncated before the actual serial validation algorithm is shown.
# We can only reconstruct a partial skeleton based on what is described.

def md5_bytes(data: bytes) -> bytes:
    return hashlib.md5(data).digest()

def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def verify(name: str, serial: str) -> bool:
    # ASSUMPTION: The crackme reads name and serial from dialog fields.
    # PEiD Krypto Analyzer detected MD5 and Base64 usage.
    # The writeup is truncated before revealing the exact algorithm.
    # Below is a plausible but ASSUMED reconstruction:

    # ASSUMPTION: name is encoded/hashed with MD5
    name_bytes = name.encode('ascii', errors='replace')
    name_hash = md5_bytes(name_bytes)  # 16 bytes

    # ASSUMPTION: The hash (or part of it) is Base64-encoded and compared to serial
    # or the serial is decoded from Base64 and compared to the hash.
    try:
        serial_decoded = base64.b64decode(serial)
    except Exception:
        return False

    # ASSUMPTION: serial decoded should match MD5 of name
    return serial_decoded == name_hash

def keygen(name: str) -> str:
    # ASSUMPTION: Generate serial as Base64(MD5(name))
    name_bytes = name.encode('ascii', errors='replace')
    name_hash = md5_bytes(name_bytes)
    serial = base64.b64encode(name_hash).decode('ascii')
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
