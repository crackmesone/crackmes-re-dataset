import ctypes

def compute_serial(name: str) -> str:
    """
    Implements the serial calculation algorithm from fusS' crackme #05.

    The algorithm (from multiple writeups / disassembly):
    1. Iterate over each character in the name string by index:
       - bl = name[i]          (low byte of ebx)
       - bh = name[i+1] if exists else 0  (high byte of ebx)
       - ebx = ebx * ebx       (imul ebx, ebx)
       - ecx += ebx
       - ebx = 0
       - i++
       - repeat until name[i] == 0
    2. ecx += 0xBAB1E5
    3. Loop 0x63 (99) times: ecx += 2  =>  ecx += 0xC6 (198)
    4. ecx = (ecx * 0xDEADBEEF) - 0xDEADBEEF
       (all arithmetic is 32-bit signed / modular)
    5. serial string = str(ecx as signed 32-bit integer) + '-[TS]'

    The MagicValue stored in the registry is: '<number>-[TS]'
    """
    # Work in 32-bit space using ctypes for proper overflow behaviour
    ecx = ctypes.c_int32(0)
    ebx = ctypes.c_int32(0)

    # Convert name to bytes
    name_bytes = name.encode('latin-1') + b'\x00'  # null-terminated

    i = 0
    while True:
        bl = name_bytes[i] if i < len(name_bytes) else 0
        if bl == 0:
            break
        bh = name_bytes[i + 1] if (i + 1) < len(name_bytes) else 0

        # ebx = bl | (bh << 8)
        ebx_val = ctypes.c_int32(bl | (bh << 8))
        # imul ebx, ebx  (32-bit signed multiply, keep low 32 bits)
        ebx_val = ctypes.c_int32(ebx_val.value * ebx_val.value)
        # add ecx, ebx
        ecx = ctypes.c_int32(ecx.value + ebx_val.value)
        # xor ebx, ebx
        ebx_val = ctypes.c_int32(0)
        # inc eax (pointer advance)
        i += 1

    # add ecx, 0BAB1E5h
    ecx = ctypes.c_int32(ecx.value + 0xBAB1E5)

    # Loop 0x63 times: add ecx, 2  =>  ecx += 0x63 * 2 = 0xC6
    for _ in range(0x63):
        ecx = ctypes.c_int32(ecx.value + 2)

    # imul ecx, 0DEADBEEFh
    ecx = ctypes.c_int32(ecx.value * ctypes.c_int32(0xDEADBEEF).value)

    # sub ecx, 0DEADBEEFh
    ecx = ctypes.c_int32(ecx.value - ctypes.c_int32(0xDEADBEEF).value)

    # Format: signed decimal + '-[TS]'
    return "{}-[TS]".format(ecx.value)


def verify(name: str, serial: str) -> bool:
    """
    Returns True if serial matches the computed MagicValue for the given name.
    The crackme checks:
      - len(name) > 1  (lstrlen >= 2; the check is 'cmp eax, 1 / jle badboy')
      - len(serial) > 0
      - computed == serial
    """
    if len(name) <= 1:
        return False
    if len(serial) == 0:
        return False
    expected = compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generates the valid MagicValue serial for the given name.
    """
    if len(name) <= 1:
        raise ValueError("Name must be at least 2 characters long.")
    return compute_serial(name)



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
