# Reverse-engineered from the writeup for 'The New Year Crackme' by kaizer_by
# The writeup was truncated and the full algorithm was not shown.
# This implementation reconstructs what was visible in the assembly listing.
# Many parts are ASSUMPTIONS due to truncation.

import ctypes

def _u32(v):
    """Truncate to 32-bit unsigned."""
    return v & 0xFFFFFFFF

def _s32(v):
    """Interpret as signed 32-bit."""
    v = _u32(v)
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def compute_serial_parts(name):
    """
    Reconstruct the serial computation from the visible assembly.
    The writeup shows:
      1. Sum all character ordinals of the name -> esi (let's call it S)
      2. ebx = len(name) (recomputed from a second call, same name) -> L
      3. Several 32-bit constants are stored but not fully used visibly.
      4. A series of arithmetic expressions using S and L produce serial parts.

    From the assembly:
      eax = S + L + 1                   (LEA EAX, [ESI+EBX+1])
      edx_a8 = 2*S + L                  (edx = esi; edx+=edx; edx+=ebx) -> [ebp-58]
      edx_a4 = L + 3 - S               ([ebp-5C])
      edx_a0 = edx_a8 + eax + edx_a4 + S  ([ebp-60])
      ecx = S + edx_a8                  
      edx_9c = eax + 1 + ecx + (edx_a4+1)*S*S*S  ([ebp-64])
      edx_98 = edx_a0 * S + edx_9c - (S - ebx_initial_sum_minus_ebx)  ([ebp-68])
        Note: [ebp-30] = ESI - EBX where EBX was some initial value (ASSUMPTION: 0)
      edx_part_next = edx_9c * edx_98  (IMUL EDX, [ebp-98]) - truncated

    ASSUMPTION: ESI starts at 0, EBX starts at 0 (uninitialized Delphi locals).
    ASSUMPTION: The serial is formatted as the computed parts joined by dashes.
    ASSUMPTION: The description says '9 dynamic and 1 static parts'.
    """
    # ASSUMPTION: esi and ebx start at 0
    esi = 0  # accumulator for char sum
    ebx_init = 0  # ASSUMPTION: uninitialized, treated as 0

    # Part 1: sum all chars of name into esi
    S = 0
    for ch in name:
        S = _s32(S + ord(ch))

    L = len(name)

    # [ebp-30] = esi - ebx  (ebx was some prior value, ASSUMPTION: 0)
    val_D0 = _s32(S - ebx_init)

    # [ebp-58] = 2*S + L
    val_A8 = _s32(2 * S + L)

    # [ebp-5C] = L + 3 - S
    val_A4 = _s32(L + 3 - S)

    # eax = S + L + 1
    eax = _s32(S + L + 1)

    # [ebp-60] = val_A8 + eax + val_A4 + S
    val_A0 = _s32(val_A8 + eax + val_A4 + S)

    # ecx = S + val_A8
    ecx = _s32(S + val_A8)

    # [ebp-64] = (eax+1) + ecx + (val_A4+1)*S*S*S
    val_9C = _s32((eax + 1) + ecx + _s32(_s32(_s32((val_A4 + 1) * S) * S) * S))

    # [ebp-68] = val_A0 * S + val_9C - val_D0
    val_98 = _s32(_s32(val_A0 * S) + val_9C - val_D0)

    # ASSUMPTION: next part = val_9C * val_98 (writeup truncated here)
    val_next = _s32(val_9C * val_98)

    # ASSUMPTION: The 8 constants stored are compared or XORed with computed parts
    # Constants from assembly:
    CONST = [
        0xC346D350,  # [ebp-38]
        0x6D460CA6,  # [ebp-3C]  (note: stored as 6D460CA6 but MOV showed A60C466D -- little-endian)
        0x86FFCD21,  # [ebp-40]
        0x65B484DF,  # [ebp-44]
        0xB2DF0517,  # [ebp-48]
        0x4427BD41,  # [ebp-4C]
        0xDCD425F1,  # [ebp-50]
        0xD7707667,  # [ebp-54]
    ]
    # ASSUMPTION: serial parts are the computed values as decimal strings joined by '-'
    # Based on writeup: '9 dynamic and 1 static parts'
    parts = [
        str(_u32(val_D0)),
        str(_u32(val_A8)),
        str(_u32(val_A4)),
        str(_u32(eax)),
        str(_u32(val_A0)),
        str(_u32(ecx)),
        str(_u32(val_9C)),
        str(_u32(val_98)),
        str(_u32(val_next)),
    ]
    return parts


def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: serial format is parts joined by '-'.
    NOTE: The writeup explicitly states serials vary per machine due to
    uninitialized variables (ESI, EBX depend on runtime stack state).
    This keygen cannot produce correct serials without knowing those runtime values.
    """
    parts = compute_serial_parts(name)
    return '-'.join(parts)


def verify(name, serial):
    """
    Verify a name/serial pair.
    ASSUMPTION: Compare generated serial with provided serial.
    WARNING: The writeup notes that the serial is machine-dependent due to
    uninitialized variables. This verify() is only an approximation.
    """
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
