import random
import string

# The crackme 'codeshield' by tdcnl
# Algorithm recovered from KeyGen.cpp in solution writeup.
#
# The serial is a 23-byte string where each byte = opcode_byte XOR src[i]
# src[] is a fixed 23-byte array.
# The opcode bytes must form valid x86 instructions (with correct lengths),
# and each resulting character must be printable ASCII (0x20..0x7E).
#
# From solution 2 (deroko): the simplest valid serial is src[i] XOR 0x90 for each i,
# because 0x90 is NOP (1-byte opcode with 0 operand bytes).
# That gives a fixed 23-byte serial independent of name.
#
# The keygen in solution 1 is more complex: it randomly picks valid x86 opcodes,
# XORs them with src[i] to get printable chars.
# The name is NOT used in the algorithm (no name-based check).

SRC = bytes([0xE2, 0xC1, 0xC7, 0x3D, 0x65, 0x7F, 0x2F, 0x35, 0x10,
             0x8A, 0x7E, 0x82, 0xB5, 0x9A, 0xDF, 0xE8, 0x4E, 0x28,
             0x91, 0x31, 0x30, 0x30, 0x30])

SERIAL_LEN = 23

# Opcode table from get_opcode: (opcode_byte, operand_bytes_count)
# Only entries with 0 operand bytes (single-byte instructions) for simplicity
# Plus entries with 1 or 4 operand bytes.
OPCODE_TABLE = [
    # (opcode, operand_len)
    (0x98, 0), (0x99, 0), (0x90, 0),
    (0x04, 1), (0x05, 4),
    (0x24, 1), (0x25, 4),
    (0x14, 1), (0x15, 4),
    (0x3A, 0), (0x37, 0), (0x2F, 0), (0x27, 0),
    (0x40, 0), (0x41, 0), (0x42, 0), (0x43, 0),
    (0x46, 0), (0x47, 0),
    (0xB8, 4), (0xB9, 4), (0xBA, 4), (0xBB, 4),
    (0xBE, 4), (0xBF, 4),
    (0xB0, 1), (0xB1, 1), (0xB2, 1), (0xB3, 1),
    (0xB4, 1), (0xB5, 1), (0xB6, 1), (0xB7, 1),
    (0x0C, 1), (0x0D, 4),
    (0x1C, 1), (0x1D, 4),
    (0xF9, 0),
    (0x34, 1), (0x35, 4),
    (0x48, 0), (0x49, 0), (0x4A, 0), (0x4B, 0),
    (0x4E, 0), (0x4F, 0),
    (0x2C, 1), (0x2D, 4),
    (0xA8, 1), (0xA9, 4),
]

def is_ansi(c):
    """Check if byte value produces printable ASCII (0x20..0x7E)"""
    return 0x20 <= c <= 0x7E

def verify(name, serial):
    """
    Verify a serial for this crackme.
    The name is NOT used in the check (no name-based validation found).
    The serial must be exactly 23 printable ASCII chars.
    Each serial[i] XOR src[i] must form the start of a valid x86 instruction
    from the allowed opcode set, with subsequent bytes also producing printable ASCII.
    The simplest check: serial is 23 printable ASCII bytes where
    serial[i] XOR src[i] byte must be a valid opcode from the table,
    and the structure must be consistent (opcode + correct number of operand bytes).
    """
    if len(serial) != SERIAL_LEN:
        return False
    # Check all chars are printable ASCII
    for c in serial:
        if isinstance(c, int):
            v = c
        else:
            v = ord(c)
        if not is_ansi(v):
            return False
    # Decode the serial as x86 instructions
    serial_bytes = [ord(c) if isinstance(c, str) else c for c in serial]
    valid_opcodes = {op: olen for op, olen in OPCODE_TABLE}
    i = 0
    while i < SERIAL_LEN:
        code = serial_bytes[i] ^ SRC[i]
        if code not in valid_opcodes:
            # Also check for JMP short (0xEB) which is used in the keygen's early-exit path
            if code == 0xEB:
                # jmp short: 2 bytes total
                if i + 1 >= SERIAL_LEN:
                    return False
                # next byte is offset
                i += 2
                continue
            return False
        olen = valid_opcodes[code]
        # Check operand bytes are printable ASCII
        for j in range(1, olen + 1):
            if i + j >= SERIAL_LEN:
                return False
            # operand bytes just need to be printable ASCII (they were randomly chosen)
        i += 1 + olen
    return i == SERIAL_LEN

def keygen(name):
    """
    Generate a valid serial.
    The simplest approach (from deroko's solution): XOR each src byte with 0x90 (NOP).
    0x90 XOR src[i] must be printable ASCII for all i.
    ASSUMPTION: The NOP-based serial is always valid since 0x90 is a single-byte opcode.
    """
    # Simple NOP-based serial
    simple_serial = bytes([s ^ 0x90 for s in SRC])
    # Check if all are printable ASCII
    if all(is_ansi(b) for b in simple_serial):
        return simple_serial.decode('latin-1')
    # Fallback: try random generation
    return keygen_random(name)

def keygen_random(name, max_attempts=100000):
    """
    Randomly generate a valid serial by picking opcodes and random operand bytes.
    ASSUMPTION: name is ignored (no name-based check in the algorithm).
    """
    # Build list of single-byte opcodes for easy selection
    single_opcodes = [(op, olen) for op, olen in OPCODE_TABLE if olen == 0]
    multi_opcodes = [(op, olen) for op, olen in OPCODE_TABLE]

    for _ in range(max_attempts):
        key = []
        i = 0
        ok = True
        while i < SERIAL_LEN:
            remaining = SERIAL_LEN - i
            # Filter opcodes that fit in remaining space
            candidates = [(op, olen) for op, olen in multi_opcodes if 1 + olen <= remaining]
            if not candidates:
                ok = False
                break
            # Try to find a valid opcode
            found = False
            random.shuffle(candidates)
            for op, olen in candidates:
                c = op ^ SRC[i]
                if not is_ansi(c):
                    continue
                # Try to fill operand bytes
                operand_bytes = []
                operand_ok = True
                for j in range(olen):
                    # Try random byte
                    attempts = 0
                    while attempts < 256:
                        rb = random.randint(0, 255)
                        if is_ansi(rb ^ SRC[i + 1 + j]):
                            operand_bytes.append(rb ^ SRC[i + 1 + j])
                            break
                        attempts += 1
                    else:
                        operand_ok = False
                        break
                if operand_ok:
                    key.append(c)
                    key.extend(operand_bytes)
                    i += 1 + olen
                    found = True
                    break
            if not found:
                ok = False
                break
        if ok and len(key) == SERIAL_LEN:
            return ''.join(chr(b) for b in key)
    return None


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
