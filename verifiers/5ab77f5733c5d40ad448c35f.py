# Reverse-engineered key validation for KeyGenMe#1 by l0calh0st
# Based on the writeup by Taliesin (crackmes.de)
#
# What is confirmed from the writeup:
#   1. The program reads the name character by character.
#   2. Each character is zero-extended to a word (cbw/cwd) and accumulated
#      into a 32-bit (double-word) sum stored at [bp-06]:[bp-04].
#   3. After the loop, INT 35 is called with this sum -- INT 35 was hooked
#      by the program and represents the start of the serial generation/check.
#   4. The writeup is truncated before the serial algorithm is shown.
#
# ASSUMPTION: The serial is derived purely from the 32-bit sum of the ASCII
#             values of the name characters (confirmed), but the exact
#             transformation from that sum to the expected serial string is
#             NOT shown in the truncated writeup.  Everything below the
#             INT 35 call is unknown.
#
# ASSUMPTION: A common pattern for this era of crackme is to use the
#             32-bit sum directly, or multiply / XOR it, and format it
#             as a decimal or hexadecimal string.  We expose the sum and
#             leave the transformation as a placeholder.

def _name_sum(name: str) -> int:
    """Compute the 32-bit (truncated) sum of the ASCII values of 'name'.
    Matches the cbw/cwd + 32-bit accumulation loop seen in the disassembly.
    """
    total = 0
    for ch in name:
        # cbw: sign-extend byte to word (but printable ASCII is 0-127, so same as zero-extend)
        # cwd: sign-extend word to dword (same reason, upper word is 0)
        val = ord(ch) & 0xFF
        if val >= 0x80:          # sign-extend to 16-bit
            val |= 0xFF00
        val = val & 0xFFFF
        if val >= 0x8000:        # sign-extend to 32-bit
            val |= 0xFFFF0000
        total = (total + val) & 0xFFFFFFFF
    return total


def _serial_from_sum(s: int) -> str:
    """Convert the 32-bit name sum to a serial string.
    ASSUMPTION: The exact algorithm inside the hooked INT 35 handler is not
    shown in the truncated writeup.  A simple hex representation of the
    sum is used as a placeholder.  Replace with the real transform once known.
    """
    # ASSUMPTION: serial is the uppercase hex of the 32-bit sum, zero-padded to 8 chars.
    return '{:08X}'.format(s)


def verify(name: str, serial: str) -> bool:
    """Check whether 'serial' is valid for 'name'.
    ASSUMPTION: The comparison is a simple equality check against the
    generated serial (algorithm inside INT 35 handler unknown / truncated).
    """
    if not name:
        return False
    expected = _serial_from_sum(_name_sum(name))
    return serial.strip().upper() == expected.upper()


def keygen(name: str) -> str:
    """Generate a valid serial for 'name'.
    ASSUMPTION: Same as above -- the real INT 35 handler transform is unknown.
    """
    if not name:
        raise ValueError('Name must be non-empty')
    return _serial_from_sum(_name_sum(name))



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
