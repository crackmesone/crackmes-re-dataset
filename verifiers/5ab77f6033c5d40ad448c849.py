import ctypes
import struct

def compute_serial_part1(name):
    """
    Key1 proc logic:
    - Iterate over first 17 bytes of NameBuffer (padded with zeros)
    - For each byte: al = byte; al *= 0x0B; ror al 2 bits (32-bit); al ^= 0x38; al += 0x7A5
    - Accumulate sum in ebx
    - Then: eax = 0x0C * ebx * 2 ^ 0x36, rotated left 7 bits (32-bit)
    """
    # Pad name to 17 bytes (NameBuffer is zero-initialized)
    name_bytes = name.encode('latin-1', errors='replace')
    # NameBuffer is 100 bytes, zero-initialized; we read exactly 17 bytes
    buf = bytearray(100)
    for i, b in enumerate(name_bytes[:100]):
        buf[i] = b

    ebx = 0
    for edi in range(17):
        al = buf[edi]
        eax = (al * 0x0B) & 0xFFFFFFFF
        # ror eax, 2 (32-bit)
        eax = ((eax >> 2) | (eax << 30)) & 0xFFFFFFFF
        eax = (eax ^ 0x38) & 0xFFFFFFFF
        eax = (eax + 0x7A5) & 0xFFFFFFFF
        ebx = (ebx + eax) & 0xFFFFFFFF

    # mov eax, 0Ch; mul ebx  -> eax = (0x0C * ebx) & 0xFFFFFFFF (low 32 bits)
    eax = (0x0C * ebx) & 0xFFFFFFFF
    # imul eax, eax, 2
    eax = (eax * 2) & 0xFFFFFFFF
    # xor eax, 36h
    eax = (eax ^ 0x36) & 0xFFFFFFFF
    # rol eax, 7 (32-bit)
    eax = ((eax << 7) | (eax >> 25)) & 0xFFFFFFFF

    # wsprintf uses signed %d
    # Convert to signed 32-bit
    if eax >= 0x80000000:
        eax_signed = eax - 0x100000000
    else:
        eax_signed = eax

    return eax_signed


def verify(name, serial):
    """
    The serial format is "%d-%d" where:
    - First %d is computed from the name via Key1
    - Second %d is the 'magic number' (mNum) entered by the user in IDC_EDIT1013
    The keygen simply formats the serial as computed_value-magic_number.
    We can verify the first part; the second part is a user-supplied magic number.
    """
    # Name must be 5..40 chars
    if len(name) < 5 or len(name) > 40:
        return False

    parts = serial.split('-')
    if len(parts) != 2:
        return False

    try:
        serial_part1 = int(parts[0])
        # parts[1] is the magic number - we cannot verify it without the original crackme
        int(parts[1])  # must be an integer
    except ValueError:
        return False

    expected_part1 = compute_serial_part1(name)
    return serial_part1 == expected_part1


def keygen(name, magic_number=0):
    """
    Generate serial for given name.
    magic_number is the 'M#' field from the crackme (user-supplied; we default to 0).
    # ASSUMPTION: magic_number is whatever integer the user enters in the crackme's M# field.
    # The real crackme requires running Magic.exe to obtain the magic number.
    Serial format: "%d-%d" % (computed_value, magic_number)
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")
    if len(name) > 40:
        raise ValueError("Name must be at most 40 characters")

    part1 = compute_serial_part1(name)
    return f"{part1}-{magic_number}"



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
