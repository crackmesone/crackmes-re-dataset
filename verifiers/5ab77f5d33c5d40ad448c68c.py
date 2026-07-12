import ctypes

part0 = [
    "Bill Gates ", "Linus Thorwald ", "Some guy ", "The cow ", "The pizza ", "Cthulhu ", "My lawyer ",
    "Everybody ", "Elvis ", "Santa Claus ", "Chewing gum ", "Your mother ", "Arthur Dent "
]

part1 = [
    "killed ", "stole ", "kisses ", "secretly loves ", "paints ", "reads ", "eats ", "dismisses ", "publicly criticises "
]

part2 = [
    "typewriters ", "Ollydbg ", "princess Leia ", "Denmark ", "cellphones ", "seven dwarves ", "navel fluff ",
    "beer ", "lipstick ", "the Pope ", "the meaning of life "
]

part3 = [
    "and ", "because ", "but ", "until ", "for it is foretold that ", "while "
]

part4 = [
    "your missing sock ", "Mozart ", "the universe ", "nobody ", "my playstation ",
    "the girl next door ", "everything you ever wanted "
]

part5 = [
    "should be kept refridgerated.", "spontaneously combusts.", "can't sing.", "is missing a tooth.",
    "doesn't have a spam filter.", "sucks.", "dumped core.", "feels a disturbance in the force.",
    "is machine washable."
]


def _to_i32(v):
    """Truncate to signed 32-bit integer (mimic C int overflow)."""
    return ctypes.c_int32(v).value


def get_name_seed(name: str) -> int:
    """Reproduce the x86 assembly hash function from the keygen."""
    var1 = 0xEEA3
    var2 = 0x195A3
    var3 = 0x17E7F

    for ch in name:
        c = ord(ch)
        # movsx edx, byte ptr [ecx]  -> sign-extend byte
        c_signed = ctypes.c_int8(c).value

        # var1 = var1 * c_signed
        var1 = _to_i32(var1 * c_signed)
        # var1 = var1 + 0x17299
        var1 = _to_i32(var1 + 0x17299)

        # var2 = var2 + c_signed
        var2 = _to_i32(var2 + c_signed)
        # var2 = var2 * 0x18757
        var2 = _to_i32(var2 * 0x18757)

        # var3 = var3 << 2
        var3 = _to_i32(var3 << 2)
        # var3 = var3 ^ c_signed
        var3 = _to_i32(var3 ^ c_signed)

    # ecx = var1 ^ var2 ^ var3
    ecx = _to_i32(var1 ^ var2 ^ var3)

    # Final: eax = ecx (treated as unsigned for division)
    eax = ecx & 0xFFFFFFFF  # unsigned 32-bit
    # xor edx, edx ; mov ecx, 486486 ; div ecx -> edx = eax % 486486
    result = eax % 486486
    return result


def keygen(name: str):
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters.")

    name_seed = get_name_seed(name)

    code = [0] * 6

    code[5] = name_seed // 54054
    if code[5] >= len(part5):
        code[5] = len(part5) - 1
    name_seed = name_seed - code[5] * 54054

    code[4] = name_seed // 7722
    if code[4] >= len(part4):
        code[4] = len(part4) - 1
    name_seed = name_seed - code[4] * 7722

    code[3] = name_seed // 1287
    if code[3] >= len(part3):
        code[3] = len(part3) - 1
    name_seed = name_seed - code[3] * 1287

    code[2] = name_seed // 117
    if code[2] >= len(part2):
        code[2] = len(part2) - 1
    name_seed = name_seed - code[2] * 117

    code[1] = name_seed // 13
    if code[1] >= len(part1):
        code[1] = len(part1) - 1
    name_seed = name_seed - code[1] * 13
    code[1] = 8 - code[1]  # note: invert index for part1

    code[0] = name_seed
    if code[0] >= len(part0):
        return None  # Can't find serial for this name

    serial = (
        part0[code[0]] + part1[code[1]] + part2[code[2]] +
        part3[code[3]] + part4[code[4]] + part5[code[5]]
    )
    return serial


def verify(name: str, serial: str) -> bool:
    if len(name) < 5:
        return False
    expected = keygen(name)
    if expected is None:
        return False
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
