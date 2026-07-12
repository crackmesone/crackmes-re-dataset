# Reconstruction of nonzenze's keygenme #1
# Based on the assembly snippet described in the solution writeup.
#
# The writeup (after decoding the garbled text) describes the validation routine
# at offset 0x004011D8 and nearby. The key instructions described are:
#
#   00401188 |. 8AC1          MOV AL, CL
#   0040118B |. 0FCB           BSWAP EBX
#   00401191 |. 03D8           ADD EBX, EAX
#   00401193 |. FE85 E7FDFFFF  INC BYTE PTR SS:[EBP-219]
#   00401199 |. 51             PUSH ECX
#   0040119A |. 8A85 A8DE F7DF FF | MOV CL, BYTE PTR SS:[EBP-219]
#   004011A0 |. 3B8D ECFDFFFF  CMP ECX, DWORD PTR SS:[EBP-214]
#   004011A6 |. 59             POP ECX
#   004011A7 |. 41             INC ECX
#   004011A8 |. ^72 E3         JB SHORT keygenme.004011D8 (loop back)
#
# And the trigger/check:
#   00401168 |. F7F3           DIV EBX
#
# The writeup says:
# - Name must have 5 OR MORE chars
# - Serial must be LONG 8 CHARS
# - The algorithm loops over name bytes, doing: BSWAP of accumulator, then
#   ADD the current name byte, INC a counter, loop until counter >= name_length
# - The final value is used in a DIV EBX check
#
# The keygen source (kgmDlg.cpp, not fully provided) likely implements:
#   acc = 0
#   for each byte c in name:
#       acc = bswap32(acc)
#       acc = (acc + c) & 0xFFFFFFFF
#   serial = format that acc as 8 hex chars

def bswap32(v):
    """Byte-swap a 32-bit integer."""
    v = v & 0xFFFFFFFF
    return ((v & 0xFF) << 24) | (((v >> 8) & 0xFF) << 16) | (((v >> 16) & 0xFF) << 8) | ((v >> 24) & 0xFF)

def compute_serial_value(name):
    """Compute the serial value from the name using the described loop."""
    acc = 0
    for c in name:
        acc = bswap32(acc)
        acc = (acc + ord(c)) & 0xFFFFFFFF
    return acc

def keygen(name):
    """Generate a serial for the given name.
    Name must be at least 5 characters; serial is 8 hex chars.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")
    val = compute_serial_value(name)
    # ASSUMPTION: serial is the hex representation of the computed value, uppercase, 8 chars
    return "{:08X}".format(val)

def verify(name, serial):
    """Verify a name/serial pair."""
    if len(name) < 5:
        return False
    if len(serial) != 8:
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
