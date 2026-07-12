# Reverse-engineered keygen for pineware_001_keygenme by ultimate_pinecone
# Based on keygen.asm writeup by qpt
#
# The crackme uses a stack-based virtual machine / interpreter.
# 'dat1' is a 2D table (rows x 20 cols) of opcodes/instructions.
# The VM state consists of:
#   - bl: column index (0..19), bh: row index (0..3)
#   - cx (split: cl = column step, ch = row step)
#   - A value stack (buff1)
#   - aName: the input name string
#   - Serial: output buffer
#
# ASSUMPTION: The exact contents of 'dat1' (the opcode table) are not provided
# in the writeup. The table drives which VM instruction is executed at each step.
# Without dat1, we cannot fully implement the algorithm.
# The opcode meanings are decoded from the assembly:
#
# 0x22 (")  -> toggle bswap mode / halt-like (flip bh<->bl role, xor bl^1)
# 0x30-0x39 -> push (al - 0x30) onto stack  (digit 0-9)
# 0x7e (~)  -> push next byte of name onto stack
# 0x2c (,)  -> output: pop stack top -> write to serial buffer
# 0x3e (>)  -> set cx = 1
# 0x3c (<)  -> set cx = 0xff
# 0x76 (v)  -> set cx = 0x100
# 0x5e (^)  -> set cx = 0xff00
# 0x2b (+)  -> pop a, pop b, push a+b
# 0x2d (-)  -> pop a, pop b, push b-a
# 0x2a (*)  -> pop a, pop b, push a*b
# 0x2f (/)  -> pop a, pop b: push a%b, push a//b (or 0 if div by zero)
# 0x5c (\) -> pop a, pop b, push b, push a  (swap)
# 0x5f (_)  -> pop a: if a==0 set cx to >-mode else <-mode
# 0x23 (#)  -> advance position (call advance_pos)
# 0x3a (:)  -> pop a, push a, push a  (dup)
# 0x21 (!)  -> pop a, push (a==0 ? 1 : 0)  (logical not)
# 0x6c (l)  -> pop a, push rol(a, 1)
# 0x60 (`)  -> pop a, pop b, push (b > a ? 1 : 0)
# 0x24 ($)  -> pop a, discard  (drop)
# 0x40 (@)  -> end / return

# ASSUMPTION: dat1 table content is unknown. We provide a skeleton that
# would work if dat1 were known. The keygen logic depends entirely on dat1.

from typing import Optional

# ASSUMPTION: dat1 is a 4-row x 20-col table of bytes (opcode characters)
# Without the actual binary, we cannot determine dat1.
# The following is a STUB that must be filled with real dat1 bytes.
dat1 = [
    # 20 bytes per row, 4 rows
    # ASSUMPTION: all zeros = unknown
    [0]*20,
    [0]*20,
    [0]*20,
    [0]*20,
]

ROWS = 4
COLS = 20

