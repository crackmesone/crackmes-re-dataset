def keygen(name: str) -> str:
    """
    Generate serial for a given name string (up to 10 chars used).
    The serial is a 20-character hex string (uppercase).
    
    Algorithm extracted directly from Solution 2 (src/main.cpp):
    
    serial = '0A'
           + hex(name[0] + name[1] + 0x16, 2 bytes)
           + '6B0D16'
           + hex(name[8] + name[4] - name[2], 2 bytes)
           + '01'
           + hex(sum(name[0..9]) + 0x34, 2 bytes)
           + hex(sum(name[0..9]), 2 bytes)
           + hex(sum(name[0..9]) + 0x48, 2 bytes)
    """
    # Name must be non-empty; pad or truncate to 10 chars for index safety
    if not name:
        raise ValueError('Name must not be empty')
    
    # Pad name with zeros (null bytes) if shorter than 10 chars, like C char array
    name_bytes = [ord(c) for c in name[:10]]
    while len(name_bytes) < 10:
        name_bytes.append(0)
    
    serial = '0A'
    
    # bytes 2-3: name[0] + name[1] + 0x16
    bValue = (name_bytes[0] + name_bytes[1] + 0x16) & 0xFF
    serial += '%02X' % bValue
    
    # bytes 4-9: literal '6B0D16'
    serial += '6B0D16'
    
    # bytes 10-11: name[8] + name[4] - name[2]
    bValue = (name_bytes[8] + name_bytes[4] - name_bytes[2]) & 0xFF
    serial += '%02X' % bValue
    
    # bytes 12-13: literal '01'
    serial += '01'
    
    # compute sum of first 10 name bytes
    total = sum(name_bytes) & 0xFF
    
    # bytes 14-15: total + 0x34
    serial += '%02X' % ((total + 0x34) & 0xFF)
    # bytes 16-17: total
    serial += '%02X' % total
    # bytes 18-19: total + 0x48
    serial += '%02X' % ((total + 0x48) & 0xFF)
    
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial matches the expected serial for name.
    Serial is a 20-character uppercase hex string.
    """
    if not name:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
    return serial.upper() == expected.upper()



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
