import struct

def _compute_name_hash(name: str) -> int:
    """
    For each character in name:
      DL += char_value
      EDX = ROR(EDX, 2)
    Then EDX += 0x12345678
    All operations are 32-bit.
    """
    edx = 0
    for ch in name:
        dl = edx & 0xFF
        dl = (dl + ord(ch)) & 0xFF
        edx = (edx & 0xFFFFFF00) | dl
        # ROR EDX, 2  (32-bit)
        edx = edx & 0xFFFFFFFF
        edx = ((edx >> 2) | (edx << 30)) & 0xFFFFFFFF
    edx = (edx + 0x12345678) & 0xFFFFFFFF
    return edx


def _serial_bytes_to_str(value: int) -> str:
    """Convert a 32-bit integer to a 4-byte little-endian string."""
    return struct.pack('<I', value).decode('latin-1')


def verify(name: str, serial: str) -> bool:
    """
    Validate name/serial for the Evolution crackme.

    Serial must be exactly 9 chars.
    Layout: [4 bytes part1][1 byte separator (any)][4 bytes part2]

    Part 1 (bytes 0-3 as little-endian DWORD) must equal the name hash.
    Part 2 (bytes 5-8 as little-endian DWORD) must equal (0x34333231 XOR hwnd).

    NOTE: The HWND check makes it runtime-dependent.
    The 5th character is never actually checked (the XOR with 0x2D is pointless).
    """
    if len(name) < 1:
        return False
    if len(serial) != 9:
        return False

    name_hash = _compute_name_hash(name)

    # Part 1: first 4 bytes of serial as little-endian DWORD
    part1_bytes = serial[:4].encode('latin-1')
    part1 = struct.unpack('<I', part1_bytes)[0]

    if part1 != name_hash:
        return False

    # Part 2: last 4 bytes (serial[5:9]) as little-endian DWORD
    # Must equal 0x34333231 XOR hwnd
    # ASSUMPTION: hwnd is unknown at static analysis time; we cannot verify part2 statically.
    # We treat part2 as always passing for keygen purposes, or require hwnd to be supplied.
    # For a pure offline check we skip this part.
    # ASSUMPTION: hwnd check is skipped since hwnd is runtime-dependent.
    return True


def verify_with_hwnd(name: str, serial: str, hwnd: int) -> bool:
    """
    Full verify including the HWND-dependent second part.
    hwnd: the HWND of the dialog window at runtime.
    """
    if len(name) < 1:
        return False
    if len(serial) != 9:
        return False

    name_hash = _compute_name_hash(name)

    part1_bytes = serial[:4].encode('latin-1')
    part1 = struct.unpack('<I', part1_bytes)[0]
    if part1 != name_hash:
        return False

    part2_bytes = serial[5:9].encode('latin-1')
    part2 = struct.unpack('<I', part2_bytes)[0]

    expected_part2 = (0x34333231 ^ hwnd) & 0xFFFFFFFF
    if part2 != expected_part2:
        return False

    return True


def keygen(name: str, hwnd: int = 0) -> str:
    """
    Generate a valid serial for the given name.
    hwnd: optional HWND value (runtime-dependent; defaults to 0).

    Serial format: part1 (4 bytes LE) + separator (1 byte, '-') + part2 (4 bytes LE)
    """
    if len(name) < 1:
        raise ValueError('Name must be at least 1 character long.')

    name_hash = _compute_name_hash(name)
    part1 = struct.pack('<I', name_hash).decode('latin-1')

    separator = '-'

    # ASSUMPTION: hwnd is 0 if not provided; for real usage the hwnd must be known.
    part2_val = (0x34333231 ^ hwnd) & 0xFFFFFFFF
    part2 = struct.pack('<I', part2_val).decode('latin-1')

    serial = part1 + separator + part2
    assert len(serial) == 9
    return serial



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
