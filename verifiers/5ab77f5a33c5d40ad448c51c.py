import ctypes
import datetime

def _rol32(value, count):
    """Rotate left 32-bit value by count bits."""
    value &= 0xFFFFFFFF
    count &= 31
    return ((value << count) | (value >> (32 - count))) & 0xFFFFFFFF

def _compute_serial(name: str, month: int) -> int:
    """
    Implements the serial computation from the disassembly:

    Per-character loop:
        ecx += ord(char)        (32-bit add)
        ecx = ROL(ecx, 8)
        ecx ^= 0x0C
        al  = 0x30
        ecx ^= 0x02
        ecx -= 0x803
        cl  += al               (only low byte: cl = (ecx & 0xFF) + 0x30)

    After loop:
        ecx ^= 0x02
        ecx -= 0x50
        ecx ^= 0x1337

    Month adjustment (16-bit SI arithmetic):
        si  = month & 0xFFFF
        si ^= 0x408A
        si  = (si + 0x1E) & 0xFFFF
        cx  = (cx + si) & 0xFFFF    <- only low 16 bits of ecx modified
    """
    ecx = 0

    for ch in name:
        al = ord(ch) & 0xFF
        ecx = (ecx + al) & 0xFFFFFFFF
        ecx = _rol32(ecx, 8)
        ecx ^= 0x0C
        al = 0x30
        ecx ^= 0x02
        ecx = (ecx - 0x803) & 0xFFFFFFFF
        # add cl, al  =>  only low byte of ecx changes
        cl = (ecx & 0xFF) + al
        ecx = (ecx & 0xFFFFFF00) | (cl & 0xFF)

    # post-loop
    ecx ^= 0x02
    ecx = (ecx - 0x50) & 0xFFFFFFFF
    ecx ^= 0x1337

    # month-based SI adjustment (16-bit operations)
    si = month & 0xFFFF
    si ^= 0x408A
    si = (si + 0x1E) & 0xFFFF
    # add cx, si  =>  only low 16 bits of ecx change
    cx = (ecx & 0xFFFF)
    cx = (cx + si) & 0xFFFF
    ecx = (ecx & 0xFFFF0000) | cx

    return ecx & 0xFFFFFFFF


def keygen(name: str, month: int = None) -> str:
    """
    Generate a valid serial for the given name.
    month: 1-12 (current month used if not supplied).
    Returns the serial as a decimal string.
    """
    if month is None:
        month = datetime.datetime.utcnow().month
    serial = _compute_serial(name, month)
    return str(serial)


def verify(name: str, serial: str, month: int = None) -> bool:
    """
    Verify name/serial pair.
    The crackme compares the entered serial (as a DWORD integer) against ECX.
    month: 1-12 (current month used if not supplied).
    """
    # Name must be between 6 and 51 characters
    if len(name) < 6 or len(name) > 51:
        return False
    if month is None:
        month = datetime.datetime.utcnow().month
    try:
        entered = int(serial) & 0xFFFFFFFF
    except ValueError:
        return False
    expected = _compute_serial(name, month)
    return entered == expected



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
