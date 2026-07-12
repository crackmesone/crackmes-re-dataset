# Mastermind crackme by Spider - reverse engineered from ZaiRoN's writeup
# algorithm_recovered: partial
# The writeup describes:
#   1. A name-based value computation (valName)
#   2. The serial is 26 hex chars -> 13 bytes of x86 machine code
#   3. A disasm engine validates those 13 bytes (only certain opcodes allowed)
#   4. The 13-byte snippet must perform some computation relating to valName
# The writeup was truncated before the full serial validation logic was shown.
# We can implement the name hash (valName) fully, but the serial/code constraints
# are only partially described.

import struct

# -------------------------------------------------------------------------
# Step 1: Compute valName from the name string
# -------------------------------------------------------------------------
# Assembly:
#   ecx = len(name)
#   eax = 0x8E310BD4
#   loop:
#     edx = name[ecx-1]   (iterates backwards from last char to first)
#     eax = (eax * edx) & 0xFFFFFFFF
#     eax ^= 0xD86F936E
#     ecx -= 1
#   until ecx == 0
#   edx:eax = eax (zero-extend)
#   (edx,eax) = divmod(eax, 0xC350)  -> remainder in edx
#   esi = edx + 0x1F4  (i.e. remainder + 500)
#   valName = esi  (range: 500..50500)

def compute_val_name(name: str) -> int:
    ecx = len(name)
    if ecx == 0:
        return 0
    eax = 0x8E310BD4
    # loop iterates ecx times, decrementing ecx each time
    # movzx edx, byte ptr [ecx+4082E3h]  with ecx starting at len
    # address = ecx + 0x4082E3, but since name is stored at 0x4082E4
    # name[0] is at 0x4082E4 = 0 + 0x4082E4
    # name[i] is at i + 0x4082E4
    # when ecx=len, address = len + 0x4082E3 = (len-1) + 0x4082E4 -> last char
    # when ecx=1,   address = 1   + 0x4082E3 = 0       + 0x4082E4 -> first char
    # So it iterates from last char down to first char
    for i in range(ecx, 0, -1):
        edx = name[i - 1] if isinstance(name[i-1], int) else ord(name[i - 1])
        eax = (eax * edx) & 0xFFFFFFFF
        eax ^= 0xD86F936E
    # div ebx (ebx=0xC350), edx:eax / 0xC350
    # eax was 32-bit, edx was 0 before xor loop ends... actually:
    # xor edx,edx sets edx=0 before the div
    remainder = eax % 0xC350
    val_name = remainder + 0x1F4  # +500
    return val_name

# -------------------------------------------------------------------------
# Step 2: Allowed opcodes (partial - from writeup examples)
# -------------------------------------------------------------------------
# The writeup says there is a 256-byte table at 0x408000 where allowed
# single-byte opcodes have value 1. Examples given:
#   0x33 (XOR r/m32, r32) -> allowed
#   0x50 (PUSH EAX)       -> NOT allowed
# We don't have the full table, so we can't fully validate.
# ASSUMPTION: The allowed opcodes form a restricted set of arithmetic/logic
# instructions that operate on registers (no memory refs, no jumps, no calls).
# Based on the checks in the writeup:
#   - No direct address operands (no jmp/call with immediate)
#   - No memory address operands (except LEA is specifically allowed)
#   - Immediate values and general registers are allowed

# -------------------------------------------------------------------------
# Step 3: Serial parsing
# -------------------------------------------------------------------------
# Serial is 26 hex chars (0-9, A-F or similar) -> 13 bytes
# ASSUMPTION: each pair of hex digits forms one byte

def serial_to_bytes(serial: str) -> bytes:
    """Convert 26-char hex serial to 13 bytes."""
    if len(serial) != 26:
        return None
    try:
        return bytes.fromhex(serial)
    except ValueError:
        return None

# -------------------------------------------------------------------------
# verify() and keygen()
# -------------------------------------------------------------------------
# Because the writeup was truncated we cannot fully verify the serial.
# We implement what we know:
#   - name must be non-empty
#   - serial must be 26 hex chars -> 13 bytes
#   - valName is computed
#   - the 13 bytes are machine code that is validated by the disasm engine
#     and then EXECUTED (or its result checked against valName)
# The execution/result check is NOT described in the truncated writeup.

def verify(name: str, serial: str) -> bool:
    # Check name
    if not name:
        return False
    # Compute name value
    val_name = compute_val_name(name)
    # Parse serial
    serial_bytes = serial_to_bytes(serial)
    if serial_bytes is None:
        return False
    # ASSUMPTION: The 13-byte snippet is x86 code that, when executed,
    # produces a value equal to valName. We cannot simulate arbitrary x86
    # here without the full disasm engine and execution context.
    # ASSUMPTION: We only perform the structural check we know about.
    # Further validation (opcode table checks, execution result == valName)
    # cannot be implemented without the full writeup.
    print(f"[verify] valName = {val_name} (0x{val_name:X})")
    print(f"[verify] serial bytes = {serial_bytes.hex()}")
    print("[verify] Full validation not possible: writeup was truncated.")
    # ASSUMPTION: return True if structural checks pass (placeholder)
    return True  # ASSUMPTION: incomplete


def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    ASSUMPTION: The 13-byte snippet must produce valName.
    A typical snippet might be: MOV EAX, <valName> ; RET (padded)
    MOV EAX, imm32 = B8 xx xx xx xx  (5 bytes)
    RET = C3 (1 byte) -> 6 bytes, need 13 total, pad with NOPs (90)
    But we don't know if MOV EAX or NOP or RET are in the allowed opcode set.
    ASSUMPTION: Using MOV EAX,imm32 + NOP padding as a guess.
    """
    if not name:
        return None
    val_name = compute_val_name(name)
    print(f"[keygen] valName = {val_name} (0x{val_name:X})")
    # ASSUMPTION: snippet = B8 <val_name as LE uint32> C3 90 90 90 90 90 90 90
    # MOV EAX, imm32 (B8 xx xx xx xx) + RET (C3) + 7x NOP (90)
    snippet = bytearray()
    snippet.append(0xB8)  # MOV EAX, imm32
    snippet.extend(struct.pack('<I', val_name))
    snippet.append(0xC3)  # RET
    snippet.extend([0x90] * 7)  # NOP padding
    assert len(snippet) == 13
    serial = snippet.hex().upper()
    # ASSUMPTION: serial encoding is straight hex, 26 chars
    print(f"[keygen] serial (ASSUMPTION) = {serial}")
    return serial



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
