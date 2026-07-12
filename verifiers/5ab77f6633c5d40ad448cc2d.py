def keygen(name: str) -> str:
    """
    Reconstruct the serial from the VB source code provided in solution 2.
    The algorithm is taken directly from solution.vb by MACH4.
    """
    if len(name) == 0:
        raise ValueError("Name must not be empty")

    counter1 = 1
    esi = 0.0
    ebp30 = 0.0
    n = len(name)

    # First iteration uses esi = 0 (goto start2 skips the ebp30*2 step)
    first = True
    while True:
        if not first:
            counter1 += 1
            if counter1 > n:
                break
            esi = ebp30 * 2
        first = False

        # start2:
        char_val = ord(name[counter1 - 1])  # Asc(Mid(name, counter1, 1))
        esi = esi + (-5708) + (char_val * 123) + (n * 2 + 4266)
        temp = esi + 5363763
        esi = 55677
        temp = temp + esi + 151413
        ebp30 = temp

    # done:
    # Text2.Text = Hex(temp) & (counter1 - 1)
    # In VB, Hex() of a floating point converts the integer part to hex (uppercase)
    # counter1 - 1 == len(name) at this point
    int_temp = int(temp)
    # VB Hex() on a negative number returns the two's-complement hex (8 hex digits for 32-bit)
    # But since temp can be large, we replicate VB6 Hex() behavior:
    # VB6 Hex() treats the value as a Long (32-bit signed) if it fits, else Double
    # For simplicity, mask to 32 bits unsigned (VB6 Hex on a Long)
    # ASSUMPTION: VB Hex() here wraps to 32-bit unsigned representation
    masked = int_temp & 0xFFFFFFFF
    hex_part = format(masked, 'X')  # uppercase hex, no leading zeros (VB6 behavior)
    serial = hex_part + str(counter1 - 1)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair by regenerating the serial and comparing.
    """
    if not name:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
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
