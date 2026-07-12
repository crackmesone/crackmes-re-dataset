import ctypes

SALT = "6789:;<=>?@ABCD"
POSTFIX = "-LEET"


def _get_serial_key(name: str) -> int:
    """
    Compute the signed 32-bit integer key from the username.
    Mirrors the assembly / keygen.cpp logic exactly.
    """
    key = 0

    for i, ch in enumerate(name):
        act = ord(ch)
        act *= (i + 1)
        act += (i + 1)
        # Shift amounts are masked to 5 bits on x86 (0xDE & 0x1F = 0x1E = 30,
        # 0xAD & 0x1F = 0x0D = 13)
        act = (act << (0xDE & 0x1F)) & 0xFFFFFFFF
        act = (act >> (0xAD & 0x1F)) & 0xFFFFFFFF
        act ^= (i + 1)
        act += 0x35
        act &= 0xFFFFFFFF
        key = (key + act) & 0xFFFFFFFF

    # key *= 0x39383736  (little-endian dword of "6789")
    key = (key * 0x39383736) & 0xFFFFFFFF

    # Interpret as signed 32-bit, then bitwise NOT
    key = ctypes.c_int32(key).value
    key = ~key
    return key


def _check_encrypted_values(key: int) -> str:
    """
    Convert the key integer to its decimal string representation,
    then apply the per-character XOR / adjustment described in keygen.cpp.
    """
    s = list(str(key))

    for i, ch in enumerate(s):
        base = ord(ch) & 0xFF
        act_enc = (base ^ 0xBE) & 0xFF

        if act_enc <= 0x8F:
            # No change needed
            pass
        elif act_enc == 0x93:
            # Replace with the '-' character encoding
            s[i] = chr(0x8D ^ 0xBE)
        else:
            # Decrement encrypted value and XOR back
            s[i] = chr(((act_enc - 1) ^ 0xBE) & 0xFF)

    return ''.join(s)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.
    Username must be 4-15 characters long.
    """
    if not (4 <= len(name) <= 15):
        raise ValueError("Username must be 4 to 15 characters long.")

    key = _get_serial_key(name)
    serial = _check_encrypted_values(key) + POSTFIX
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that the given serial is valid for the given username.
    """
    if not (4 <= len(name) <= 15):
        return False
    expected = keygen(name)
    return serial == expected


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

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
