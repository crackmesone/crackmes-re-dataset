def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be longer than 3 characters.
    """
    if len(name) <= 3:
        raise ValueError("Name must be greater than 3 characters")

    nln = len(name)
    # Convert each character to its integer (ASCII) value
    nnum = [ord(c) for c in name]

    # Build id array of 10 integers
    id_ = [0] * 10
    for i in range(255):
        id_[i % 10] = id_[i % 10] + (nnum[i % nln] ^ i)

    # Format each id entry as a 2-digit hex string (lowercase), concatenated
    hexid = "".join(format(num, 'x').zfill(2) for num in id_)
    # The C# code uses num.ToString("x2") which zero-pads to at least 2 hex digits
    # but for larger numbers it will be more than 2 chars; replicate that:
    hexid = "".join(format(num, 'x2') if num < 256 else format(num, 'x') for num in id_)
    # Actually replicate exactly: 'x2' in C# means lowercase hex, min 2 digits
    hexid = "".join(format(num, '02x') for num in id_)

    # Remove every other character starting at index 0 (i.e., remove even-indexed chars)
    # Original C#: for (i=0; i<hexid.Length; i+=2) { hexid = hexid.Remove(i,1); }
    # This removes char at position i each time, but after removal the string shrinks
    # Simulate exactly:
    hexid_list = list(hexid)
    i = 0
    while i < len(hexid_list):
        hexid_list.pop(i)
        i += 2
    hexid = "".join(hexid_list)

    # Build final serial: swap segments in reverse order
    # hexid.Substring(15,5) + "-" + hexid.Substring(10,5) + "-" + hexid.Substring(5,5) + "-" + hexid.Substring(0,5)
    part0 = hexid[0:5]
    part1 = hexid[5:10]
    part2 = hexid[10:15]
    part3 = hexid[15:20]
    serial = part3 + "-" + part2 + "-" + part1 + "-" + part0
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that the serial matches the one generated for the given name.
    """
    if len(name) <= 3:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
    return serial.strip() == expected.strip()



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
