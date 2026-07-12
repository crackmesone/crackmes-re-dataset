import random
import re

# Map each character to its effect on the running value (res/ebx)
CHAR_OPS = {
    '0': ('sub', 0x1388),
    '1': ('add', 0x3E8),
    '2': ('sub', 0x7D0),
    '3': ('add', 0xBB8),
    '4': ('sub', 0xFA0),
    '5': ('add', 0x1388),
    '6': ('sub', 0x1770),
    '7': ('add', 0x1B58),
    '8': ('sub', 0x1F40),
    '9': ('add', 0x2EE0),
    '(': ('add', 1),
    ')': ('xor', None),  # XOR ebx with itself => sets to 0
}


def _apply_op(res, ch):
    """Apply the effect of character ch to res, return new res (32-bit signed)."""
    op_info = CHAR_OPS.get(ch)
    if op_info is None:
        # Unknown character: skip (ASSUMPTION: ignored)
        return res
    op, val = op_info
    if op == 'add':
        res = (res + val) & 0xFFFFFFFF
    elif op == 'sub':
        res = (res - val) & 0xFFFFFFFF
    elif op == 'xor':
        # ')' means res = 0 (XOR EBX with EBX = 0)
        res = 0
    return res


def _is_valid_result(res):
    """
    Mirrors the isExit / final check:
      mov ecx, ebx
      and ecx, 80000001h
      js  bad          ; sign bit set => bad
      jnz bad          ; low bit set => bad
      cmp ebx, 5DC0h
      jl  bad          ; value < 0x5DC0 => bad
    So res must be even, non-negative (bit 31 clear), and >= 0x5DC0.
    """
    masked = res & 0x80000001
    # js: sign bit set
    if masked & 0x80000000:
        return False
    # jnz: bit 0 set (or any bit in mask set)
    if masked != 0:
        return False
    # cmp with 5DC0h
    if res < 0x5DC0:
        return False
    return True


def verify(name, serial):
    """
    Validate a serial string.
    The crackme ignores the name; only the serial matters.
    It iterates over every character of the serial, applies the
    corresponding arithmetic operation to a running value (starting at 0),
    and at the end checks that the value satisfies:
      - bit 31 clear (positive)
      - bit 0 clear (even)
      - value >= 0x5DC0 (24000)
    """
    # ASSUMPTION: name is not used in the validation (serial-only keygenme)
    res = 0
    for ch in serial:
        res = _apply_op(res, ch)
    return _is_valid_result(res)


def keygen(name):
    """
    Generate a valid serial.
    Strategy: randomly pick operations from the allowed characters until
    the running total satisfies the exit condition.
    We reset (via ')') if we overshoot or exceed 255 chars.
    """
    # ASSUMPTION: name is not used
    allowed = list(CHAR_OPS.keys())
    max_attempts = 100000
    for _ in range(max_attempts):
        serial = []
        res = 0
        for _ in range(255):
            ch = random.choice(allowed)
            res = _apply_op(res, ch)
            serial.append(ch)
            if _is_valid_result(res):
                return ''.join(serial)
            # If res went negative (sign bit set) or got too large, reset with ')'
            if res & 0x80000000:
                serial.append(')')
                res = 0
    # Fallback: brute-force a deterministic solution
    # 9 adds 0x2EE0; we need at least ceil(0x5DC0 / 0x2EE0) = 2 nines = 0x5DC0
    # 0x2EE0 * 2 = 0x5DC0 exactly, and 0x5DC0 & 0x80000001 == 0, so it's valid
    return '99'



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
