import math

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Rules from CalculateSerial:
      - name must be at least 6 characters
      - only first 8 characters are used
      - serial[i] = 0x31 + (ord(name[i]) & 0xF) % 9
    """
    name_bytes = name.encode('latin-1')
    name_len = len(name_bytes)
    if name_len < 6:
        return ""
    if name_len > 8:
        name_len = 8
    serial_chars = []
    for i in range(name_len):
        c = 0x31 + (name_bytes[i] & 0xF) % 9
        serial_chars.append(chr(c))
    return ''.join(serial_chars)


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the expected serial for name.
    """
    expected = keygen(name)
    if not expected:
        return False
    return serial == expected


def _decode_serial_to_int(serial_str: str) -> int:
    """
    Parse the serial string as an integer (what GetDlgItemInt would return).
    """
    try:
        return int(serial_str)
    except ValueError:
        return 0


def keygen_keyfile(name: str):
    """
    Reproduce the KeyFileAndRegistry logic to show what goes in the keyfile
    and registry, given a name.

    Returns (keyfile_serial_bytes, reg_serial_str)
    """
    serial_str = keygen(name)
    if not serial_str:
        return None, None

    iSerial = _decode_serial_to_int(serial_str)
    szKeyFileSerial = list(b'figugegl') + [0] * 24  # 32 bytes total

    cCountBytes = 0
    for i in range(8, 28):
        # iRest = iSerial % (-2)
        iRest = iSerial % (-2)  # Python modulo matches C for positive iSerial: result is 0 or -1
        # In C, result of % with negative divisor when dividend is positive: 0 or negative
        # For positive iSerial:
        #   iSerial % (-2) in C can be 0 or -(iSerial % 2) i.e. 0 or -1 when iSerial > 0
        # ASSUMPTION: Python's % gives 0 or 1 for negative modulus; we replicate C behavior:
        # In C: iSerial % (-2) = iSerial % 2 with sign of iSerial -> 0 or 0 for even, 0 or -1 for odd when positive
        # Let's implement C-style:
        if iSerial >= 0:
            c_iRest = -(iSerial % 2)  # 0 for even, -1 for odd
        else:
            c_iRest = iSerial % 2  # For negative iSerial
        iRest = c_iRest
        if iRest < 0:
            iRest = 1
            iSerial -= 1
        cCountBytes += iRest
        szKeyFileSerial[i] = iRest + 0x30
        # C integer division toward zero
        if iSerial >= 0:
            iSerial = -(iSerial // 2)
        else:
            iSerial = -(-iSerial // 2)  # ASSUMPTION: C truncation toward zero
        if iSerial == 0:
            break

    keyfile_bytes = bytes(szKeyFileSerial)

    # Registry serial
    iSerial2 = _decode_serial_to_int(serial_str)
    if cCountBytes != 0:
        iSerial2 = iSerial2 // cCountBytes  # C integer division
    dSerial = math.sqrt(iSerial2)
    reg_serial = str(int(dSerial))

    return keyfile_bytes, reg_serial



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
