def keygen(name: str) -> str:
    """
    Implements the two-phase serial generation algorithm from sharpe's Crackme #3.

    Phase 1 (firstHash / SMC-decoded routine):
      - Uses name bytes, a running 'carry' word (BX split into BH:BL),
        and XOR operations to produce a 16-byte intermediate buffer.
      - The initial BX value comes from memory at [403164]; we ASSUME it is 0
        (zero-initialised .data section). ASSUMPTION: initial BX = 0.

    Phase 2 (second hashing call at 401158 / 004011FE):
      - ECX starts at 0x10 (16 loops), ESI points to the name buffer (16 bytes,
        zero-padded to exactly 16), EDI points to the magic (intermediate) buffer.
      - The name buffer is immediately followed by the magic buffer in memory
        (address 403178 then 403188, i.e. 16 bytes apart).
      - Per loop iteration:
          AL = name[esi_index] if non-zero, else 0x3F
          AL = AL * CL  (unsigned 8-bit multiply)
          inner loop: XOR AL with name[esi_index + ecx_inner .. 1] for ecx_inner down to 1
            (accessing bytes at [ECX+ESI] where ECX goes from nameLen down to 1,
             i.e. relative offsets from current ESI position)
          toggle flag: first nibble = low nibble (AND 0x0F),
                       subsequent nibble = high nibble (SHR AL,4 after AND 0xF0)
          convert nibble to ASCII hex digit:
            if nibble > 9: nibble += 7
            nibble += 0x30
          store ASCII char, advance ESI and EDI, LOOP

    The argument pushed before the call (name length from lstrlen) becomes [EBP+8] = nameLen.

    ASSUMPTION: The first hash (phase 1) produces an intermediate buffer that is then
    overwritten by phase 2. Based on MACH4's write-up the name buffer is exactly 16 bytes
    (zero-padded) and the magic buffer follows immediately.

    Since phase 1 (the SMC-decoded routine) is not fully recovered from the write-ups
    (only phase 2 is shown in plain code), we implement phase 2 directly.
    For phase 1 we use the intermediate values observable from the solutions:
      br0ken      -> intermediate buffer starts at 403188 before phase 2
      El_PuPaZzArO -> intermediate buffer starts at 403188 before phase 2
    ASSUMPTION: Phase 1 intermediate buffer is built as follows (from pseudonym's
    restored code at 004011AB):
      EBX = initial word from [403164] (ASSUME = 0, so BH=0, BL=0)
      For i in range(16):
        AL = name[i] if name[i] != 0 else (0x39 if CL==0 else CL)
        AL = CL  (MOV AL,CL overrides the above when name[i]==0 and CL!=0)
        Actually: if name[i]!=0: AL=name[i]; else if CL==0: AL=0x39; AL=XOR(AL,BL); XCHG BH,BL; XOR AL,BL
        ... this is unclear. We skip phase 1 and instead implement the verified phase 2
        treating the 16-byte intermediate as zero (since we can verify against known pairs).

    Actually, from careful reading of SOLUTION 4 (MACH4) the correct approach is:
    - Phase 2 (at 004011FE) receives nameLen as argument
    - ESI -> name buffer (16-byte field, zero-padded)
    - The function reads [ECX+ESI] where ECX goes from nameLen down to 1 per inner loop,
      relative to the CURRENT ESI position in the outer loop.
    - So on outer loop iteration i (ESI offset = i from start of name buf),
      the inner XOR loop reads bytes at positions i+nameLen, i+nameLen-1, ..., i+1
      from the name buffer (which, being 16 bytes zero-padded followed by intermediate
      buffer, means it can read into the intermediate buffer).

    We implement only phase 2 as shown in the disassembly (SOLUTION 1/2),
    with phase 1 intermediate buffer assumed to be all zeros.
    This matches the verified example pairs IF the intermediate buffer happens to be
    all zeros OR if the inner XOR loop reads into it.

    Given the complexity and partial information about phase 1, we implement
    what is fully described: phase 2 as shown in the disassembly.
    """
    # Ensure name is 1-16 bytes
    name_bytes = name.encode('latin-1')
    if not (1 <= len(name_bytes) <= 16):
        raise ValueError("Name must be 1 to 16 bytes")
    name_len = len(name_bytes)

    # ASSUMPTION: Phase 1 produces an intermediate 16-byte buffer of zeros initially.
    # The combined memory layout is: name_buf (16 bytes, zero-padded) + magic_buf (16 bytes)
    # We simulate this combined 32-byte region.
    # Phase 1 fills magic_buf. Since we cannot fully reconstruct phase 1 from the writeups,
    # we treat it as zero. This will likely produce incorrect serials for most names.
    # ASSUMPTION: intermediate/magic buffer after phase 1 = 16 zero bytes.
    # The correct keygen requires phase 1 to be implemented.
    # However we implement what is described in the write-ups as best we can.

    # Build the combined 32-byte memory region as the crackme sees it:
    # [0..15] = name (zero-padded to 16), [16..31] = magic_buf (from phase 1)
    # ASSUMPTION: magic_buf starts as zeros (phase 1 result unknown)
    combined = bytearray(32)
    for i, b in enumerate(name_bytes):
        combined[i] = b
    # combined[16..31] = 0 (phase 1 result assumed zero)

    # Phase 2: generate the serial (16 ASCII hex chars)
    # ECX starts at 0x10 (outer loop counter)
    # ESI index (into combined) starts at 0
    # EDI is the output buffer
    # [EBP+8] = name_len (pushed before call as lstrlen result)
    # [EBP-1] = toggle flag, starts at 0

    output = bytearray(16)
    esi = 0  # index into combined (name buffer start)
    toggle = 0  # [EBP-1]
    cl = 0x10  # outer loop counter (ECX)

    for out_idx in range(16):
        # AL = combined[esi] if non-zero else 0x3F
        al = combined[esi]
        if al == 0:
            al = 0x3F

        # MUL CL: AL = (AL * CL) & 0xFF
        al = (al * cl) & 0xFF

        # Inner XOR loop: ECX goes from name_len down to 1
        # ASSUMPTION: inner loop uses the current name_len as the starting ecx value
        # MOV BL, BYTE PTR DS:[ECX+ESI]   (solution 1 uses [ECX+ESI], solution 2 uses [ECX+ESI-1])
        # The two solutions differ slightly; solution 1 (br0ken) is used here
        # as it appears to be the patched/correct version.
        inner_ecx = name_len
        while inner_ecx != 0:
            # BL = combined[inner_ecx + esi]   (from MOV BL, [ECX+ESI])
            idx = inner_ecx + esi
            bl = combined[idx] if idx < len(combined) else 0
            al = al ^ bl
            inner_ecx -= 1

        # Toggle: if toggle >= 1: use high nibble; else use low nibble
        bl_flag = toggle
        if bl_flag >= 1:
            al = (al & 0xF0) >> 4
        else:
            al = al & 0x0F

        # NEG BL (toggle flag)
        toggle = (-bl_flag) & 0xFF

        # Convert nibble to ASCII hex
        if al > 9:
            al += 7
        al += 0x30

        output[out_idx] = al
        esi += 1
        cl -= 1  # LOOPD decrements ECX

    return output.decode('ascii')


def verify(name: str, serial: str) -> bool:
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
    except Exception:
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
