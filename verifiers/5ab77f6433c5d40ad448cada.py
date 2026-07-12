# This crackme is a PatchMe/CrackMe that checks a file 'cdrom_drive/sec.code'
# on disk. There is no name/serial validation algorithm - the protection is
# purely file-based (the file must exist and pass a checksum check).
#
# The 'sec.code' file must be 12 bytes (11 meaningful bytes + 1 implicit zero)
# such that XOR of all 12 bytes equals 0xB7.
# After that check, the bytes are called as code (stolen bytes / code cave).
# There is no name/serial pair to verify.

def verify(name: str, serial: str) -> bool:
    # ASSUMPTION: There is no name/serial check in this crackme.
    # The crackme validates the file 'cdrom_drive/sec.code' on disk.
    # The check XORs 12 bytes from the file and compares against 0xB7.
    # Then the bytes are executed as machine code (stolen bytes).
    # A name/serial concept does not apply here.
    raise NotImplementedError(
        "This crackme does not use a name/serial scheme. "
        "It validates a file 'cdrom_drive/sec.code' on disk."
    )

def keygen(name: str) -> str:
    # ASSUMPTION: Not applicable - no serial/keygen concept exists.
    raise NotImplementedError(
        "This crackme is a PatchMe, not a KeygenMe. "
        "No serial generation is possible."
    )

def check_sec_code_file(data: bytes) -> bool:
    """
    Actual check performed by the crackme:
    Read up to 12 bytes from sec.code (padded with 0x00 to 12 bytes),
    XOR all bytes together, result must equal 0xB7.
    Then the bytes are jumped to / called as code (stolen bytes).
    """
    if len(data) < 11:
        return False
    # Pad to 12 bytes with zero
    padded = (data[:11] + b'\x00').ljust(12, b'\x00')
    checksum = 0
    for b in padded:
        checksum ^= b
    return checksum == 0xB7

def generate_sec_code(payload_bytes_11: bytes) -> bytes:
    """
    Given 11 bytes of desired machine code payload,
    compute the 12th byte (appended as a NOP or filler)
    such that XOR of all 12 equals 0xB7.
    The 12th byte is implicit zero per the writeup,
    so the first 11 bytes must already XOR to 0xB7.
    """
    # ASSUMPTION: The 12th byte is always 0x00 (zero-initialized before read).
    # So XOR of the 11 file bytes must equal 0xB7.
    assert len(payload_bytes_11) == 11
    checksum = 0
    for b in payload_bytes_11:
        checksum ^= b
    # Adjust last byte so total xor == 0xB7
    adjusted = list(payload_bytes_11)
    adjusted[-1] ^= (checksum ^ 0xB7)
    return bytes(adjusted)


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
