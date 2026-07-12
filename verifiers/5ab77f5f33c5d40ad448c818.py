import hashlib

def md5hex(name: str) -> str:
    """Return lowercase MD5 hex digest of the name (encoded as latin-1/bytes)."""
    return hashlib.md5(name.encode('latin-1')).hexdigest()

def verify(name: str, serial: str) -> bool:
    """Verify that serial matches the expected value for name."""
    if not name:
        return False
    expected = keygen(name)
    return serial == expected

def keygen(name: str) -> str:
    """
    Generate the serial for a given name.

    Algorithm (from solution writeups):
      1. Compute MD5 hex digest of the username (lowercase hex, 32 chars, 0-indexed).
      2. block1 = md5[4:10]   (chars at positions 5-10 in 1-based, 6 chars) -> lowercase
      3. block2 = md5[1:4].upper()  (chars at positions 2-4 in 1-based, 3 chars) -> uppercase
      4. block3 = md5[6:16]  (chars at positions 7-16 in 1-based, 10 chars) -> lowercase
      5. serial = block1 + block2 + block3

    Verified with known test vectors:
      name='r0ckstar' -> MD5='f9de12c19bc444b4c50e89b7567d67b7'
        block1 = md5[4:10]  = '12c19b'
        block2 = md5[1:4].upper() = '9DE'
        block3 = md5[6:16]  = 'c19bc444b4'
        serial = '12c19b9DEc19bc444b4'

      name='Adjiang' -> MD5='59b2bbc05ae348b9ccdadb932cce16df'
        block1 = md5[4:10]  = 'bbc05a'
        block2 = md5[1:4].upper() = '9B2'
        block3 = md5[6:16]  = 'c05ae348b9'
        serial = 'bbc05a9B2c05ae348b9'
    """
    if not name:
        return '-'
    h = md5hex(name)  # 32 lowercase hex chars, 0-indexed
    # 1-based Mid(h, 5, 6) => 0-based h[4:10]
    block1 = h[4:10]          # lowercase (already lowercase from md5hex)
    # 1-based Mid(h, 2, 3) => 0-based h[1:4], then UCase
    block2 = h[1:4].upper()   # uppercase
    # 1-based Mid(h, 7, 10) => 0-based h[6:16]
    block3 = h[6:16]          # lowercase
    return block1 + block2 + block3


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
