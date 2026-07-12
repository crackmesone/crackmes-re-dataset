def level1_serial(name: str) -> str:
    # Sum of ASCII decimal values of each character in name
    total = sum(ord(c) for c in name)
    return str(total)


def level2_serial(name: str) -> str:
    # Concatenation of ASCII hex values (uppercase, 2 digits) of each character
    return ''.join(f'{ord(c):02X}' for c in name)


def level3_serial(name: str) -> str:
    # Each byte's hex digits are reversed (nibbles swapped), then '26' is inserted between each
    # From the writeup: '43616C63756C696369' reversed per byte gives '34 16 C6 36 75 6C 69 63 69'
    # Wait, let's re-read: '34 16 C6 36 57 C6 96 36 96' with '26' interspersed
    # The full level3 serial shown: '2634261626C62636265726C6269626362696'
    # Breaking it: 26 34 26 16 26 C6 26 36 26 57 26 C6 26 96 26 36 26 96
    # So '26' is prepended before each reversed-nibble byte
    # Reversed nibbles: swap high and low nibble of ASCII value
    # e.g. 'C' = 0x43 -> reversed nibbles = 0x34
    # 'a' = 0x61 -> reversed nibbles = 0x16
    # 'l' = 0x6C -> reversed nibbles = 0xC6
    # 'c' = 0x63 -> reversed nibbles = 0x36
    # 'u' = 0x75 -> reversed nibbles = 0x57
    # 'l' = 0x6C -> reversed nibbles = 0xC6
    # 'i' = 0x69 -> reversed nibbles = 0x96
    # 'c' = 0x63 -> reversed nibbles = 0x36
    # 'i' = 0x69 -> reversed nibbles = 0x96
    # So serial = '26' + ''.join('26' + reversed_nibble_hex for each char)
    # But that gives '26' + 26+34 + 26+16 + ... = '262634261626C6...' which matches!
    # ASSUMPTION: The leading '26' is a fixed prefix, then each char produces '26' + swapped-nibble hex
    parts = []
    for c in name:
        val = ord(c)
        high = (val >> 4) & 0xF
        low = val & 0xF
        swapped = (low << 4) | high
        parts.append(f'{swapped:02X}')
    serial = '26' + '26'.join(parts)
    return serial


def keygen(name: str):
    """Returns (level1, level2, level3) serials for the given name."""
    return (
        level1_serial(name),
        level2_serial(name),
        level3_serial(name),
    )


def verify(name: str, serial: str, level: int = 1) -> bool:
    """
    Verify a serial for a given name and level (1, 2, or 3).
    """
    if level == 1:
        expected = level1_serial(name)
        return serial.strip() == expected
    elif level == 2:
        expected = level2_serial(name)
        return serial.strip().upper() == expected.upper()
    elif level == 3:
        expected = level3_serial(name)
        return serial.strip().upper() == expected.upper()
    return False



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
