import ctypes

def keygen(name: str) -> str:
    """
    Compute the valid serial for the given name.
    Algorithm recovered from the writeup by TaGaDaPaF.
    """
    length = len(name)

    if length < 4:
        return "Name too small"

    local1 = length // 2   # Name.Length / 2  (integer division)
    local2 = length % 2    # Name.Length mod 2  (0 if even, 1 if odd)

    # First loop: i from 1 to local1 inclusive (1-based index into name)
    # Uses name[i] where i=1 means the SECOND character (0-based: name[i])
    # The writeup says: for(int i=1; i<=local1; i++) using name[i]
    # In Delphi strings are 1-based; in the assembly EDX starts at name[1] (0-based index 1)
    # ASSUMPTION: name[i] uses 0-based Python indexing starting at index 1
    ESI = 0
    for i in range(1, local1 + 1):
        char_val = ord(name[i]) if i < length else 0
        ESI = (ESI + char_val * local1) ^ 0xCC
        # abs() via two's complement 32-bit signed
        ESI = ctypes.c_int32(ESI).value
        if ESI < 0:
            ESI = -ESI

    # Second loop: i from local1 to length-1 (0-based)
    # The writeup says: for(int i=local1; i<length; i++) using name[i]
    # ASSUMPTION: name[i] uses 0-based Python indexing starting at local1
    EBX = 0
    for i in range(local1, length):
        char_val = ord(name[i])
        # EBX = ( EBX * name[i] * local2 ) ^ 0xDD
        # ASSUMPTION: multiplication is standard Python int (can overflow 32-bit)
        # We apply 32-bit signed truncation after each operation to match x86 behavior
        product = ctypes.c_int32(EBX * char_val * local2).value
        EBX = ctypes.c_int32(product ^ 0xDD).value
        if EBX < 0:
            EBX = -EBX

    # Determine EDI based on comparison
    # ASSUMPTION: 0x1CC7D16F and 0xFA91E187 are constants returned by two subroutines
    # when IsDebuggerPresent returns 0 (not being debugged)
    if EBX > ESI:
        EDI = 0x1CC7D16F
    else:
        EDI = ctypes.c_int32(0xFA91E187).value
        if EDI < 0:
            EDI = -EDI

    # abs(EDI) - 0x1CC7D16F is already positive; 0xFA91E187 treated as signed is negative
    if EDI < 0:
        EDI = -EDI

    serial = f"RK302{EDI}Q-ZX{ESI}A-PM{EBX}OU"
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify whether the given serial is valid for the given name.
    """
    if len(name) < 4:
        return False
    expected = keygen(name)
    return serial == expected



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
