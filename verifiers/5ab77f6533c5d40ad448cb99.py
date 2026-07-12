import ctypes

def _process_name(name: str) -> str:
    """If name length > 10, take first 5 and last 5 chars and concatenate."""
    if len(name) > 10:
        # ASSUMPTION: based on solution2 description - first 5 + last 5 chars
        name = name[:5] + name[len(name)-5:]
    return name


def _compute_serial(name: str) -> int:
    """Core serial computation matching the assembly loop.
    Registers: ESI starts at 3, EDX starts at 3 (=ESI).
    Loop:
        EAX = name[i] (signed byte)
        ECX = EDX + EAX
        ECX *= ESI
        ESI = EAX * 8 - EAX   (= 7 * EAX)
        EDX += 1
        ESI = ESI + ECX + 0x1341
    After loop: ESI &= 0xDEADBEEF
    """
    # Use 32-bit signed arithmetic via ctypes
    def i32(v):
        return ctypes.c_int32(v).value

    def u32(v):
        return ctypes.c_uint32(v).value

    ESI = 3
    EDX = 3

    for ch in name:
        EAX = i32(ord(ch))          # MOVSX: sign-extend byte
        ECX = i32(EDX + EAX)
        ECX = i32(ECX * ESI)
        ESI = i32(EAX * 8 - EAX)   # ESI = EAX*8; SUB ESI, EAX
        EDX = i32(EDX + 1)
        ESI = i32(ESI + ECX + 0x1341)

    ESI = i32(u32(ESI) & 0xDEADBEEF)  # AND with 0xDEADBEEF (treat as unsigned mask)
    return ESI


def _serial_to_string(serial_int: int) -> str:
    """Convert to decimal string as the crackme does with wsprintfA(\"%d\")."""
    return str(serial_int)


def keygen(name: str) -> str:
    """Generate valid serial for the given name (must be <= 10 chars)."""
    if len(name) > 10:
        raise ValueError("Name must be 10 characters or fewer for reliable serial generation.")
    processed = _process_name(name)
    serial_int = _compute_serial(processed)
    return _serial_to_string(serial_int)


def verify(name: str, serial: str) -> bool:
    """Return True if serial matches the expected serial for name."""
    try:
        expected = keygen(name)
        return serial.strip() == expected.strip()
    except ValueError:
        return False



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
