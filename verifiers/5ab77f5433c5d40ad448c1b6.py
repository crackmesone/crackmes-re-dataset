magic = b'.rESISTANCe.is.fUTILe.'

def compute_serial(name: str) -> int:
    """
    Reimplementation of the assembly loop from the crackme.

    Assembly logic (per-iteration, index ecx starting at 0):
      dl  = name[ecx]          (b)
      al  = magic[ecx]         (m)
      ebx = ebx + b            (add ebx, edx  where edx = sign-extend(b))
      edx = m
      eax = ecx                (l = number of bytes processed so far)
      edx = edx >> cl          (shr edx, cl  -- shift m right by ecx bits)
      ecx += 1
      bl  = bl + 0x30          (add only the low byte of ebx, with carry into higher bytes)
      esi = ebx

    Note: 'add bl, 0x30' only adds to the low byte (bl), which in Python we
    simulate by keeping ebx as a 32-bit unsigned integer and only adding 0x30
    to the low byte.

    The final serial is esi (== ebx after the last iteration) treated as a
    32-bit unsigned integer, then printed with %lu (unsigned long).
    """
    name_bytes = name.encode('latin-1')
    ebx = 0
    ecx = 0

    for i, b in enumerate(name_bytes):
        ecx = i
        # dl = b (sign-extended to 32-bit, but we treat as signed int)
        edx = b  # name byte
        # al = magic[ecx % len(magic)] -- magic is 22 chars + NUL
        # ASSUMPTION: if name is longer than magic string, magic wraps or gives 0;
        # the crackme appears to index magic directly. Since magic has 22 chars,
        # for names longer than 22 chars magic[ecx] would read into surrounding
        # memory. We assume magic bytes beyond index 21 are 0 (NUL terminator onward).
        if ecx < len(magic):
            m = magic[ecx]
        else:
            m = 0  # ASSUMPTION: beyond magic length, treat as 0

        eax_m = m  # movsx eax, al (sign-extend byte to dword)
        # add ebx, edx (edx is sign-extended b)
        # treat edx as signed byte sign-extended to 32-bit
        edx_signed = b if b < 128 else b - 256
        ebx = (ebx + edx_signed) & 0xFFFFFFFF

        # edx = eax_m (m)
        edx2 = eax_m
        # eax = ecx (l = current index before increment)
        # shr edx, cl  -- shift by ecx (which is i, the current 0-based index)
        # note: x86 shr uses cl mod 32
        shift = ecx & 0x1F
        edx2 = (edx2 >> shift) & 0xFFFFFFFF

        # ecx += 1 (done by loop, ecx becomes i+1 for next iteration)
        # add bl, 0x30 -- only low byte of ebx
        low_byte = (ebx & 0xFF) + 0x30
        ebx = (ebx & 0xFFFFFF00) | (low_byte & 0xFF)
        # carry from low byte into rest of ebx
        if low_byte > 0xFF:
            carry = low_byte >> 8
            ebx = (ebx & 0xFFFFFF00) | ((ebx >> 8) + carry) << 8
            # Re-do properly:
            # Actually simulate the 32-bit add of 0x30 to the full ebx
            # but 'add bl, 0x30' only affects bl (8-bit add with 8-bit result)
            # It does NOT carry into bh; x86 'add bl, imm8' is an 8-bit op.
            pass

        # esi = ebx
    esi = ebx
    # Return as unsigned 32-bit
    return esi & 0xFFFFFFFF


def compute_serial_v2(name: str) -> int:
    """
    Cleaner reimplementation. Key insight: 'add bl, 0x30' is an 8-bit addition
    (does NOT propagate carry to bh/ebx upper bytes). We track ebx as a
    Python int but simulate 8-bit add for the bl += 0x30 step.
    """
    name_bytes = name.encode('latin-1')
    ebx = 0  # 32-bit register

    for ecx, b in enumerate(name_bytes):
        # b = name byte (dl, sign-extended)
        b_signed = b if b < 128 else b - 256

        # add ebx, sign_extend(b)  --> 32-bit add
        ebx = (ebx + b_signed) & 0xFFFFFFFF

        # add bl, 0x30  --> 8-bit add, no carry to upper bytes
        bl = (ebx & 0xFF) + 0x30
        bl = bl & 0xFF  # 8-bit truncation, carry lost
        ebx = (ebx & 0xFFFFFF00) | bl

        # esi = ebx (updated each iteration)

    esi = ebx & 0xFFFFFFFF
    return esi


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    computed = compute_serial_v2(name)
    return serial_int == computed


def keygen(name: str) -> str:
    """Generate the correct serial for a given name."""
    return str(compute_serial_v2(name))



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
