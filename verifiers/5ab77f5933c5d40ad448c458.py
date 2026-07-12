import ctypes

def compute_serials(name: str):
    """
    Compute serial and masterserial for a given name.
    The serial depends only on len(name), not the actual characters.
    """
    length = len(name)
    # NAME = (strlen(name) + 0xCA) ^ 0x3D8D40F, treated as a 32-bit signed integer
    name_val = ctypes.c_int32((length + 0xCA) ^ 0x3D8D40F).value

    # masterserial is computed BEFORE the adjustment of name_val
    # masterserial = 0x186A0 + name_val + 0xD75E9
    # Simplified: name_val + 0xEFC89
    masterserial = ctypes.c_int32(name_val + 0xEFC89).value

    # Adjust name_val to equal 0x186A0 (the constant [ebp-2c])
    # First if: if name_val < 0x186A0: name_val += 0x8C9666F8 (signed 32-bit)
    if name_val < 0x186A0:
        name_val = ctypes.c_int32(name_val + 0x8C9666F8).value
    # Second if: if name_val > 0x186A0: name_val += 0xB61B9688 (signed 32-bit)
    if name_val > 0x186A0:
        name_val = ctypes.c_int32(name_val + 0xB61B9688).value

    # serial is the (possibly adjusted) name_val, entered as signed decimal
    serial = name_val
    return serial, masterserial


def verify(name: str, serial: str) -> bool:
    """
    Verify the first serial only.
    The serial must be the signed decimal representation of the computed serial value.
    """
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    computed_serial, _ = compute_serials(name)
    return serial_int == computed_serial


def verify_master(name: str, masterserial: str) -> bool:
    """
    Verify the masterserial (second challenge).
    """
    try:
        ms_int = int(masterserial)
    except ValueError:
        return False
    _, computed_ms = compute_serials(name)
    return ms_int == computed_ms


def keygen(name: str):
    """
    Generate (serial, masterserial) as signed decimal strings for the given name.
    Note: all names of the same length produce the same serial.
    """
    serial, masterserial = compute_serials(name)
    return str(serial), str(masterserial)



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
