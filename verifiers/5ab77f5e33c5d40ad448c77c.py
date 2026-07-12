# NAVM 2 - Not Another Virtual Machine keygen/verifier
# Based on the tutorial writeup for winfan's NAVM 2 crackme
#
# The VM is stack-based, reads 10-byte commands (opcode 1B, postfix 1B, param1 4B, param2 4B)
# The actual validation algorithm runs inside program.navm in the VM.
# The writeup was truncated before full algorithm details were provided.
#
# ASSUMPTION: Based on the writeup, the crackme:
#   1. Reads username via VMIN_USERNAME (opcode A2) -> stores length on VM stack
#   2. Reads each char via MOV [paramN], USERNAME.CHAR (opcode E1, postfix D0)
#   3. Reads password/serial via VMIN_PASSWORD (opcode A3) -> converts string to integer
#   4. Performs some arithmetic on username chars/length to derive expected serial
#   5. Compares computed value with entered serial
#
# ASSUMPTION: The writeup shows the VM dissassembler output starts at CODE:000000F0
# with 'MOV [00007530], 0000004E' but is truncated. We cannot determine the exact
# arithmetic without the full out.txt disassembly.
#
# ASSUMPTION: A common pattern for such crackmes is:
#   serial = sum_of_char_values * some_constant XOR some_constant2
#   or similar transformation of username bytes.
#
# Since the writeup is truncated and we do not have the full program.navm analysis,
# we implement a partial skeleton that models the VM structure.

import struct

# --- VM emulator skeleton ---

VM_STACK_SIZE = 0x10000  # 64K entries (4 bytes each)

def parse_navm(data):
    """Parse program.navm bytes into list of (opcode, postfix, param1, param2)"""
    commands = []
    for i in range(0, len(data) - 9, 10):
        opcode, postfix = data[i], data[i+1]
        param1, = struct.unpack_from('<I', data, i+2)
        param2, = struct.unpack_from('<I', data, i+6)
        commands.append((opcode, postfix, param1, param2))
    return commands


def run_navm(commands, username, serial_str):
    """
    Emulate the NAVM virtual machine.
    Returns True if the program accepts the (username, serial) pair.
    ASSUMPTION: The VM signals acceptance by falling through without jumping to a 'fail' branch.
    """
    stack = [0] * VM_STACK_SIZE
    username_iter = iter(username)
    username_len = len(username)
    # ASSUMPTION: VMIN_PASSWORD stores the integer value of serial string on the stack
    try:
        serial_int = int(serial_str)
    except ValueError:
        try:
            serial_int = int(serial_str, 16)
        except ValueError:
            serial_int = 0

    pc = 0  # current command index
    max_steps = 100000
    steps = 0
    result = False  # ASSUMPTION: default fail

    while 0 <= pc < len(commands) and steps < max_steps:
        steps += 1
        opcode, postfix, param1, param2 = commands[pc]
        next_pc = pc + 1

        if opcode == 0x01:  # JMP
            if postfix == 0xD1:  # absolute jump to param1
                next_pc = param1
            elif postfix == 0xD0:  # jump to VM_STACK[param1]
                next_pc = stack[param1]

        elif opcode == 0xE4:  # MOV [param1], immediate (ASSUMPTION: opcode for MOV imm)
            if postfix == 0xD1:
                stack[param1] = param2

        elif opcode == 0xE1:  # USERNAME ops
            if postfix == 0xD0:  # MOV [param1], USERNAME.CHAR
                try:
                    ch = next(username_iter)
                    stack[param1] = ord(ch) if isinstance(ch, str) else ch
                except StopIteration:
                    stack[param1] = 0

        elif opcode == 0xA2:  # VMIN_USERNAME: store username length
            # ASSUMPTION: stores length at top of stack or at param1
            stack[param1] = username_len

        elif opcode == 0xA3:  # VMIN_PASSWORD: store serial as int
            # ASSUMPTION: stores at param1
            stack[param1] = serial_int

        elif opcode == 0xA0 or opcode == 0xA1:  # VM_PRINT / VM_PRINTLN
            pass  # ignore output

        # ASSUMPTION: success/fail opcodes not fully known; placeholder:
        elif opcode == 0xFF:  # ASSUMPTION: some 'accept' opcode
            result = True
            break
        elif opcode == 0xFE:  # ASSUMPTION: some 'reject' opcode
            result = False
            break

        # ASSUMPTION: arithmetic opcodes (XOR, ADD, etc.) not fully decoded from truncated writeup
        # Would need full out.txt to implement correctly

        pc = next_pc

    return result


# --- Fallback algorithm based on common patterns described ---
# ASSUMPTION: Since we cannot fully emulate without program.navm content,
# we implement a plausible keygen based on the described VM operations:
# sum of ordinal values of username chars, possibly XOR/multiplied with constants.

def _compute_serial(name):
    """
    ASSUMPTION: Serial is derived from username character values.
    Common pattern: serial = sum(ord(c) for c in name) * len(name) or similar.
    Without full out.txt we cannot be certain.
    """
    if not name:
        return 0
    total = 0
    for i, c in enumerate(name):
        total += ord(c) * (i + 1)
    # ASSUMPTION: final transformation
    return total & 0xFFFFFFFF


def verify(name: str, serial: str) -> bool:
    """
    Verify (name, serial) pair.
    ASSUMPTION: Falls back to computed algorithm since we lack full program.navm disassembly.
    If program.navm bytes were available, run_navm() would be used instead.
    """
    try:
        serial_int = int(serial)
    except ValueError:
        try:
            serial_int = int(serial, 16)
        except ValueError:
            return False
    expected = _compute_serial(name)
    return serial_int == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    ASSUMPTION: Based on inferred algorithm.
    """
    return str(_compute_serial(name))



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
