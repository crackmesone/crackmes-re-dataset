def calculate_serial(name):
    """
    Part 1: Process name bytes by subtracting/adding CL (which starts at len and decrements).
    If result == 0x20, add CL back (undo the subtraction).
    This modifies the name buffer in place.
    """
    buf = list(name.encode('latin-1'))
    n = len(buf)
    ecx = n  # CL = length of name
    ebx = 0
    # INC DWORD PTR SS:[EBP-4] => stored_len = n + 1 (used later as loop bound)
    stored_len = n + 1

    while ecx != 0:
        val = (buf[ebx] - ecx) & 0xFF
        if val == 0x20:
            # ADD back CL
            val = (buf[ebx]) & 0xFF  # effectively buf[ebx] stays as-is after sub then add
            buf[ebx] = (buf[ebx] - ecx + ecx) & 0xFF  # = original
        else:
            buf[ebx] = val
        ebx += 1
        ecx -= 1
        # loop continues while ecx != 0

    # After loop, ebx points one past last processed char
    # DEC EBX: go back to last char
    ebx -= 1

    """
    Part 2: Walk backwards through buf, building the serial.
    For each byte:
      - if < 0x41: add 0x20
      - if > 0x5A: sub 0x20
    Insert '-' at position 4 (0-indexed).
    Loop until ecx == stored_len.
    """
    ecx = 0
    serial_bytes = []

    while True:
        eax = buf[ebx] & 0xFF
        if eax < 0x41:
            eax = (eax + 0x20) & 0xFF
        if eax > 0x5A:
            eax = (eax - 0x20) & 0xFF

        # At index 1 (second byte), the serial check increments EBX by 1
        # So the generated serial byte at position 1 needs to be incremented by 1
        # to match what the checker expects.
        # We handle this in verify/keygen by pre-incrementing position 1.

        serial_bytes.append(eax)
        ebx -= 1
        ecx += 1

        if ecx == 4:
            # Insert dash
            serial_bytes.append(0x2D)  # '-'
            ecx += 1

        if ecx == stored_len:
            break

    # serial_bytes[1] needs to be incremented by 1 because the checker does INC EBX
    # when ecx==1, meaning it compares entered_serial[1] with (calc_serial[1] + 1)
    # So the CORRECT serial has serial_bytes[1] + 1 at position 1
    serial_bytes[1] = (serial_bytes[1] + 1) & 0xFF

    return bytes(serial_bytes).decode('latin-1')


def verify(name, serial):
    if not name or len(name) < 5:
        return False
    if not serial:
        return False
    expected = keygen(name)
    return serial == expected


def keygen(name):
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")
    return calculate_serial(name)



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
