import ctypes

def keygen(name: str) -> str:
    """
    For each character at index i in name:
        key_byte = (2 * ord(char) >> 2) + (i >> 2) - 0xC8
    taken as a signed 8-bit value (via arithmetic right shift / sign extension),
    then stored as a byte (truncated to 8 bits).
    """
    result = []
    for i, ch in enumerate(name):
        val = (2 * ord(ch) >> 2) + (i >> 2) - 0xC8
        # Truncate to 8-bit signed (like the assembly does with SAR + MOVSX AL)
        val = val & 0xFF
        if val > 127:
            val -= 256
        result.append(chr(val & 0xFF))
    return ''.join(result)


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the keygen output for name.
    The serial is a string of bytes derived from the name.
    We compare byte-by-byte.
    """
    expected = keygen(name)
    if len(serial) != len(name):
        return False
    for i in range(len(name)):
        # Compare the low 8 bits of each character
        if (ord(serial[i]) & 0xFF) != (ord(expected[i]) & 0xFF):
            return False
    return True



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