def run_vm(name: str) -> Optional[str]:
    """
    Stack-based VM interpreter reconstructed from keygen.asm.
    ASSUMPTION: dat1 contents are unknown; this will not produce correct output
    without the real dat1 table from the binary.
    """
    # VM registers
    bl = 0        # column (0..19)
    bh = 0        # row (0..3)
    cl_reg = 1    # column step (low byte of cx)
    ch_reg = 0    # row step (high byte of cx... actually bswap ecx is used)
    # ASSUMPTION: cx high word holds bh/bl after bswap; cl=1 is initial ecx=1
    # After bswap ecx: the low 16 bits of ecx become high 16 bits.
    # We model cx as a 16-bit value split into ch (high) and cl (low).
    cx = 1        # ecx initial value; after bswap the low word becomes the step

    name_ptr = 0  # index into name
    serial = []   # output bytes
    stack = []    # value stack (buff1 modeled as list)

    MAX_STEPS = 100000

    def stack_push(val):
        stack.append(val & 0xFFFFFFFF)

    def stack_pop():
        if stack:
            return stack.pop()
        return 0

    def advance_pos():
        nonlocal bl, bh, cl_reg, ch_reg
        bl = (bl + cl_reg) & 0xFF
        bh = (bh + ch_reg) & 0xFF
        # Wrap-around with specific sentinel values from asm
        if bl == 0xFF:
            bl = 0x13  # 19
        if bh == 0xFF:
            bh = 0x03
        if bl == 0x14:  # 20
            bl = 0
        if bh == 0x04:
            bh = 0

    # Parse cx: after bswap ecx, cx (low 16 bits) represents steps
    # Initial ecx=1 means cl_reg=1, ch_reg=0
    cl_reg = 1
    ch_reg = 0

    name_bytes = [ord(c) for c in name]

    for _ in range(MAX_STEPS):
        # Lookup opcode
        if bh >= ROWS or bl >= COLS:
            break
        al = dat1[bh][bl]

        if al == 0x22:  # '"' -> toggle / halt-branch
            # bswap ebx, xor bl^1, bswap ebx  => flip bl bit0
            bl ^= 1
            advance_pos()
            continue

        # Check if bh != 0 (dl from mov edx,ebx; test dl,dl checks bl)
        # ASSUMPTION: 'test dl,dl' checks the original bl before bswap
        # After bswap ebx: bh and bl swap roles in edx
        # We model: if bl != 0 => call advance and jump
        if bl != 0 and al != 0x22:
            # The asm does bswap ebx, test dl,dl (dl=original bh after bswap)
            # ASSUMPTION: this checks original bh (which becomes bl after bswap)
            # This is complex; we approximate: if original bl != 0 then just advance
            advance_pos()
            continue

        if 0x30 <= al <= 0x39:  # '0'-'9'
            stack_push(al - 0x30)
        elif al == 0x7e:  # '~' -> push name char
            if name_ptr < len(name_bytes):
                stack_push(name_bytes[name_ptr])
                name_ptr += 1
            else:
                stack_push(0)
        elif al == 0x2c:  # ',' -> output to serial
            val = stack_pop()
            serial.append(val & 0xFF)
        elif al == 0x3e:  # '>'
            cl_reg = 1; ch_reg = 0
        elif al == 0x3c:  # '<'
            cl_reg = 0xFF; ch_reg = 0  # ASSUMPTION: 0xFF as signed = -1
        elif al == 0x76:  # 'v'
            cl_reg = 0; ch_reg = 1  # cx=0x100 means ch=1,cl=0
        elif al == 0x5e:  # '^'
            cl_reg = 0; ch_reg = 0xFF  # cx=0xff00 means ch=0xFF,cl=0
        elif al == 0x2b:  # '+'
            a = stack_pop()
            b = stack_pop()
            stack_push(a + b)
        elif al == 0x2d:  # '-'
            a = stack_pop()
            b = stack_pop()
            stack_push(b - a)
        elif al == 0x2a:  # '*'
            a = stack_pop()
            b = stack_pop()
            stack_push(a * b)
        elif al == 0x2f:  # '/'
            a = stack_pop()  # divisor
            b = stack_pop()  # dividend
            if a == 0:
                stack_push(0)
                stack_push(0)
            else:
                import ctypes
                # signed division
                dividend = ctypes.c_int32(b).value
                divisor = ctypes.c_int32(a).value
                quot = int(dividend / divisor)
                rem = dividend - quot * divisor
                stack_push(rem)
                stack_push(quot)
        elif al == 0x5c:  # '\\' -> swap
            a = stack_pop()
            b = stack_pop()
            stack_push(a)
            stack_push(b)
        elif al == 0x5f:  # '_' -> conditional direction
            a = stack_pop()
            if a == 0:
                cl_reg = 1; ch_reg = 0   # '>'
            else:
                cl_reg = 0xFF; ch_reg = 0  # '<'
        elif al == 0x23:  # '#' -> advance (skip)
            advance_pos()
        elif al == 0x3a:  # ':' -> dup
            a = stack_pop()
            stack_push(a)
            stack_push(a)
        elif al == 0x21:  # '!' -> not
            a = stack_pop()
            stack_push(1 if a == 0 else 0)
        elif al == 0x6c:  # 'l' -> rol 1
            a = stack_pop()
            result = ((a << 1) | (a >> 31)) & 0xFFFFFFFF
            stack_push(result)
        elif al == 0x60:  # '`' -> greater-than
            a = stack_pop()
            b = stack_pop()
            stack_push(1 if b > a else 0)
        elif al == 0x24:  # '$' -> drop
            stack_pop()
        elif al == 0x40:  # '@' -> end
            break

        advance_pos()

    return ''.join(chr(b) for b in serial if 32 <= b < 127)


def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The crackme computes a serial from the name using the VM,
    then compares it. We run the VM and compare output.
    Without dat1, this always returns False.
    """
    computed = run_vm(name)
    if computed is None:
        return False
    return computed == serial


def keygen(name: str) -> str:
    """
    Generate serial for given name by running the VM.
    ASSUMPTION: dat1 table is unknown; output will be incorrect without it.
    """
    result = run_vm(name)
    return result if result else ''



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
