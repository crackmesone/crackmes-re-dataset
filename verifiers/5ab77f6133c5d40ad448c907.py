import struct

def compute_serial(name, code=0x000005D4):
    """
    Reconstruct the serial validation algorithm from the writeup.
    
    From the disassembly:
    - 'code' is a DWORD (initially loaded from ESI+26C, seeded from random)
    - For each character in name:
        1. XOR current byte of 'code' (low byte of EBX) with name[i]
        2. Shift code right by 8 bits for next iteration
        3. If code becomes 0, reload original code
        4. Also maintain a running sum of name chars (sum)
        5. Also maintain a running product of name chars (product, using IMUL EBP)
    
    The writeup is truncated, so the exact serial format is partially reconstructed.
    """
    # ASSUMPTION: code is the DWORD at ESI+60 which is 0x5D4 = 1492
    # This is stored as part of the object. We use it as the XOR key.
    code_orig = code
    ebx = code

    xored_name = []
    char_sum = 0
    char_product = 1  # EBP starts at 1 (ASSUMPTION)

    for i, ch in enumerate(name):
        ch_val = ord(ch)

        # If code has been shifted to 0, reload original
        if ebx == 0:
            ebx = code_orig

        # XOR low byte of code with name char
        dl = (ebx & 0xFF) ^ ch_val
        xored_name.append(dl)

        # Shift code right by 8 for next character
        ebx = ebx >> 8

        # Running sum and product of name chars
        char_sum = (char_sum + ch_val) & 0xFFFFFFFF
        char_product = (char_product * ch_val) & 0xFFFFFFFF

    # ASSUMPTION: serial is derived from xored_name bytes formatted as hex
    # The writeup shows the XOR of code bytes with name chars, but the
    # exact serial format (how xored bytes become the serial string) is truncated.
    # Common pattern: serial = hex digits of xored bytes concatenated,
    # possibly with sum/product appended.
    serial_bytes = xored_name
    serial = ''.join('{:02X}'.format(b) for b in serial_bytes)
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: Serial is compared against compute_serial(name) output.
    The writeup is truncated and does not show the final comparison,
    so this is a partial reconstruction.
    """
    if not name or not serial:
        return False
    expected = compute_serial(name)
    # ASSUMPTION: case-insensitive comparison
    return serial.upper() == expected.upper()


def keygen(name):
    """
    Generate a serial for the given name.
    """
    return compute_serial(name)



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
