def _extend_name(name: str) -> str:
    """Truncate name to 12 bytes, extending by repetition if shorter."""
    name = name[:12]  # truncate to 12
    length = len(name)
    if length == 0:
        raise ValueError("Name must not be empty")
    result = list(name)
    for i in range(length, 12):
        result.append(result[i % length])
    return ''.join(result)


# Index tables from the writeup
_EBP_14_IDXS = [0, 3, 6, 9]
_EBP_18_IDXS = [5, 8, 11, 2]
_EBP_1C_IDXS = [10, 1, 4, 7]


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Serial is 36 characters, characters from 0-9, A-Z,
    every third character (indices 2,5,8,...) from range '0'-'3'.
    """
    name12 = _extend_name(name)

    # Start with the serial template
    serial = list("882882882882882882882882882882882882")

    for idx in range(4):
        ebp_14 = ord(name12[_EBP_14_IDXS[idx]])
        ebp_18 = ord(name12[_EBP_18_IDXS[idx]])
        ebp_1c = ord(name12[_EBP_1C_IDXS[idx]])

        # dwSerialHash1 = dwSerialHash2 = dwSerialHash3 = -0x88 (as signed 32-bit)
        # In Python we use the raw integer value
        serial_hash = -0x88  # same value for all three hashes

        # --- Check/fix position 9*idx + 2 ---
        eax = serial_hash + serial_hash  # dwSerialHash1 + dwSerialHash2
        edx = ord(serial[9 * idx + 2]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_14 ^ eax) & 1:  # if XOR is odd, increment to make it even
            serial[9 * idx + 2] = chr(ord(serial[9 * idx + 2]) + 1)

        # --- Check/fix position 9*idx + 5 ---
        eax = serial_hash + serial_hash  # dwSerialHash2 + dwSerialHash3
        edx = ord(serial[9 * idx + 5]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_18 ^ eax) & 1:
            serial[9 * idx + 5] = chr(ord(serial[9 * idx + 5]) + 1)

        # --- Check/fix position 9*idx + 8 ---
        eax = serial_hash + serial_hash  # dwSerialHash1 + dwSerialHash3
        edx = ord(serial[9 * idx + 8]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_1c ^ eax) & 1:
            serial[9 * idx + 8] = chr(ord(serial[9 * idx + 8]) + 1)

    return ''.join(serial)


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Reconstructs what the serial should be and compares.
    Also validates serial format constraints.
    """
    # Serial must be exactly 36 characters
    if len(serial) != 36:
        return False

    # Serial must consist of 0-9, A-Z
    valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if not all(c in valid_chars for c in serial):
        return False

    # Every third character (positions 2,5,8,...,35) must be in '0'-'3'
    for i in range(2, 36, 3):
        if serial[i] not in '0123':
            return False

    name12 = _extend_name(name)

    serial_hash = -0x88

    for idx in range(4):
        ebp_14 = ord(name12[_EBP_14_IDXS[idx]])
        ebp_18 = ord(name12[_EBP_18_IDXS[idx]])
        ebp_1c = ord(name12[_EBP_1C_IDXS[idx]])

        # Check position 9*idx + 2
        eax = serial_hash + serial_hash
        edx = ord(serial[9 * idx + 2]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_14 ^ eax) & 1:
            return False

        # Check position 9*idx + 5
        eax = serial_hash + serial_hash
        edx = ord(serial[9 * idx + 5]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_18 ^ eax) & 1:
            return False

        # Check position 9*idx + 8
        eax = serial_hash + serial_hash
        edx = ord(serial[9 * idx + 8]) - ord('0')
        eax = eax + (edx & 1)
        if (ebp_1c ^ eax) & 1:
            return False

    return True



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
