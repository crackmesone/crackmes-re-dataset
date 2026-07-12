import struct

XOR_CONST = 0x63546D32  # 'cTm2'
MASK32 = 0xFFFFFFFF


def compute_serial(name: str) -> int:
    """
    Implements the key-file checksum algorithm described in the writeups.

    Starting with eax=1, edx=0:
      for each byte b in name (up to 0xFF bytes):
          eax = (eax * b) & 0xFFFFFFFF
          eax = eax ^ 0x63546D32

    After the loop:
      if eax != 0:
          eax = eax >> 1

    Return eax (the 32-bit serial value).
    """
    eax = 1
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name

    for i, b in enumerate(name_bytes):
        if i >= 0xFF:
            break
        if b == 0:
            # Null byte terminates the name portion
            break
        eax = (eax * b) & MASK32
        eax = eax ^ XOR_CONST

    if eax != 0:
        eax = (eax >> 1) & MASK32

    return eax


def make_keyfile_bytes(name: str) -> bytes:
    """
    Build the raw bytes that should be written to 'ctm_cm02.key'.
    Format: <name bytes> <0x00> <serial as 4 LE bytes>
    Total length = len(name) + 1 + 4
    The crackme checks: null_pos + 1 + 4 == file_size,
    i.e. the null byte is exactly 5 bytes before the end.
    """
    serial = compute_serial(name)
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    # serial stored as little-endian 32-bit
    serial_bytes = struct.pack('<I', serial)
    return name_bytes + b'\x00' + serial_bytes


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.

    'serial' here is interpreted as the hex string representation of the
    expected 32-bit little-endian value stored in the key file,
    OR as a raw 4-byte bytes-like string.

    We reconstruct what the key file would look like and check whether
    the serial matches the computed checksum.
    """
    expected = compute_serial(name)

    # Accept serial as integer, hex string, or raw 4-byte value
    if isinstance(serial, int):
        provided = serial & MASK32
    elif isinstance(serial, (bytes, bytearray)):
        if len(serial) != 4:
            return False
        provided = struct.unpack('<I', serial)[0]
    elif isinstance(serial, str):
        try:
            provided = int(serial, 16) & MASK32
        except ValueError:
            return False
    else:
        return False

    return provided == expected


def keygen(name: str) -> str:
    """
    Generate the serial (as a hex string) for the given name.
    The actual key file content is: name + NUL + serial_le32.
    """
    serial = compute_serial(name)
    return '{:08X}'.format(serial)

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
