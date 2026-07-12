import struct

def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    Name must be at least 3 characters long.
    """
    # Sum all character byte values in the name
    name_sum = 0
    for ch in name:
        name_sum += ord(ch)

    # Multiply by 0xDEADBEEF, truncate to 32-bit (matches C uint32_t overflow)
    name_sum = (name_sum * 0xDEADBEEF) & 0xFFFFFFFF

    # Format as 8-character uppercase hex string
    hex_str = "{:08X}".format(name_sum)

    # Build serial in format K{0}{1}E-W{2}{3}L-S{4}{5}H-I{6}{7}T
    serial = "K{0}{1}E-W{2}{3}L-S{4}{5}H-I{6}{7}T".format(
        hex_str[0], hex_str[1],
        hex_str[2], hex_str[3],
        hex_str[4], hex_str[5],
        hex_str[6], hex_str[7]
    )
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify that the given serial matches the expected serial for the given name."""
    if len(name) < 3:
        return False
    expected = keygen(name)
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
