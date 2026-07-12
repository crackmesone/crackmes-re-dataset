import math

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 8:
        return "min 8 chars"

    # Constants from the VB source (treated as unsigned 32-bit via masking)
    var1 = 3134320653  # 0xBAD1F00D
    var2 = 283028737   # 0x10DEAD01
    var3 = 269532911   # 0x1010BEEF
    var4 = 268548816   # 0x1001BAD0

    name_len = len(name)

    # Last character (VB Mid(text, Len, Len) returns the last char)
    last_char = ord(name[-1])
    # First character
    first_char = ord(name[0])

    # temp1: based on last char
    temp1 = last_char * 123
    temp1 = temp1 ^ var1
    temp1 = temp1 ^ (name_len * 321)
    temp1 = temp1 ^ var4

    # temp2: based on first char
    temp2 = first_char * 123
    temp2 = temp2 ^ var3
    temp2 = temp2 ^ (name_len * 321)
    temp2 = temp2 ^ var2
    temp2 = temp2 ^ 16843009  # 0x01010101

    # pass = temp1 + temp2 + last_char
    # Note: VB Long is 64-bit signed, but the hex output may wrap;
    # we replicate VB Long arithmetic (no overflow concern for these values)
    pass_val = temp1 + temp2 + last_char

    # namecalc: index into name for the middle segment
    # VB: namecalc = (Len - 6) / 2, then CInt(Fix(...))
    namecalc = math.trunc((name_len - 6) / 2)  # Fix() truncates toward zero

    # VB Mid(text, namecalc, 6): 1-based index, 6 chars
    # namecalc can be 0 or 1; VB Mid with start=0 treats it as 1
    vb_start = max(namecalc, 1)  # VB Mid clamps start < 1 to 1
    mid_segment = name[vb_start - 1: vb_start - 1 + 6]

    # Hex(pass_val) in VB: uppercase hex, no '0x' prefix
    # For negative VB Long values, VB Hex returns the two's complement representation
    # VB Long is 64-bit, so mask to 64-bit signed
    if pass_val < 0:
        # Two's complement 64-bit
        hex_pass = format(pass_val & 0xFFFFFFFFFFFFFFFF, 'X')
    else:
        hex_pass = format(pass_val, 'X')

    # StrReverse the hex string
    reversed_hex = hex_pass[::-1]

    serial = f"L-{name_len}-{mid_segment}-{reversed_hex}"
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify a serial for a given name."""
    expected = keygen(name)
    if expected == "min 8 chars":
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
