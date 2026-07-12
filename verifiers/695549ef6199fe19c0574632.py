def rol64(value: int, count: int) -> int:
    """Rotate left 64-bit value by count bits."""
    value &= 0xFFFFFFFFFFFFFFFF
    count %= 64
    if count == 0:
        return value
    return ((value << count) | (value >> (64 - count))) & 0xFFFFFFFFFFFFFFFF


def calculate_checksum(resolution: str) -> int:
    """
    Replicates the calculate_checksum() function from the binary.
    Algorithm:
      1. Initialize v3 = 2025
      2. For each character at index i (0-based):
         a. Multiply ASCII value by (i + 1)
         b. Add to v3
         c. Rotate left 64-bit result by 3
         d. XOR with 0x20262026
      3. Return v3 as unsigned 64-bit integer
    """
    v3 = 2025
    for i, ch in enumerate(resolution):
        v3 = rol64(v3 + (i + 1) * ord(ch), 3) ^ 0x20262026
    return v3


def verify(name: str, serial: str) -> bool:
    """
    Verify a (resolution, unlock_code) pair.
    'name' is the resolution string.
    'serial' is the unlock code as a string (decimal integer).
    """
    if not name:
        return False
    try:
        code = int(serial)
    except (ValueError, TypeError):
        return False
    expected = calculate_checksum(name)
    # The binary compares as signed 64-bit; handle negative serial values too
    # by interpreting expected as signed if needed
    expected_signed = expected if expected < (1 << 63) else expected - (1 << 64)
    return code == expected or code == expected_signed


def keygen(name: str) -> str:
    """
    Generate the correct unlock code for a given resolution string.
    Returns the code as a decimal string (unsigned 64-bit).
    """
    if not name:
        raise ValueError("Resolution must not be empty.")
    code = calculate_checksum(name)
    return str(code)



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
