def verify_level3(name: str, serial: str) -> bool:
    """Level 3 serial check."""
    hash2 = 0.0
    for ch in name:
        num1 = ord(ch)
        hash1 = num1 ** 2
        hash1 = hash1 * 17
        hash1 = hash1 - 42
        tmp = 3.0 ** 3.0
        tmp = tmp * hash1 * 12
        hash2 = hash2 + tmp + 29421
    expected = str(int(hash2)) if hash2 == int(hash2) else str(hash2)
    return serial.strip() == expected.strip()


def keygen_level3(name: str) -> str:
    """Generate Level 3 serial for a given name."""
    hash2 = 0.0
    for ch in name:
        num1 = ord(ch)
        hash1 = num1 ** 2
        hash1 = hash1 * 17
        hash1 = hash1 - 42
        tmp = 3.0 ** 3.0  # 27.0
        tmp = tmp * hash1 * 12
        hash2 = hash2 + tmp + 29421
    # VB CStr on a Double: represent as integer if whole number
    if hash2 == int(hash2):
        return str(int(hash2))
    return str(hash2)


def verify_level4(name: str, serial: str) -> bool:
    """Level 4 serial check."""
    return serial.strip() == keygen_level4(name).strip()


def keygen_level4(name: str) -> str:
    """Generate Level 4 serial for a given name."""
    hash2 = 0.0
    for ch in name:
        num1 = ord(ch)
        hash1 = num1 ** 4.45354345543454
        hash1 = hash1 * 1778676.89547349
        # ASSUMPTION: 153# + 0.9380400258997 = 153.9380400258997
        R8temp = 3.0 ** (153.0 + 0.9380400258997)
        R8temp = R8temp * hash1
        R8temp = R8temp / 76.7677686786689
        hash2 = hash2 + R8temp

    str_hash = str(hash2)
    # VB: strip last 4 chars, then strip first 2 chars of result
    hash_len = len(str_hash)
    hash_len = hash_len - 4
    str_hash = str_hash[:hash_len]  # Left(strHash, hashLen)
    hash_len = len(str_hash)
    hash_len = hash_len - 2
    str_hash = str_hash[hash_len:]  # Right(strHash, hashLen) -- take last hashLen chars
    # ASSUMPTION: Right(strHash, hashLen) in VB returns the RIGHTMOST hashLen characters
    return str_hash


def verify(name: str, serial: str) -> bool:
    """Try both level 3 and level 4 verification."""
    return verify_level3(name, serial) or verify_level4(name, serial)


def keygen(name: str) -> str:
    """Return Level 3 serial (most straightforward)."""
    return keygen_level3(name)



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
