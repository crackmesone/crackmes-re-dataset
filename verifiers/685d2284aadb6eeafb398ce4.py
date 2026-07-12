import ctypes

def boozhash(username: str) -> int:
    """
    Custom hash function as described in the crackme solutions.
    Based on assembly + C# + C++ implementations provided.
    """
    # Convert to lowercase first (main routine does str_tolower before calling boozhash,
    # but boozhash also calls tolower on each char - we do both for safety)
    s = username.lower()
    
    # Use 32-bit unsigned arithmetic via masking
    MASK = 0xFFFFFFFF
    
    h = 0
    for c in s:
        v2 = ord(c)  # already lowercase
        # add char value to hash
        h = (h + v2) & MASK
        # hash += (hash << 10)  =>  hash *= 1025
        h = (h + (h << 10)) & MASK
        # hash ^= (hash >> 6)
        h = (h ^ (h >> 6)) & MASK
    
    # Final mixing steps
    # hash += (hash << 3)  =>  hash *= 9
    h = (h + (h << 3)) & MASK
    # hash ^= (hash >> 11)
    h = (h ^ (h >> 11)) & MASK
    # hash += (hash << 15)  =>  hash *= 32769
    h = (h + (h << 15)) & MASK
    
    return h


def verify(name: str, serial: str) -> bool:
    """
    Verify a (username, serial) pair.
    Serial is expected as an uppercase or lowercase hex string (e.g. 'BE34A10D').
    The program reads the password with %x (scanf hex), so it's a hex value.
    """
    try:
        serial_int = int(serial, 16)
    except ValueError:
        return False
    
    expected = boozhash(name.lower())
    return (serial_int & 0xFFFFFFFF) == expected


def keygen(name: str) -> str:
    """
    Generate the correct serial (password) for a given username.
    Returns an uppercase 8-character hex string.
    """
    h = boozhash(name.lower())
    return f"{h:08X}"



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
