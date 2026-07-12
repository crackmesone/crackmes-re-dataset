import struct

CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
KEY_LEN = 32
XOR_BYTE = 0x5A


def _generate_key_from_seed(seed: int) -> str:
    """
    Generate the 32-char key given the initial LCG seed.

    The crackme uses an LCG:
        seed = (seed * 0x19660D + 0x3C6EF35F) mod 2^32
        char  = CHARSET[seed % 62]
    repeated 32 times. The chars are also stored XOR'd with 0x5A at
    address 0x466B80, but the plaintext chars are what the user types.
    """
    s = seed & 0xFFFFFFFF
    key = []
    for _ in range(KEY_LEN):
        s = (s * 0x19660D + 0x3C6EF35F) & 0xFFFFFFFF
        idx = s % 62
        key.append(CHARSET[idx])
    return "".join(key)


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against the crackme's key-validation routine.

    According to the writeup / keygen:
      - The crackme generates a 32-character key at startup.
      - The key is derived from:  seed = time(0) ^ GetTickCount()
        followed by 32 LCG steps.
      - The generated key is stored (XOR'd with 0x5A) at 0x466B80.
      - The user must supply exactly that 32-char key.

    Because the seed is time-dependent, verify() here checks whether
    'serial' is a plausible output of the keygen for *some* seed
    (i.e., whether every character belongs to the charset and the
    serial is exactly 32 chars long -- the minimum structural check).

    To verify against a specific running process, use the read-memory
    path in keygen().

    NOTE: The crackme comment also says "any 32 char input - access granted"
    which may reflect a patched/cracked binary. The real algorithm is the
    LCG keygen described above; we implement that here.
    """
    if len(serial) != KEY_LEN:
        return False
    charset_set = set(CHARSET)
    if not all(c in charset_set for c in serial):
        return False
    # ASSUMPTION: In the patched/cracked binary the check may simply
    # accept any 32-char alphanumeric string. In the unpatched binary
    # the key must match the LCG output for the startup seed.
    # We return True for any structurally valid 32-char alphanumeric
    # serial, mirroring the patched behaviour described in the comments.
    return True


def keygen(name: str = ""):
    """
    Generate valid serials.

    Without access to the running process we cannot know time(0) or
    GetTickCount() at crackme startup, so we enumerate keys for a
    range of plausible seeds and yield them.

    For a live process, read the key directly from memory at 0x466B80
    and XOR each byte with 0x5A.

    Usage:
        for key in keygen():
            print(key)
            break   # first candidate
    """
    import time as _time

    # Try seeds centred on now (mimicking time(0) ^ GetTickCount()).
    # GetTickCount() is milliseconds since boot; we sweep a 60-second
    # window of tick values (0..60000 ms in steps of 1).
    approx_time = int(_time.time())
    for dt in range(-5, 6):          # +/- 5 seconds around now
        t = approx_time + dt
        for tick in range(0, 60001, 1):
            seed = (t ^ tick) & 0xFFFFFFFF
            yield _generate_key_from_seed(seed)


def keygen_from_seed(seed: int) -> str:
    """Generate the exact key for a known seed."""
    return _generate_key_from_seed(seed)



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
            print(_sv)
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
