import ctypes

def _to_s32(val):
    """Convert to signed 32-bit integer."""
    val = val & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def _to_u32(val):
    return val & 0xFFFFFFFF

def _sar32(val, count):
    """Arithmetic (signed) right shift on 32-bit value."""
    val = _to_s32(val)
    return val >> count

def compute_serial(name: str):
    ebx = 0x49390305  # magic 1
    esi = 0x48631220  # magic 2

    name_bytes = name.encode('latin-1')
    length = len(name_bytes)

    for i in range(length):
        ecx = name_bytes[i]  # mov cl, byte ptr [edi+edx-1]

        ebx = _to_u32(ebx ^ ecx)   # xor ebx, ecx
        esi = _to_u32(esi ^ ebx)   # xor esi, ebx  (after xor with ecx)

        if (ebx & 0x01) != 0:
            # test bl, 01 -> je branch NOT taken
            # sar ebx, 1
            ebx_s = _sar32(ebx, 1)
            # jns -> if sign flag not set (result >= 0), skip adc
            # adc ebx, 0 adds carry; after sar if sign bit was set (negative result),
            # the carry from the shift is added.
            # ASSUMPTION: 'adc ebx, 00' adds the carry bit (bit shifted out) to ebx.
            # After arithmetic right shift of a negative number by 1,
            # carry = original bit 0 (which is 1 here since we are in the odd branch).
            # So if result is negative (sign set), add 1.
            if ebx_s < 0:  # jns not taken -> adc
                ebx_s = ebx_s + 1  # carry = 1 (the bit shifted out was 1)
            ebx = _to_u32(ebx_s)
            ebx = _to_u32(ebx ^ 0x01200311)  # xor ebx, 01200311
        else:
            # test bl, 01 -> je branch taken
            ebx_s = _sar32(ebx, 1)
            if ebx_s < 0:  # jns not taken -> adc
                ebx_s = ebx_s + 1  # ASSUMPTION: carry=0 here since bl was even (bit0=0)
                # ASSUMPTION: carry from sar when bit0=0 is 0, so adc adds 0
                # Actually adc ebx,0 adds CF; CF after sar = last bit shifted out = bit0 of original = 0
                # So we should NOT add 1 here. Correcting:
                ebx_s = ebx_s  # no carry added (CF=0)
            ebx = _to_u32(ebx_s)
            # no xor with 01200311 in this branch

    return ebx, esi

def _fix_adc(ebx_before_sar, carry_bit):
    """Helper: perform sar+adc correctly."""
    ebx_s = _sar32(ebx_before_sar, 1)
    if ebx_s < 0:  # sign flag set -> jns not taken -> adc
        ebx_s = ebx_s + carry_bit
    return _to_u32(ebx_s)

def compute_serial_v2(name: str):
    """Corrected version with proper carry handling."""
    ebx = 0x49390305
    esi = 0x48631220

    name_bytes = name.encode('latin-1')
    length = len(name_bytes)

    for i in range(length):
        ecx = name_bytes[i]

        ebx = _to_u32(ebx ^ ecx)
        esi = _to_u32(esi ^ ebx)

        bit0 = ebx & 0x01  # carry for adc = bit shifted out = original bit0

        if bit0 != 0:  # odd branch
            ebx = _fix_adc(ebx, carry_bit=1)
            ebx = _to_u32(ebx ^ 0x01200311)
        else:  # even branch
            ebx = _fix_adc(ebx, carry_bit=0)
            # no xor

    return ebx, esi

def build_serial(ebx, esi):
    part1 = ebx & 0x0000FFFF
    part2 = (ebx >> 16) & 0x0000FFFF
    part3 = esi & 0x0000FFFF
    part4 = (esi >> 16) & 0x0000FFFF
    return '{:04X}-{:04X}-{:04X}-{:04X}'.format(part1, part2, part3, part4)

def keygen(name: str) -> str:
    ebx, esi = compute_serial_v2(name)
    return build_serial(ebx, esi)

def verify(name: str, serial: str) -> bool:
    expected = keygen(name)
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
