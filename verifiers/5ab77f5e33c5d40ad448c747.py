# Keygen for JamesCrackme V2 by jamesinuk
# Reconstructed from multiple solution write-ups (mj_keygen.cpp, Keygen.asm, Src.txt)
#
# The crackme takes:
#   name        : 3-15 chars
#   code        : exactly 10 chars (authorization code)
#   serial      : name-f1-f3-f4-f2  (computed as below)
#
# Serial format: <name>-<dwFirst>-<dwThird>-<dwFourth>-<dwSecond>
#
# Per iteration i (0-indexed, over name length):
#   edx = ord(name[i]) + ord(code[i])
#   eax = edx
#   eax = eax << 2          # shl 2
#   eax = eax + edx         # add edx
#   eax = eax + eax         # double
#   dwFirst  = eax                  (last iteration value)
#   dwSecond = eax + 0xBB8          (last iteration value)
#   tmp      = ord(code[i]) - 0x94
#   dwThird  = tmp                  (last iteration value)
#   dwFourth = dwFourth + tmp - 0xFA0  (accumulated)
#
# Confirmed by all three solutions (C++, Pascal, ASM).

CODELETTERVAL = 0x94    # 148
CODETOTALVAL  = 0xBB8   # 3000
MISCTOTALVAL  = 0xFA0   # 4000
DEFAULT_CODE  = "0000000000"  # 10-char authorization code used by mj_keygen


def _compute(name: str, code: str):
    """Core computation shared by verify and keygen."""
    assert len(code) == 10, "Authorization code must be exactly 10 characters"
    assert 3 <= len(name) <= 15, "Name must be 3-15 characters"

    dwFirst  = 0
    dwSecond = 0
    dwThird  = 0
    dwFourth = 0  # accumulates across iterations

    for i in range(len(name)):
        name_char = ord(name[i])
        code_char = ord(code[i])

        # Compute the (name[i] + code[i]) expression
        edx = name_char + code_char
        eax = edx
        eax = (eax << 2) & 0xFFFFFFFF   # shl 2 (keep 32-bit, but Python ints are unbounded)
        eax = eax + edx
        eax = eax + eax
        # Treat as signed 32-bit for output consistency
        dwFirst = eax

        dwSecond = eax + CODETOTALVAL

        tmp = code_char - CODELETTERVAL  # code[i] - 0x94
        dwThird = tmp

        dwFourth = dwFourth + tmp - MISCTOTALVAL

    # Convert to signed 32-bit integers (match C int behaviour for output)
    def to_signed32(v):
        v = v & 0xFFFFFFFF
        if v >= 0x80000000:
            v -= 0x100000000
        return v

    return (to_signed32(dwFirst), to_signed32(dwSecond),
            to_signed32(dwThird), to_signed32(dwFourth))


def keygen(name: str, code: str = DEFAULT_CODE) -> str:
    """
    Generate a valid serial for the given name and authorization code.
    The serial format is: name-dwFirst-dwThird-dwFourth-dwSecond
    (confirmed by mj_keygen.cpp output line and Keygen.asm wsprintf call)
    """
    if not (3 <= len(name) <= 15):
        raise ValueError("Name must be 3-15 characters")
    if len(code) != 10:
        raise ValueError("Authorization code must be exactly 10 characters")

    dwFirst, dwSecond, dwThird, dwFourth = _compute(name, code)
    return f"{name}-{dwFirst}-{dwThird}-{dwFourth}-{dwSecond}"


def verify(name: str, serial: str, code: str = DEFAULT_CODE) -> bool:
    """
    Verify that serial matches the expected value for name+code.
    """
    try:
        expected = keygen(name, code)
        return serial == expected
    except ValueError:
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
