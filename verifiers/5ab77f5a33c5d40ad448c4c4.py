# Reconstructed from the writeup by kao for keygenme_1 by TaGaDaPaF
# The writeup describes:
#   1. A serial is generated from the name (described as 'easy algo' but not fully shown)
#   2. During comparison, each byte of the stored serial has 0xFD subtracted (low byte of 6D82B4FDh)
#      before comparing to the entered serial.
#   3. Name must be 3..48 (0x30) chars long.
#
# The generation algorithm is NOT fully shown in the writeup.
# The writeup says 'TaGaDaPaF says it's an easy algo' but does not disclose it.
# ASSUMPTION: We can only implement the structure; the core keygen algo is unknown.

def _sub_trick(b):
    # ASSUMPTION: The stored 'almost-correct' serial byte has 0xFD subtracted (low byte of 6D82B4FDh)
    # to produce the real expected byte. We model this as: real_byte = (stored_byte - 0xFD) & 0xFF
    # But since we don't know the stored serial generation, we can't implement this fully.
    return (b - 0xFD) & 0xFF

def _generate_serial(name):
    # ASSUMPTION: The actual serial generation algorithm is not disclosed in the writeup.
    # The author calls it 'easy'. A common simple approach: sum/xor of name bytes with index.
    # We implement a placeholder that cannot be verified without the binary.
    # ASSUMPTION: simple checksum-style algo over name bytes.
    serial_bytes = []
    acc = 0
    for i, c in enumerate(name.encode('ascii', errors='replace')):
        # ASSUMPTION: placeholder - real algo unknown
        val = (c * (i + 1) + acc) & 0xFF
        acc = val
        serial_bytes.append(val)
    return bytes(serial_bytes)

def verify(name, serial):
    """
    Verify a name/serial pair.
    Based on the writeup:
    - Name must be 3..48 chars long
    - A 'correct' serial is generated from the name
    - During check, each byte from the stored serial has low byte of 6D82B4FDh (=0xFD) subtracted
    - The result is compared to the entered serial byte by byte
    """
    if not (3 <= len(name) <= 48):
        return False

    # ASSUMPTION: serial is compared as a string/bytes against generated value
    try:
        serial_bytes = serial.encode('ascii', errors='replace')
    except AttributeError:
        serial_bytes = bytes(serial)

    # Generate the 'almost correct' stored serial
    stored = _generate_serial(name)

    # Apply the subtraction trick: real expected = (stored_byte - 0xFD) & 0xFF
    expected = bytes(_sub_trick(b) for b in stored)

    # ASSUMPTION: comparison is length-matched to the generated serial
    if len(serial_bytes) != len(expected):
        return False

    return serial_bytes == expected

def keygen(name):
    """
    Generate a valid serial for a given name.
    ASSUMPTION: The actual generation algorithm is not shown in the writeup.
    This is a placeholder implementation only.
    """
    if not (3 <= len(name) <= 48):
        raise ValueError('Name must be 3 to 48 characters')

    stored = _generate_serial(name)
    # The real serial to enter = stored_byte - 0xFD for each byte
    real_serial = bytes(_sub_trick(b) for b in stored)
    # Return as latin-1 string
    return real_serial.decode('latin-1')


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
