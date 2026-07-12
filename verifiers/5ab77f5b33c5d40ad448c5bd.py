# Reverse-engineered keygen for keygenme_2_ver.2.00 by t.0.r.n.a.d.0
# Based on the partial writeup by 'Obnoxious' from crackmes.de
#
# What is known from the writeup:
# - The serial/key is processed character by character
# - Each character is compared against specific ASCII values:
#   'D' (0x44), 'B' (0x42), and something > 'D' (likely 'F' = 0x46)
# - These appear to be Brainfuck-like or tape-machine instructions:
#     'D' (0x44) -> DEC the byte at the current tape pointer
#     'B' (0x42) -> DEC the tape pointer itself (move left), but only if > base address
#     'F' (0x46, > 0x44) -> likely INC the tape pointer (move right)
# - The tape starts at address 0x405160 (in the real crackme)
# - There is also a check for 0x21 ('!') which may terminate or signal success
# - The name field likely initialises the tape or a target value
# - The validation checks that after executing all 'instructions' in the serial,
#   the tape produces values that match something derived from the name
#
# ASSUMPTION: The crackme uses a simple virtual machine where:
#   'I' or 'F' (0x46) = increment tape pointer
#   'B' (0x42) = decrement tape pointer
#   'D' (0x44) = decrement byte at current tape position
#   'U' or some char = increment byte at current tape position
#   The name sets target values on the tape and the serial must reduce them all to 0
#
# ASSUMPTION: Without the full disassembly we cannot fully reconstruct the algorithm.
# The implementation below is a best-guess skeleton.

TAPE_SIZE = 256

def _run_serial(serial, tape):
    """
    ASSUMPTION: Simulates the crackme's serial processing VM.
    Characters in serial are interpreted as tape machine instructions.
    Returns the tape state after processing.
    """
    ptr = 0  # tape pointer, relative index
    tape = list(tape)  # mutable copy
    i = 0
    while i < len(serial):
        c = serial[i]
        if c == 'D':  # 0x44: DEC byte at current position (if not 0)
            if tape[ptr] != 0:
                tape[ptr] = (tape[ptr] - 1) & 0xFF
        elif c == 'B':  # 0x42: DEC pointer (move left), if ptr > 0
            if ptr > 0:
                ptr -= 1
        elif c == 'F':  # 0x46: INC pointer (move right) - ASSUMPTION
            if ptr < TAPE_SIZE - 1:
                ptr += 1
        elif c == 'U':  # ASSUMPTION: INC byte at current position
            tape[ptr] = (tape[ptr] + 1) & 0xFF
        elif c == '!':  # 0x21: possible terminator / success signal
            break
        # ASSUMPTION: other characters may be NOPs or serve other purposes
        i += 1
    return tape


def _name_to_tape(name):
    """
    ASSUMPTION: The name is used to initialise target tape values.
    Most likely each character of the name sets a byte on the tape.
    """
    tape = [0] * TAPE_SIZE
    for idx, ch in enumerate(name[:TAPE_SIZE]):
        tape[idx] = ord(ch) & 0xFF
    return tape


def verify(name, serial):
    """
    ASSUMPTION: The serial is valid if after running the VM the tape is all zeros
    (or matches some derived target). This is a plausible but unconfirmed reconstruction.
    """
    if not name or not serial:
        return False
    tape = _name_to_tape(name)
    result = _run_serial(serial, tape)
    # ASSUMPTION: success when all used tape cells are zeroed
    return all(b == 0 for b in result[:len(name)])


def keygen(name):
    """
    ASSUMPTION: Generate a serial that decrements each name byte to 0.
    For each character in name, emit that many 'D' instructions,
    then move to next cell with 'F'.
    """
    if not name:
        return ''
    serial_parts = []
    for ch in name:
        val = ord(ch) & 0xFF
        # Decrement the cell val times
        serial_parts.append('D' * val)
        # Move tape pointer right to next cell
        serial_parts.append('F')
    return ''.join(serial_parts)



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
