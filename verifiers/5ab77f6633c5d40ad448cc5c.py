import sys

def _compute_magic(username8):
    """
    Compute the initial 'magic' / salt from username[1].
    Based on the assembly:
        movzx eax, username[1]
        movsx dx, al
        imul  edx, 0x56
        shr   dx, 8
        sar   al, 7
        ebx = edx - eax
        eax = ebx & 0xFF  (movsx eax, al -> sign-extend byte)
    """
    c1 = ord(username8[1]) & 0xFF
    # imul / shr path (16-bit arithmetic)
    dx = c1 * 0x56
    dx = (dx >> 8) & 0xFF
    # sar al, 7  -> arithmetic shift right 7 on signed byte
    al = c1 & 0xFF
    # sign extend to 8-bit signed then sar 7
    if al & 0x80:
        al_signed = al - 0x100
    else:
        al_signed = al
    sar_result = (al_signed >> 7) & 0xFF
    # ebx = dx - sar_result  (both treated as bytes, result taken as byte)
    ebx = (dx - sar_result) & 0xFF
    # movsx eax, al  -> sign-extend the byte
    if ebx & 0x80:
        eax = ebx - 0x100
    else:
        eax = ebx
    # var_8 / magic used as integer in xor; keep as byte value
    return eax & 0xFF


def _normalize_username(name):
    """
    Normalize the username to exactly 8 characters:
    - Must be at least 7 chars (the 8th will be '\n' appended by fgets).
    - Only first 8 chars are used.
    - Spaces are not allowed (replace with 'X' if needed by keygen).
    Per solution 1 (32-bit version): username[:8], padded with '\n' if <8.
    Per solution 6 (64-bit version): must be exactly 7 chars, padded with '\n'.
    We support both: pad to 8 with '\n' if shorter, truncate to 8.
    """
    if len(name) < 7:
        raise ValueError("Username must be at least 7 characters")
    # Pad with newline if less than 8
    if len(name) < 8:
        name = name + '\n'
    # Truncate to 8
    name = name[:8]
    return name


def _gen_serial_chars(username8):
    """
    Core loop: iterate over all 8 characters of username8.
    For each character c at index i:
        tmp = (ord(c) ^ magic) & 0x3C
        serial_char = chr(tmp + 0x30)
        magic = (tmp * 3) & 0xFF   # kept as byte via natural truncation
    Returns list of serial characters (length 8).
    """
    magic = _compute_magic(username8)
    serial = []
    for c in username8:
        tmp = (ord(c) ^ magic) & 0x3C
        serial.append(chr(tmp + 0x30))
        magic = (tmp * 3) & 0xFF
    return serial


def verify(name, serial):
    """
    Verify a (username, serial/password) pair.
    Returns True if the serial matches the one generated from the username.
    Only the first 8 characters of the generated serial are checked
    (the crackme has an off-by-one and only checks 8 chars even though 9 are generated).
    """
    try:
        username8 = _normalize_username(name)
    except ValueError:
        return False
    expected_chars = _gen_serial_chars(username8)
    expected = ''.join(expected_chars)  # 8 chars
    # The crackme only checks first 8 chars of the entered password
    return serial[:8] == expected


def keygen(name):
    """
    Generate the serial/password for the given username.
    Returns an 8-character serial string.
    """
    username8 = _normalize_username(name)
    chars = _gen_serial_chars(username8)
    return ''.join(chars)



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
