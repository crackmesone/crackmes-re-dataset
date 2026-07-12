import ctypes

def verify(name: str, serial: str) -> bool:
    """Verify that the serial matches the one generated from name."""
    if len(name) == 0:
        return False
    return keygen(name) == serial


def keygen(name: str) -> str:
    """
    Algorithm (from both solution writeups):
    1. Take the ASCII value of the LAST character of the name.
    2. Multiply by 0x16 (decimal 22) -> edx
    3. Multiply result by 0x38 (decimal 56) -> esi
    4. Add last_char + last_char -> eax  (i.e. last_char * 2)
    5. serial = esi + eax
    6. Convert to decimal string.

    Note: The crackme uses 32-bit signed integer arithmetic (imul),
    so we replicate that with ctypes to handle potential overflow.
    """
    if len(name) == 0:
        raise ValueError("Name must be at least 1 character (original requires >= 5).")

    last_char = ord(name[-1]) & 0xFF  # treat as unsigned byte (movzx)

    # Use 32-bit signed multiplication as in the original x86 imul instructions
    eax = ctypes.c_int32(last_char).value
    edx = ctypes.c_int32(eax * 0x16).value   # imul edx, eax, 0x16
    esi = ctypes.c_int32(edx * 0x38).value   # imul esi, edx, 0x38
    eax2 = ctypes.c_int32(eax + eax).value   # add eax, eax
    result = ctypes.c_int32(esi + eax2).value  # add esi, eax

    return str(result)



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
