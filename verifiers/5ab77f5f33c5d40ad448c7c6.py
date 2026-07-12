import ctypes

def _to_int32(v):
    """Truncate to signed 32-bit integer (simulates x86 register overflow)."""
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def _to_uint32(v):
    return v & 0xFFFFFFFF


def compute_key1_key2(name_upper: str, pcname_upper: str):
    """
    BLOCK1: sum of username chars, then subtract pcname chars -> EBX
    BLOCK2: apply math transformations -> KEY1 (EBX), KEY2 (ESI = EBX * len(pcname))
    All arithmetic is 32-bit (signed for IMUL, truncated via hex conversion trick).
    """
    ebx = 0

    # Sum of uppercase username chars
    for ch in name_upper:
        ebx = _to_int32(ebx + ord(ch))

    # Subtract pcname chars
    for ch in pcname_upper:
        ebx = _to_int32(ebx - ord(ch))

    # BLOCK2 math (replicates the assembly exactly)
    # 0046B341: IMUL EBX  -> EDX:EAX = EBX * EBX  (EAX = low 32 bits)
    eax = _to_int32(ebx)
    eax = _to_int32(eax * eax)          # IMUL EBX (EAX = low 32 of EBX^2)

    # 0046B343: XOR EAX, 0DEADh
    eax = _to_int32(_to_uint32(eax) ^ 0xDEAD)

    # 0046B348: MOV EBX, EAX
    ebx = eax

    # 0046B34A: ADD EBX, 69220368h
    ebx = _to_int32(_to_uint32(ebx) + 0x69220368)

    # 0046B350: XOR EBX, 7D6h
    ebx = _to_int32(_to_uint32(ebx) ^ 0x7D6)

    # 0046B356: IMUL EAX, EBX, 2007h
    eax = _to_int32(ebx * 0x2007)

    # 0046B35C: IMUL EAX, EAX, 2008h
    eax = _to_int32(eax * 0x2008)

    # 0046B362: MOV EBX, EAX
    ebx = eax

    # 0046B364: MOV EAX, EBX
    eax = ebx

    # 0046B366: ADD EAX, EAX  (eax *= 2)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax))

    # 0046B368: LEA EAX, [EAX + EAX*4]  (eax *= 5)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax) * 4)

    # 0046B36B: IMUL EAX, EAX, 0Bh
    eax = _to_int32(eax * 0x0B)

    # 0046B36E: ADD EAX, EAX  (eax *= 2)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax))

    # 0046B370: ADD EAX, EAX  (eax *= 2)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax))

    # 0046B372: LEA EAX, [EAX + EAX*2]  (eax *= 3)
    eax = _to_int32(_to_uint32(eax) + _to_uint32(eax) * 2)

    # 0046B375: MOV EBX, EAX
    ebx = eax

    # 0046B377: IMUL EBX, EBX, 6F644372h
    ebx = _to_int32(ebx * 0x6F644372)

    # 0046B37D: IMUL EBX, EBX, F6279CDAh  (signed: this is negative)
    ebx = _to_int32(ebx * _to_int32(0xF6279CDA))

    # 0046B383: ADD EBX, 60BA28F5h
    ebx = _to_int32(_to_uint32(ebx) + 0x60BA28F5)

    # 0046B389: IMUL EBX, EBX, 3A7BEDB2h
    ebx = _to_int32(ebx * 0x3A7BEDB2)

    # EBX = KEY1
    key1 = _to_uint32(ebx)

    # 0046B399: IMUL ESI, EBX  where ESI = len(pcname)
    esi = len(pcname_upper)
    esi = _to_int32(esi * ebx)
    key2 = _to_uint32(esi)

    return key1, key2


def keygen(name: str, pcname: str = None) -> str:
    """
    Generate serial for given name and PC name.
    PC name must be provided; in the original crackme it's read from the registry.
    Serial format: KEY2-KEY1<PCNAME>  (uppercase)
    Note: KEY2 has leading zero stripped if present (as in BaKaE's keygen).
    """
    # ASSUMPTION: pcname must be supplied by the caller (registry key not available here)
    if pcname is None:
        raise ValueError("pcname must be provided (read from registry on target machine)")

    name_upper = name.upper()
    pcname_upper = pcname.upper()

    key1, key2 = compute_key1_key2(name_upper, pcname_upper)

    key1_hex = format(key1, '08X')
    key2_hex = format(key2, '08X')

    # Strip leading zero from key2 part if first char is '0' (matches BaKaE's keygen logic)
    # ASSUMPTION: only strip a single leading '0' as shown in the Delphi source
    if key2_hex.startswith('0'):
        key2_hex = key2_hex[1:]

    serial = key2_hex + '-' + key1_hex + pcname_upper
    return serial


def verify(name: str, serial: str, pcname: str = None) -> bool:
    """
    Verify name/serial pair.
    pcname must be provided.
    """
    if pcname is None:
        raise ValueError("pcname must be provided")
    expected = keygen(name, pcname)
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
