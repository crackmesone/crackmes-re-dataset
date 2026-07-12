import hashlib

def generate_segment(input_string: str) -> str:
    """Reproduce the C# GenerateSegment method using SHA-256."""
    sha = hashlib.sha256()
    sha.update(input_string.encode('utf-8'))
    buf = sha.digest()
    result = []
    for i in range(2):
        num2 = buf[i] % 0x24       # buf[0] % 36, buf[1] % 36
        num3 = buf[i + 2] % 0x24  # buf[2] % 36, buf[3] % 36
        ch  = chr(0x30 + num2)       if num2 < 10 else chr(0x41 + (num2 - 10))
        ch2 = chr(0x30 + num3)       if num3 < 10 else chr(0x41 + (num3 - 10))
        result.append(ch)
        result.append(ch2)
    return ''.join(result)


def keygen(name: str) -> str:
    """Generate the serial key (three 4-char segments joined by '-') for the given username."""
    if len(name) < 4:
        raise ValueError("Username must be at least 4 characters long.")
    seg1 = generate_segment(name)
    seg2 = generate_segment(name + "salt1")
    seg3 = generate_segment(name + "salt2")
    return f"{seg1}-{seg2}-{seg3}"


def verify(name: str, serial: str) -> bool:
    """Verify a serial key against the given username."""
    if not name or len(name) < 4:
        return False
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    str2, str3, str4 = parts
    # Each segment must be at least 3 characters (the crackme checks Length < 3)
    if len(str2) < 3 or len(str3) < 3 or len(str4) < 3:
        return False
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
