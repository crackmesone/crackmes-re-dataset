# Reverse-engineered from: UFO-Pu55y's CrackMe/KeygenMe - Naked naughty .net doggy
# Solution by: indomit
#
# The crackme uses a serial in the format: XXXXXXXX-XXXXXXXX-<suffix>
# where:
#   - Part 1 (chars 0-7) encodes 4 MSIL opcodes via differences/sums of char pairs
#   - Part 2 (chars 9-16) encodes 4 MSIL opcodes via differences/sums of char pairs
#   - Part 3 (chars 18+) is checked by an embedded DLL decrypted with a key derived
#     from executing the two dynamic methods on 0x6F6A57B0
#
# The opcode encoding rules for each function:
#   opcode1 = text[0] - text[1]   (must map to Ldarg_0 = 0x02)
#   opcode2 = text[2] - text[3]   (must map to Ldc_I4_3 = 0x19 for shot, Ldarg_0=0x02 for shot2)
#   opcode3 = text[4] + text[5]   (must map to Shr=0x63 for shot, Mul=0x5a for shot2)
#   opcode4 = text[6] - text[7]   (must map to Ret = 0x2a)
#
# The GetOpcode mapping is partially reconstructed from the writeup:
#   0x02 -> Ldarg_0
#   0x00 -> Nop
#   0x2a -> Ret
#   0x19 -> Ldc_I4_3
#   0x63 -> Shr
#   0x5a -> Mul
#
# The two functions must compute:
#   shot(x)  = x >> 3
#   shot2(x) = x * x  (truncated to 32 bits)
# Such that shot2(shot(0x6F6A57B0)) == 0xDD6F2464
#
# The third part of the serial is checked by check.dll (native DLL).
# From the Olly dump in the writeup the DLL appears to return 1 unconditionally
# for any input (MOV EAX,1 / LEAVE), but the writeup is truncated so we cannot
# be 100% sure.
# ASSUMPTION: check.dll accepts any non-empty string as the third part of the serial.

import ctypes

# Known S2I("WTF:?") value from writeup
S2I_VALUE = 0x6F6A57B0

# Target key value that correctly decrypts check.dll
TARGET_KEY = 0xDD6F2464


def shot(x: int) -> int:
    """First dynamic method: Ldarg_0, Ldc_I4_3, Shr, Ret => x >> 3"""
    # Treat x as signed 32-bit integer for C# arithmetic behaviour
    x = ctypes.c_int32(x).value
    result = x >> 3
    return ctypes.c_int32(result).value


def shot2(x: int) -> int:
    """Second dynamic method: Ldarg_0, Ldarg_0, Mul, Ret => x * x (32-bit truncated)"""
    x = ctypes.c_int32(x).value
    result = x * x
    # .NET truncates to 32 bits on overflow
    return ctypes.c_int32(result).value


def compute_key() -> int:
    """Compute the decryption key as the crackme does."""
    return shot2(shot(S2I_VALUE))


# Opcode values from writeup
OPCODE_LDARG_0  = 0x02
OPCODE_NOP      = 0x00
OPCODE_RET      = 0x2a
OPCODE_LDC_I4_3 = 0x19
OPCODE_SHR      = 0x63
OPCODE_MUL      = 0x5a
OPCODE_LDARG_0b = 0x02  # same value, used for shot2 opcode2


def find_char_pair_diff(target_opcode: int, base_char: int = ord('A')) -> tuple:
    """
    Find two printable ASCII characters (c1, c2) such that c1 - c2 == target_opcode
    """
    for c1 in range(32, 127):
        c2 = c1 - target_opcode
        if 32 <= c2 < 127:
            return chr(c1), chr(c2)
    raise ValueError(f"Cannot find char pair for diff opcode 0x{target_opcode:02x}")


def find_char_pair_sum(target_opcode: int) -> tuple:
    """
    Find two printable ASCII characters (c1, c2) such that c1 + c2 == target_opcode
    """
    for c1 in range(32, 127):
        c2 = target_opcode - c1
        if 32 <= c2 < 127:
            return chr(c1), chr(c2)
    raise ValueError(f"Cannot find char pair for sum opcode 0x{target_opcode:02x}")


