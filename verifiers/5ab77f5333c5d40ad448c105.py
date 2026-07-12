import ctypes

def _to_u32(x):
    return x & 0xFFFFFFFF

def _to_u8(x):
    return x & 0xFF

def generate_serial(name):
    """
    Keygen based primarily on mjones' C++ keygen (Solution 1), which is the
    most detailed disassembly-level reconstruction available.
    """
    key = [0x40, 0x5E, 0x2A, 0x52, 0x24, 0x46, 0x56, 0x54, 0x25, 0x40,
           0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
           0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
           0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
           0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    # These match the C++ keygen initial values
    var_eax = 0x22FD00
    var_edx = 0xFAFF7264

    ebp_34c = 0   # v10 / stg5 -- last value of inner loop
    ebp_350 = 0   # v9  / stg3 -- XOR accumulator
    ebp_354 = 0   # v8  / stg4 -- multiply+add accumulator

    n = len(name)

    for i in range(n):
        char_val = ord(name[i])

        var_ebx = char_val
        var_ecx = char_val

        # MOVSX AX, CL  (sign-extend byte to 16-bit, place in low 16 of eax)
        # In practice for printable ASCII the sign bit is 0, so same as zero-extend
        var_eax = (var_eax & 0xffff0000) | (var_ecx & 0xff)
        var_eax = _to_u32(var_eax * 0x67)
        var_eax = var_eax & 0x0000ffff   # MOVZX EAX, AX
        var_eax = var_eax >> 8           # SHR EAX, 8

        # MOV DL, AL
        var_edx = (var_edx & 0xffffff00) | (var_eax & 0xff)

        # SAR DL, 2  (arithmetic right shift preserving sign bit)
        var_dl = _to_u8(var_edx)
        sign_bit = var_dl & 0x80
        var_dl = (var_dl >> 2) | sign_bit  # replicate sign bit
        var_edx = (var_edx & 0xffffff00) | var_dl

        # MOV AL, CL
        var_eax = (var_eax & 0xffffff00) | (var_ecx & 0xff)
        # SAR AL, 7
        al = _to_u8(var_eax)
        # arithmetic shift right 7: result is 0x00 or 0xFF depending on sign bit
        if al & 0x80:
            al_sar7 = 0xFF
        else:
            al_sar7 = 0x00
        var_eax = (var_eax & 0xffffff80) | al_sar7  # per C++ keygen: var_eax &= 0xffffff80 then SAR
        # ASSUMPTION: The C++ keygen does `var_eax &= 0xffffff80` then subtracts low byte;
        # for printable ASCII SAR AL,7 gives 0, so al_sar7 = 0 for normal chars.

        # SUB DL, AL
        dl = _to_u8(var_edx)
        dl = _to_u8(dl - al_sar7)
        var_edx = (var_edx & 0xffffff00) | dl

        # MOV AL, DL
        var_eax = (var_eax & 0xffffff00) | dl

        # SHL AL, 2
        var_al = _to_u8(dl << 2)
        # ADD AL, DL
        var_al = _to_u8(var_al + dl)
        # ADD AL, AL
        var_al = _to_u8(var_al + var_al)

        # SUB CL, AL
        var_cl = _to_u8(var_ecx - var_al)
        var_al = var_cl
        var_ecx = (var_ecx & 0xffffff00) | var_cl
        var_eax = var_al

        # MOVSX EAX, BYTE PTR DS:[EAX+EBP-348]  => key[var_eax]
        # var_eax used as index; for printable ASCII this should be small
        idx = var_eax & 0xff
        key_val = key[idx] if idx < len(key) else 0
        var_eax = key_val

        # XOR EDX, EAX
        var_edx = var_ebx ^ var_eax
        # ADD [ebp_350], EDX
        ebp_350 = _to_u32(ebp_350 + var_edx)

        # Second part of outer loop
        var_edx = char_val
        var_eax = key[i] if i < len(key) else 0
        var_eax = _to_u32(var_eax * var_edx)
        var_eax = _to_u32(var_eax + ebp_354)
        var_eax = _to_u32(var_eax + 0xefef)
        ebp_354 = var_eax

        # Inner loop over all name characters
        for j in range(n):
            char_j = ord(name[j])
            tmp = _to_u32(char_j * char_j)
            tmp = _to_u32(tmp + ebp_354)
            tmp = _to_u32(tmp - ebp_350)
            ebp_34c = tmp

    return ebp_354, ebp_350, ebp_34c


def keygen(name):
    if not name:
        return None
    ebp_354, ebp_350, ebp_34c = generate_serial(name)
    # Format: br0-{ebp_354}-{ebp_350}{ebp_34c}-ken
    return f"br0-{ebp_354}-{ebp_350}{ebp_34c}-ken"


def verify(name, serial):
    if not name:
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
