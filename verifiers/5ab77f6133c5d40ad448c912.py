import ctypes

def _compute_hash(name: str) -> int:
    """
    Compute the hash for a given name using the algorithm extracted from the crackme.
    Initial value: 0x1908
    For each character in name:
        hash = (hash + len(name)) * ord(char)
    Final XOR with 0xA9F9FA
    Result is treated as unsigned 32-bit integer.
    """
    length = len(name)
    h = 0x1908
    for ch in name:
        h = (h + length) * ord(ch)
        # Keep as 32-bit signed (IMUL in x86 truncates to 32 bits)
        h = ctypes.c_int32(h).value
    h = ctypes.c_uint32(h ^ 0x0A9F9FA).value
    return h


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Requirements:
      - Name must be longer than 4 characters (len > 4)
      - Serial (entered as a decimal string) must equal the computed hash
    The original crackme compares atoi(serial) with the computed hash value.
    The serial is stored/displayed as an unsigned decimal number (via %lu / IntToStr),
    but comparison is done after XOR which may produce a value that, as a signed 32-bit
    int, could be negative. Multiple solutions show it printed as unsigned cardinal.
    We accept both signed and unsigned decimal representations.
    """
    if len(name) <= 4:
        return False
    computed = _compute_hash(name)
    # Try matching as unsigned 32-bit
    try:
        entered = int(serial)
    except ValueError:
        return False
    # Accept both unsigned and signed interpretations
    computed_signed = ctypes.c_int32(computed).value
    return entered == computed or entered == computed_signed


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Returns the serial as an unsigned decimal string (matches the keygen's %lu / cardinal output).
    Name must be more than 4 characters.
    """
    if len(name) <= 4:
        raise ValueError('Name must be more than 4 characters long.')
    computed = _compute_hash(name)
    return str(computed)



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