def build_part(op1, op2, op3, op4) -> str:
    """
    Build an 8-char serial part from 4 opcodes:
      chars[0]-chars[1] = op1  (difference)
      chars[2]-chars[3] = op2  (difference)
      chars[4]+chars[5] = op3  (sum)
      chars[6]-chars[7] = op4  (difference)
    """
    c0, c1 = find_char_pair_diff(op1)
    c2, c3 = find_char_pair_diff(op2)
    c4, c5 = find_char_pair_sum(op3)
    c6, c7 = find_char_pair_diff(op4)
    return c0 + c1 + c2 + c3 + c4 + c5 + c6 + c7


def keygen(name: str) -> str:
    """
    Generate a valid serial.
    Part1 encodes: Ldarg_0(0x02), Ldc_I4_3(0x19), Shr(0x63), Ret(0x2a)
    Part2 encodes: Ldarg_0(0x02), Ldarg_0(0x02), Mul(0x5a), Ret(0x2a)
    Part3: ASSUMPTION: any non-empty string works (check.dll returns 1 unconditionally)
    """
    part1 = build_part(OPCODE_LDARG_0, OPCODE_LDC_I4_3, OPCODE_SHR, OPCODE_RET)
    part2 = build_part(OPCODE_LDARG_0b, OPCODE_LDARG_0b, OPCODE_MUL, OPCODE_RET)
    # ASSUMPTION: third part can be any non-empty string
    part3 = "keygen"
    return f"{part1}-{part2}-{part3}"


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial:
    1. Length >= 19, serial[8] == '-', serial[17] == '-'
    2. Opcodes encoded in parts 1 and 2 must form valid dynamic methods
       that compute shot2(shot(0x6F6A57B0)) == 0xDD6F2464
    3. ASSUMPTION: third part is passed to check.dll which always returns True
       (based on truncated Olly dump showing MOV EAX,1)
    """
    text = serial

    # Format check
    if len(text) < 0x13:  # 19 chars minimum
        return False
    if text[8] != '-' or text[0x11] != '-':
        return False

    try:
        # Decode opcodes from serial characters
        # Part 1 (shot function):
        op1_1 = ord(text[0]) - ord(text[1])   # should be Ldarg_0 = 0x02
        op1_2 = ord(text[2]) - ord(text[3])   # should be Ldc_I4_3 = 0x19
        op1_3 = ord(text[4]) + ord(text[5])   # should be Shr = 0x63
        op1_4 = ord(text[6]) - ord(text[7])   # should be Ret = 0x2a

        # Part 2 (shot2 function):
        op2_1 = ord(text[9])  - ord(text[10]) # should be Ldarg_0 = 0x02
        op2_2 = ord(text[11]) - ord(text[12]) # should be Ldarg_0 = 0x02
        op2_3 = ord(text[13]) + ord(text[14]) # should be Mul = 0x5a
        op2_4 = ord(text[15]) - ord(text[0x10]) # should be Ret = 0x2a
    except (IndexError, TypeError):
        return False

    # We simulate what the dynamic methods do based on their opcodes.
    # We only handle the specific opcode sequences that produce the correct result.
    # ASSUMPTION: only the proven-correct opcode sequence is checked here.
    # A full verifier would need to emulate arbitrary MSIL opcode sequences.

    # Check that part1 encodes shot(x) = x >> 3
    part1_correct = (
        op1_1 == OPCODE_LDARG_0 and
        op1_2 == OPCODE_LDC_I4_3 and
        op1_3 == OPCODE_SHR and
        op1_4 == OPCODE_RET
    )

    # Check that part2 encodes shot2(x) = x * x
    part2_correct = (
        op2_1 == OPCODE_LDARG_0 and
        op2_2 == OPCODE_LDARG_0b and
        op2_3 == OPCODE_MUL and
        op2_4 == OPCODE_RET
    )

    if not (part1_correct and part2_correct):
        # Could also try other valid opcode combos that produce the same result
        # ASSUMPTION: only the documented solution is validated here
        return False

    # Verify the key computation
    key = compute_key()
    if key != TARGET_KEY:
        return False  # Sanity check on our implementation

    # Part 3: ASSUMPTION: any non-empty string is accepted by check.dll
    part3 = text[0x12:]
    if len(part3) == 0:
        return False

    return True



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
