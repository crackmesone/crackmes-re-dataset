def keygen(name: str) -> str:
    """
    Generate the serial for a given username.
    The algorithm is fully described by multiple solutions.
    """
    if len(name) < 4:
        raise ValueError("Username must be at least 4 characters long")

    # Constant magic string from the crackme
    MAGIC = "_r <()<1-Z2[l5,^"
    magic_len = len(MAGIC)  # 16

    # Initialize key buffer with magic string bytes
    key = list(MAGIC)

    name_len = len(name)

    # Loop runs for max(len(name), len(MAGIC)) iterations
    upper_bound = max(name_len, magic_len)

    for i in range(upper_bound):
        a = i % magic_len     # index into key buffer (string2)
        b = i % name_len      # index into username

        char_name = ord(name[b])
        char_key  = ord(key[a])

        result = (char_name ^ char_key) % 0x19
        result += 0x41  # 'A'

        key[a] = chr(result)

    serial = ''.join(key)
    return serial[0:4] + '-' + serial[4:8] + '-' + serial[8:12] + '-' + serial[12:16]


def verify(name: str, serial: str) -> bool:
    """
    Verify that the serial matches the one generated for the given username.
    """
    if len(name) < 4:
        return False
    try:
        expected = keygen(name)
    except ValueError:
        return False
    # Normalize: remove dashes for comparison just in case
    return serial.upper() == expected.upper()



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
