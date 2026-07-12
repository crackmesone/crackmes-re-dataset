import ctypes

def _to_int32(val):
    """Truncate to signed 32-bit integer."""
    return ctypes.c_int32(val).value

def _to_uint32(val):
    """Truncate to unsigned 32-bit integer."""
    return ctypes.c_uint32(val).value


def _compute_code(name):
    """
    Code generation algorithm from the writeup:

    1. al = first byte of username  (name[0])
    2. edx = al + 0x3B9ACA00
    3. eax = al * len(name)          (IMUL EAX, [LOCAL.6])
    4. eax = eax * edx               (IMUL EAX, EDX)
    5. code = eax  (signed 32-bit)
    6. while code < 0: code += 0x3B9ACA00

    NOTE: 'al' is the low byte of eax which was loaded from localbuff
    (first char of username). The writeup shows:
        mov al, byte ptr [localbuff]   ; first char of username
        lea edx, [eax+3B9ACA00h]       ; edx = al + 0x3B9ACA00
        imul eax, dword ptr [localbuff2]; eax = al * username_length
        imul eax, edx                   ; eax = eax * edx
    All arithmetic is 32-bit signed/truncated.
    """
    if not name:
        return 0

    name_len = len(name)
    al = ord(name[0]) & 0xFF          # low byte of first char

    # ASSUMPTION: eax starts as al (zero-extended to 32 bits) before the sequence
    eax = al
    edx = _to_int32(eax + 0x3B9ACA00)

    eax = _to_int32(eax * name_len)   # IMUL EAX, [LOCAL.6]
    eax = _to_int32(eax * edx)        # IMUL EAX, EDX

    code = eax
    # Loop: while code < 0: code += 0x3B9ACA00
    while code < 0:
        code = _to_int32(code + 0x3B9ACA00)

    return code


def _compute_serial(code, name_len):
    """
    Serial generation algorithm from the writeup:

    1. eax = code
    2. eax = eax * name_len           (IMUL EAX, [LOCAL.6])
    3. eax = eax * 0x3E7              (IMUL EAX, EAX, 3E7h)
    4. local.10 = eax
    5. while local.10 < 0: local.10 += 0x3B9ACA00
    """
    eax = _to_int32(code)
    eax = _to_int32(eax * name_len)   # IMUL EAX, [LOCAL.6]
    eax = _to_int32(eax * 0x3E7)      # IMUL EAX, EAX, 3E7h

    serial_val = eax
    while serial_val < 0:
        serial_val = _to_int32(serial_val + 0x3B9ACA00)

    return serial_val


def keygen(name):
    """
    Generate a valid serial for the given username.
    The username must be < 12 characters (as noted: local.6 < 12).
    Returns the serial as a decimal string.
    """
    # ASSUMPTION: username length must be between 1 and 11 inclusive
    if not name or len(name) >= 12:
        raise ValueError("Username must be 1-11 characters long")

    code = _compute_code(name)
    serial = _compute_serial(code, len(name))
    return str(serial)


def verify(name, serial):
    """
    Verify whether the serial is valid for the given username.
    Compares the computed serial (as a string) against the provided serial.
    """
    if not name or len(name) >= 12:
        return False
    try:
        user_serial = int(serial)
    except ValueError:
        return False

    expected = int(keygen(name))
    return user_serial == expected



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
