import ctypes

def _to_int64(v):
    """Clamp to signed 64-bit."""
    v = v & 0xFFFFFFFFFFFFFFFF
    if v >= 0x8000000000000000:
        v -= 0x10000000000000000
    return v

def _to_uint64(v):
    return v & 0xFFFFFFFFFFFFFFFF

def _llmul(a, b):
    """64-bit multiply (unsigned, keep lower 64 bits)."""
    return _to_uint64(a * b)

def _lldiv(num, den):
    """64-bit signed division."""
    # treat as signed
    def to_signed(v):
        v = v & 0xFFFFFFFFFFFFFFFF
        if v >= 0x8000000000000000:
            v -= 0x10000000000000000
        return v
    sn = to_signed(num)
    sd = to_signed(den)
    if sd == 0:
        raise ZeroDivisionError
    # truncate toward zero
    result = int(sn / sd)
    return _to_uint64(result)

# ASSUMPTION: dword_4648AC = 0xFFA based on the disassembly comment
CONST_FFA = 0xFFA

def _compute_serial(name):
    name_len = len(name)          # strlen(name)
    name_len64 = _to_uint64(name_len)

    # sum of ASCII values of name characters
    ascii_sum = 0
    for ch in name:
        ascii_sum = _to_uint64(ascii_sum + ord(ch))

    # --- generate_correct_serial section ---
    # push strlen, 0, strlen, 0  => two 64-bit args both = strlen
    # eax = CONST_FFA; cdq => edx=0
    # __LLMUL(CONST_FFA * strlen) => part1
    part1 = _llmul(CONST_FFA, name_len64)

    # push strlen, 0, strlen, 0  => same args again
    # __LLMUL(CONST_FFA * strlen) => part2 (same)
    part2 = _llmul(CONST_FFA, name_len64)

    # __LLMUL(part1 * part2)
    numerator = _llmul(part1, part2)

    # __LLDIV(numerator / (strlen * strlen))
    # ASSUMPTION: the denominator is strlen^2 based on push pattern
    denominator = _llmul(name_len64, name_len64)
    if denominator == 0:
        # ASSUMPTION: avoid div-by-zero for empty name
        denominator = 1
    var_10 = _lldiv(numerator, denominator)

    # ascii_sum <<= 0xA (10 bits)
    ascii_sum_shifted = _to_uint64(ascii_sum << 10)

    # var_10 = var_10 * ascii_sum_shifted
    var_10 = _llmul(var_10, ascii_sum_shifted)

    # zero upper 32 bits: xor edx,edx => keep only lower 32 bits
    var_10 = var_10 & 0xFFFFFFFF

    # xor with strlen (lower), xor with 0 (upper)
    var_10 = _to_uint64(var_10 ^ name_len64)

    # ASSUMPTION: the final serial is var_10 (64-bit number) converted to decimal string
    # and then multiplied by 16 to reverse the initial shrd/shr by 4
    # (serial / 16 XOR strlen = var_10  =>  serial = (var_10 XOR strlen) * 16)
    # But XOR happens after division, so:
    # step1 = serial_int >> 4
    # step2 = step1 XOR strlen
    # step2 must equal var_10
    # => step1 = var_10 XOR strlen
    # => serial_int = step1 << 4  (since shrd by 4 = divide by 16 for 64-bit)
    step1 = _to_uint64(var_10 ^ name_len64)
    serial_int = _to_uint64(step1 << 4)

    return serial_int

def keygen(name):
    if not name:
        return "0"
    serial_int = _compute_serial(name)
    return str(serial_int)

def verify(name, serial):
    """
    Reconstruct the check:
    1. serial -> int64 via StrToInt64
    2. serial_int >> 4  (shrd/shr by 4)
    3. XOR with strlen(name)
    4. Compare against computed var_10
    """
    try:
        serial_int = int(serial)
    except ValueError:
        return False

    name_len = len(name)
    name_len64 = _to_uint64(name_len)

    # step1: serial >> 4
    serial_uint = _to_uint64(serial_int)
    divided = _to_uint64(serial_uint >> 4)

    # step2: XOR strlen
    xored_lower = _to_uint64(divided ^ name_len64)
    # upper word XOR 0 = unchanged (upper is 0 for reasonable serials)
    var_28 = xored_lower

    # compute expected value
    ascii_sum = 0
    for ch in name:
        ascii_sum = _to_uint64(ascii_sum + ord(ch))

    part1 = _llmul(CONST_FFA, name_len64)
    part2 = _llmul(CONST_FFA, name_len64)
    numerator = _llmul(part1, part2)
    denominator = _llmul(name_len64, name_len64)
    if denominator == 0:
        denominator = 1
    var_10 = _lldiv(numerator, denominator)
    ascii_sum_shifted = _to_uint64(ascii_sum << 10)
    var_10 = _llmul(var_10, ascii_sum_shifted)
    var_10 = var_10 & 0xFFFFFFFF
    var_10 = _to_uint64(var_10 ^ name_len64)

    return var_28 == var_10


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
