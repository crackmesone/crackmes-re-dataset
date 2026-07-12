# keygenme_3 by hmx0101
# Reconstructed from solution writeup (Delphi Pascal source embedded in writeup)
# The writeup contains a Pascal function MakeKey(Name: String): String
# Core algorithm recovered from the Pascal pseudocode in the writeup.

def make_key(name: str) -> str:
    """
    Reconstructed MakeKey function from the Pascal source in the writeup.
    Name must be at least 5 characters.
    """
    length = len(name)
    if length < 5:
        raise ValueError('Name must be at least 5 characters')

    Sum1 = 0
    Sum2 = 0
    Sum3 = 0
    Sum4 = 0

    for Index in range(1, length + 1):  # 1-based Pascal loop
        c = ord(name[Index - 1])
        Sum1 += c + (length - 0)
        Sum2 += c + (length - 1)  # // Delphi String Format!!
        Sum3 += c + (length - 2)
        Sum4 += c + (length - 3)

    # Build a 20-byte array (indices $00..$13 in Pascal, 0-based here)
    SArray = [0] * 0x1A  # enough slots

    # Group 1: Sum1 xor constants -> SArray[0x00..0x04]
    SArray[0x00] = Sum1 ^ 0x90
    SArray[0x01] = Sum1 ^ 0xFF
    SArray[0x02] = Sum1 ^ 0x90
    SArray[0x03] = Sum1 ^ 0xFF
    SArray[0x04] = Sum1 ^ 0x0F

    # Group 2: Sum2 xor constants -> SArray[0x05..0x09]
    SArray[0x05] = Sum2 ^ 0x58
    SArray[0x06] = Sum2 ^ 0x44
    SArray[0x07] = Sum2 ^ 0x43
    SArray[0x08] = Sum2 ^ 0x56
    SArray[0x09] = Sum2 ^ 0x23

    # Group 3: Sum3 xor constants -> SArray[0x0A..0x0F]
    SArray[0x0A] = Sum3 ^ 0x55
    SArray[0x0B] = Sum3 ^ 0x44
    SArray[0x0C] = Sum3 ^ 0x64
    SArray[0x0D] = Sum3 ^ 0x57
    SArray[0x0E] = Sum3 ^ 0x45
    SArray[0x0F] = Sum3 ^ 0x95

    # Mixed entries using combinations
    SArray[0x10] = Sum1 ^ Sum4
    SArray[0x11] = Sum2 ^ Sum4
    SArray[0x12] = Sum3 ^ Sum4
    SArray[0x13] = (Sum1 + Sum2) ^ Sum4
    SArray[0x14] = (Sum2 + Sum3) ^ Sum4

    # Entries derived from individual name chars xor 0x44
    SArray[0x15] = ord(name[1]) ^ 0x44  # name[2] in Pascal (1-based)
    SArray[0x16] = ord(name[2]) ^ 0x44
    SArray[0x17] = ord(name[3]) ^ 0x44
    SArray[0x18] = ord(name[4]) ^ 0x22
    SArray[0x19] = ord(name[5 - 1]) ^ 0x11  # name[5], 0-based: name[4]

    # ASSUMPTION: The serial is built by converting each SArray entry to string and concatenating
    # The writeup shows IntToStr calls and concatenation into StrResult
    # The final serial covers indices 0x00..0x19 (26 entries)
    StrResult = ''
    for i in range(0x1A):
        StrResult += str(SArray[i])

    return StrResult


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: The check simply compares the generated key to the provided serial.
    """
    if len(name) < 5:
        return False
    try:
        expected = make_key(name)
    except Exception:
        return False
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    if len(name) < 5:
        raise ValueError('Name must be at least 5 characters')
    return make_key(name)



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
