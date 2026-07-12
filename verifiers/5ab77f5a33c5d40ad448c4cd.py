def _process_char(car, i):
    """Apply the normalization steps to a computed character value."""
    # Step 1: Divide by 3 while > 0x7A ('z')
    while car > 0x7A:
        car //= 3

    # Step 2: Add (i*2 + 1) while < 0x30 ('0')
    while car < 0x30:
        car += (i * 2) + 1

    # Step 3: If in gap between '9' and 'A' (0x39 < car < 0x41), subtract 8
    if car > 0x39 and car < 0x41:
        car -= 0x08

    # Step 4: If in gap between 'Z' and 'a' (0x5A < car < 0x61), subtract 7
    if car > 0x5A and car < 0x61:
        car -= 0x07

    return car


def _process_char_second(car, i):
    """Apply normalization for the second cycle (padding with 'a')."""
    # Step 1: Divide by 3 while > 0x7A
    while car > 0x7A:
        car //= 3

    # Step 2: Add 0x0F while < 0x30
    # ASSUMPTION: The second cycle uses a flat +0x0F increment (from C source), not (i*2+1)
    while car < 0x30:
        car += 0x0F

    # Step 3: If in gap between '9' and 'A', subtract 8 and skip step 4
    if car > 0x39 and car < 0x41:
        car -= 0x08
        return car

    # Step 4: If in gap between 'Z' and 'a', subtract 7
    if car > 0x5A and car < 0x61:
        car -= 0x07

    return car


# From C source: fixed suffix string appended after keygen logic
_SUFFIX = b"v8E259a"


def keygen(name):
    """Generate a valid serial for the given name."""
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    length = len(name_bytes)

    # Name must be 5..15 characters
    if length < 5 or length > 15:
        raise ValueError("Name must be between 5 and 15 characters")

    serial = bytearray(16)

    # First cycle: process each character of the name
    for i in range(length):
        tmp = i + 2
        car = tmp * name_bytes[i]
        car = _process_char(car, i)
        serial[i] = car

    # Second cycle: fill remaining positions (up to 16) using 0x61 ('a')
    for c in range(length, 16):
        i = c
        tmp = i + 2
        car = tmp * 0x61
        car = _process_char_second(car, i)
        serial[c] = car

    # Overlay the fixed suffix string based on name length
    # From C source:
    # if len < 9: serial[9..15] = "v8E259a"
    # else: serial[len..len+7] = string[(len-9):(len-9+7)]
    if length < 9:
        for i in range(7):
            serial[9 + i] = _SUFFIX[i]
    else:
        for i in range(7):
            idx = (length - 9) + i
            if idx < len(_SUFFIX):
                serial[length + i] = _SUFFIX[idx]

    serial[15] = 0  # null-terminate at index 15 (serial is 15 chars)
    return serial[:15].decode('latin-1')


def verify(name, serial):
    """Verify that the serial matches the expected serial for the given name."""
    try:
        expected = keygen(name)
    except ValueError:
        return False
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
