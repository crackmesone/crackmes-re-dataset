# Reverse-engineered keygen for imp's Keygen#1
# Based on the writeup by Zaphod
#
# What we know from the writeup:
# 1. Name must be >= 5 characters
# 2. First char must be a letter (A-Z or a-z)
# 3. Remaining chars can be: A-Z, a-z, 0-9, . - _ @
# 4. Serial buffer is at 4031CD (16 bytes, indices 0-15)
# 5. The check at 4013BE-4013C6:
#      for ecx in range(15, -1, -1):
#          dl = serial_byte[ecx]
#          dl += 1
#          if dl != 0: jump to 4013DE (INC EAX, DEC EDX)
#    => For the "good" path, every serial byte incremented must wrap to 0,
#       meaning every serial byte must be 0xFF.
#    But that's only the wrap-around loop path. The writeup says
#    the program loops 16 times and ends at 4013D6 (INC EAX, INC EDX)
#    meaning all 16 bytes when incremented == 0, i.e. all bytes are 0xFF.
# 6. The comparison at 401439: CMP EAX, EDX => must be equal.
#    EAX starts at 1 (4013B4), EDX starts at... unclear from writeup.
#    The writeup says EAX=1, EDX=1 at first breakpoint hit and program
#    goes through 4013DE path (INC EAX, DEC EDX) making them diverge.
#    The good path is all bytes = 0xFF (wrap to 0 on INC).
# 7. The actual serial generation algorithm (how name maps to serial bytes)
#    is described as "very long and complicated" and NOT fully shown.
#    The writeup only shows that the serial buffer at 4031CD must have
#    all 16 bytes = 0xFF for the correct path.
#
# ASSUMPTION: The serial displayed in the dialog is a transformed version
# of the raw serial buffer. The actual name->serial mapping is not given.
# We implement what we can verify from the writeup.

VALID_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-_@')
ALPHA_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')

def validate_name(name):
    """Check name restrictions described in writeup."""
    if len(name) < 5:
        return False
    if name[0] not in ALPHA_CHARS:
        return False
    for ch in name[1:]:
        if ch not in VALID_CHARS:
            return False
    return True

def _check_serial_buffer(serial_bytes_16):
    """
    Implements the check loop from 4013B4-4013E0.
    serial_bytes_16: list/bytes of exactly 16 bytes (the raw serial buffer).
    Returns True if EAX == EDX at 401439 via the 'good' path.

    Loop: for ecx from 15 down to 0:
        dl = serial_bytes_16[ecx]
        dl = (dl + 1) & 0xFF
        if dl != 0: go to 4013DE => INC EAX, DEC EDX, done
    # if all bytes wrapped: go to 4013D6 => load EAX=dword@CD, EDX=dword@D2, INC both
    # The writeup says EAX==EDX is achieved via the wrap path.
    """
    eax = 1
    edx = 1  # ASSUMPTION: EDX initial value is 1 based on writeup observation
    for ecx in range(15, -1, -1):
        dl = (serial_bytes_16[ecx] + 1) & 0xFF
        if dl != 0:
            # path 4013DE: INC EAX, DEC EDX
            eax += 1
            edx -= 1
            # then jump to 40141B for final compare
            return eax == edx
    # All bytes wrapped (all were 0xFF)
    # path 4013CB: load EAX=dword at [4031CD], EDX=dword at [4031D2], then INC both
    # ASSUMPTION: When all serial bytes are 0xFF, EAX and EDX after INC will be equal
    # because both overflow similarly. The writeup confirms this gives EAX==EDX.
    return True  # The good path

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: We cannot reconstruct the full name->serial mapping from the writeup.
    We validate name format and check if serial could produce the correct buffer state.
    The writeup does not give the actual transformation algorithm.
    """
    if not validate_name(name):
        return False
    # ASSUMPTION: The serial is a hex or ASCII string representing 16 bytes.
    # The actual encoding of the serial displayed in the dialog is unknown.
    # We attempt to interpret the serial as a 16-char string mapped to raw bytes.
    if len(serial) < 16:
        return False
    # ASSUMPTION: raw serial buffer = first 16 bytes of serial string
    raw = [ord(c) & 0xFF for c in serial[:16]]
    return _check_serial_buffer(raw)

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: The actual serial generation algorithm is not described in the writeup.
    The writeup says the calculation is 'very long and complicated' and does not
    show the name->serial transformation.
    We cannot generate a real valid serial without the actual algorithm.
    Returning None to indicate this limitation.
    """
    if not validate_name(name):
        raise ValueError(f"Invalid name: '{name}'. Must be >=5 chars, start with a letter, "
                         "remaining chars in [A-Za-z0-9.-_@]")
    # ASSUMPTION: A serial whose raw buffer is all 0xFF bytes would pass the check loop.
    # But the serial displayed in the edit box is some encoding of those bytes.
    # We don't know that encoding.
    # Return a placeholder showing what raw bytes would satisfy the buffer check:
    # all bytes = 0xFF
    # ASSUMPTION: direct ASCII representation as \xFF chars (probably wrong display encoding)
    raw_serial = bytes([0xFF] * 16)
    return raw_serial  # placeholder; real encoding unknown


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
