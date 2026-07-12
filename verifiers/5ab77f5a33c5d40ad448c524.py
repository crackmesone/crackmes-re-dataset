import struct

# This crackme does NOT use a name; it's a fixed password (serial-only) crackme.
# The password must be exactly 10 printable characters.
# Algorithm reconstructed from keygen.DPR by NoRG.

PASSLEN = 10

# Known valid passwords from solution.txt (subset)
VALID_PASSWORDS = [
    "(I3s$J61md", "(I3s%J61md", "(I3s4J61md", "(I3s5J61md",
    "(I3sDJ61md", "(I3sEJ61md", "(I3sTJ61md", "(I3sUJ61md",
    "(I3sdJ61md", "(I3seJ61md", "(I3stJ61md", "(I3suJ61md",
]


def _u8(x):
    return x & 0xFF


def _check_pass89(p8, p9):
    """
    Check bytes at index 8 and 9 of the password.
    pre8 = p8 + 0xf2 (mod 256), then pre8 = pre8 * 2 (mod 256), then pre8 += p9
    pre9 = p9 + 0x3a (mod 256), then pre9 += pre8, then pre9 = pre9 * 2 (mod 256)
    Must satisfy: pre8 == 0x22 and pre9 == 0x80
    """
    pre8 = _u8(p8 + 0xf2)
    pre8 = _u8(pre8 + pre8)  # pre8 * 2
    pre8 = _u8(pre8 + p9)

    pre9 = _u8(p9 + 0x3a)
    pre9 = _u8(pre9 + pre8)
    pre9 = _u8(pre9 + pre9)  # pre9 * 2

    return pre8 == 0x22 and pre9 == 0x80


def _check_pass0to7(password_bytes):
    """
    Reconstruct and verify bytes 0-7.

    Forward pass (what crackme does):
      For k in [0, 4]:
        dword = unpack('<I', pass[k:k+4])
        dword ^= 0x01234567
        pass[k] = pass[k] & 0x0E  (only low nibble, must be even)
        dword ^= 0x089ABCDE
        pass[k] = pass[k] & 0x0E

    Then compare:
      dword at [0] == 0x7A8AB000
      dword at [4] == 0x388FB30C

    ASSUMPTION: The 'and 0x0E' is applied only to pass[k] (the first byte of the dword).
    The keygen bruteforces pass[0] and pass[4] because those bytes are partially destroyed.
    """
    test = bytearray(password_bytes[:8])

    for k in [0, 4]:
        dw = struct.unpack_from('<I', test, k)[0]
        dw ^= 0x01234567
        b0 = (dw & 0xFF) & 0x0E
        dw = (dw & 0xFFFFFF00) | b0
        struct.pack_into('<I', test, k, dw)

    for k in [0, 4]:
        dw = struct.unpack_from('<I', test, k)[0]
        dw ^= 0x089ABCDE
        b0 = (dw & 0xFF) & 0x0E
        dw = (dw & 0xFFFFFF00) | b0
        struct.pack_into('<I', test, k, dw)

    dw0 = struct.unpack_from('<I', test, 0)[0]
    dw4 = struct.unpack_from('<I', test, 4)[0]

    return dw0 == 0x7A8AB000 and dw4 == 0x388FB30C


def verify(name, serial):
    """
    Verify a serial (password). Name is ignored (crackme is serial-only).
    Password must be exactly 10 printable ASCII characters.
    """
    if len(serial) != PASSLEN:
        return False
    # Check all chars are printable (32-127)
    for c in serial:
        if ord(c) < 32 or ord(c) > 127:
            return False

    bs = [ord(c) for c in serial]

    # Check bytes 8 and 9
    if not _check_pass89(bs[8], bs[9]):
        return False

    # Check bytes 0-7
    if not _check_pass0to7(bs):
        return False

    return True


def keygen(name):
    """
    Generate valid serials. Name is ignored.
    Bruteforce all printable character combinations.
    """
    # First find valid (pass[8], pass[9])
    valid_89 = []
    for i in range(32, 128):
        for j in range(32, 128):
            if _check_pass89(i, j):
                valid_89.append((i, j))

    # Compute base bytes 0-7 by reversing:
    # Start from target values and undo xor operations
    # Target after processing: dw0=0x7A8AB000, dw4=0x388FB30C
    # ASSUMPTION: reconstruct base bytes ignoring the 'and 0x0E' destruction on byte[0] and byte[4]
    # The keygen sets pass[0..7] then bruteforces pass[0] and pass[4]

    # Reverse: undo second xor pass
    base = bytearray(8)
    struct.pack_into('<I', base, 0, 0x7A8AB000)
    struct.pack_into('<I', base, 4, 0x388FB30C)

    for k in [4, 0]:
        dw = struct.unpack_from('<I', base, k)[0]
        dw ^= 0x089ABCDE
        struct.pack_into('<I', base, k, dw)

    for k in [4, 0]:
        dw = struct.unpack_from('<I', base, k)[0]
        dw ^= 0x01234567
        struct.pack_into('<I', base, k, dw)

    for i in range(33, 128):
        for j in range(33, 128):
            candidate = bytearray(base)
            candidate[0] = i
            candidate[4] = j

            # Check this combination
            if _check_pass0to7(candidate):
                for p8, p9 in valid_89:
                    serial_bytes = bytes(candidate) + bytes([p8, p9])
                    serial = ''.join(chr(b) for b in serial_bytes)
                    yield serial



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
