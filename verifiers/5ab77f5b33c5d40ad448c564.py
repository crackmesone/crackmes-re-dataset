# Keygen for SMoKE KeyGenME N1
# Based on the C++ inline ASM keygen by TSCube and ASM source by _Nordic_
# The algorithm is fully described in the keygen source.

def verify(name: str, serial: str) -> bool:
    expected = keygen(name)
    if expected is None:
        return False
    return serial == expected


def keygen(name: str) -> str:
    if len(name) < 5:
        return None

    magic1 = b"B1A4F6920C8"  # 11 bytes, indices 0..10
    magic2 = b"KPLT"          # 4 bytes, indices 0..3
    # Initial template for the serial (25 chars)
    szTmpSerial = bytearray(b"A0YTR765JUY3KD76DMH3FDJ4M")

    name_bytes = [ord(c) for c in name]
    nameLen = len(name_bytes)

    # --- Loop 1: sum all bytes of name -> ebpm14 (not used later in serial generation directly)
    ebpm14 = sum(name_bytes)

    # --- Loop 2: sum odd-indexed bytes (1-based odd = index 0,2,4,...) -> edi
    edi = 0
    ebx = 1  # 1-based
    while ebx <= nameLen:
        edi += name_bytes[ebx - 1]
        ebx += 2

    # --- Loop 3: sum even-indexed bytes (1-based even = index 1,3,5,...) -> ebpm18
    ebpm18 = 0
    ebx = 2  # 1-based
    while ebx <= nameLen:
        ebpm18 += name_bytes[ebx - 1]
        ebx += 2

    # tmpv1 = edi * ebpm18  (low 32 bits, signed)
    # In the original: imul gives 64-bit result, but only eax (low 32) is stored
    ebpm1C = (edi * ebpm18) & 0xFFFFFFFF
    # treat as signed 32-bit
    if ebpm1C >= 0x80000000:
        ebpm1C -= 0x100000000

    # Helper: signed 32-bit
    def s32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    def u32(v):
        return v & 0xFFFFFFFF

    def idiv32(a, b):
        """C-style signed integer division (truncate toward zero), returns (quotient, remainder)"""
        a = s32(a)
        b = s32(b)
        if b == 0:
            raise ZeroDivisionError
        q = int(a / b)  # truncate toward zero
        r = a - q * b
        return q, r

    # --- Loop 4: uses ebpm1C (tmpv1), fills odd positions of szTmpSerial
    ebx = 1
    while True:
        if ebpm1C == 0:
            break
        if ebx > 0x19:  # 25
            break
        # divide twice by 0Bh
        ebpm1C, _ = idiv32(ebpm1C, 0x0B)
        ebpm1C = s32(ebpm1C)
        _, edx_rem = idiv32(ebpm1C, 0x0B)
        esi = edx_rem  # remainder
        # index into magic1: (0Bh - esi) - 1  => 0-based
        idx = (0x0B - esi) - 1
        idx = idx % 11  # ASSUMPTION: clamp/wrap to valid magic1 index
        dl = magic1[idx]
        szTmpSerial[ebx - 1] = dl
        ebx += 2

    # --- Loop 5: uses edi (odd-bytes sum), fills from position 25 downward
    ebx = 0x19  # 25
    while True:
        if edi == 0:
            break
        if ebx < 1:
            break
        edi, _ = idiv32(edi, 0x0B)
        edi = s32(edi)
        _, edx_rem = idiv32(edi, 0x0B)
        esi = edx_rem
        idx = (0x0B - esi) - 1
        idx = idx % 11  # ASSUMPTION: clamp/wrap
        dl = magic1[idx]
        szTmpSerial[ebx - 1] = dl
        ebx -= 1

    # --- Loop 6: uses ebpm18 (even-bytes sum), fills odd positions with magic2
    ebx = 1
    while True:
        if ebpm18 == 0:
            break
        if ebx > 0x19:
            break
        eax = s32(ebpm18)
        if eax < 0:
            eax += 3
        eax = eax >> 2  # sar eax, 2  (arithmetic right shift)
        ebpm18 = s32(eax)
        esi = s32(ebpm18)
        esi_u = u32(esi) & 0x80000003
        # check sign of esi_u interpreted as s32
        if esi_u >= 0x80000000:
            esi_u = u32(esi_u - 1)
            esi_u = u32(esi_u | 0xFFFFFFFC)
            esi_u = u32(esi_u + 1)
        esi = s32(esi_u)
        edx = 4 - esi
        idx = edx - 1
        idx = idx % 4  # ASSUMPTION: clamp/wrap to valid magic2 index
        dl = magic2[idx]
        szTmpSerial[ebx - 1] = dl
        ebx += 2

    # --- Loop 7: for each char in name (forward), name[i] % 0x0B -> magic1 lookup, overwrite pos i
    esi = nameLen
    if esi > 0:
        ebx = 1
        while esi > 0:
            edi_v = name_bytes[ebx - 1]
            _, edx_rem = idiv32(edi_v, 0x0B)
            edi_v = edx_rem
            idx = (0x0B - edi_v) - 1
            idx = idx % 11  # ASSUMPTION
            dl = magic1[idx]
            szTmpSerial[ebx - 1] = dl
            ebx += 1
            esi -= 1

    # --- Loop 8: for each char in name (backward), fills middle positions with magic2
    ebx = nameLen
    while ebx >= 1:
        edi_v = name_bytes[ebx - 1]
        edi_u = u32(edi_v) & 0x80000003
        if edi_u >= 0x80000000:
            edi_u = u32(edi_u - 1)
            edi_u = u32(edi_u | 0xFFFFFFFC)
            edi_u = u32(edi_u + 1)
        edi_v = s32(edi_u)
        # compute position in szTmpSerial: ecx = 0Ch - (ebx >> 1)
        edx2 = ebx
        # sar edx, 1
        if edx2 < 0:
            edx2 = (edx2 + 1) >> 1  # arithmetic right shift for negative
        else:
            edx2 = edx2 >> 1
        ecx = 0x0C - edx2
        edx3 = 4 - edi_v
        idx = edx3 - 1
        idx = idx % 4  # ASSUMPTION
        dl = magic2[idx]
        pos = ecx - 1
        if 0 <= pos < 25:
            szTmpSerial[pos] = dl
        ebx -= 1
        if ebx == 0:
            break

    # --- Loop 9 (from _Nordic_ keygen): uses tmpv3 (sum of all bytes)
    # For each name char forward: (tmpv3 - char_val) mod 3 -> magic2 lookup; fills some positions
    # ASSUMPTION: based on _Nordic_'s j1A2 loop description (truncated), partial reconstruction
    tmpv3 = ebpm14  # sum of all name bytes
    esi = nameLen
    if esi > 0:
        ebx = 1
        while esi > 0:
            edx_v = name_bytes[ebx - 1]
            ecx_v = tmpv3 - edx_v
            ecx_u = u32(ecx_v) & 0x80000003
            if ecx_u >= 0x80000000:
                ecx_u = u32(ecx_u - 1)
                ecx_u = u32(ecx_u | 0xFFFFFFFC)
                ecx_u = u32(ecx_u + 1)
            esi_v = s32(ecx_u)
            # ASSUMPTION: similar to loop6, uses magic2 at position (4 - esi_v)
            edx_idx = 4 - esi_v
            idx = (edx_idx - 1) % 4
            dl = magic2[idx]
            # ASSUMPTION: writes to szTmpSerial at some position derived from ebx
            # Based on _Nordic_ source: mov byte ptr [eax+ecx-01], dl where ecx derived from DWord1
            # We skip this loop as it's truncated - mark as ASSUMPTION
            # ASSUMPTION: this loop may overwrite more positions; without full source we skip
            ebx += 1
            esi -= 1

    return szTmpSerial.decode('ascii', errors='replace')



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
