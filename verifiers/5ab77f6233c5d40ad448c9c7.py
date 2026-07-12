import ctypes
import struct

# RandomNum uses LastNameChar (seeded by last char of name) as state
# Formula:
#   state = state (initialized to ord(last_char_of_name))
#   q, r = divmod(state, 0x1F31D)
#   result = (0x41A7 * r) - (0x0B14 * q)
#   new_state = result
#   return result

def make_random_num_gen(last_char_val):
    state = [last_char_val & 0xFFFFFFFF]
    def random_num():
        val = state[0]
        q = val // 0x1F31D
        r = val % 0x1F31D
        result = (0x41A7 * r) - (0x0B14 * q)
        result = result & 0xFFFFFFFF
        state[0] = result
        return result
    return random_num

# ASSUMPTION: The generated code operates on 32-bit unsigned arithmetic
# The 'FillRegisters' loop runs 7 times, filling registers EDI,ESI,EBP,ESP,EBX,EDX,ECX
# with random values (in that order, as B8+reg for reg=7,6,5,4,3,2,1)
# Then 'Codegen_Core' runs 0x30 (48) iterations, each picking a random op and operands

# Register encoding: B8=EAX(0), B9=ECX(1), BA=EDX(2), BB=EBX(3),
#                    BC=ESP(4), BD=EBP(5), BE=ESI(6), BF=EDI(7)
# EAX is register 0 (set to serial_as_hex at start)

NUM_REGS = 8

def simulate_generated_code(serial_val, last_char_val):
    """Simulate the generated code and return final EAX value."""
    rng = make_random_num_gen(last_char_val)
    
    # Registers: index 0=EAX, 1=ECX, 2=EDX, 3=EBX, 4=ESP, 5=EBP, 6=ESI, 7=EDI
    regs = [0] * NUM_REGS
    regs[0] = serial_val & 0xFFFFFFFF  # EAX = serial
    
    # FillRegisters: 7 calls, filling regs based on (loop_counter & 7)
    # ecx counts down from 7 to 1, so (ecx & 7) gives 7,6,5,4,3,2,1
    # => fills EDI(7), ESI(6), EBP(5), ESP(4), EBX(3), EDX(2), ECX(1)
    for i in range(7, 0, -1):
        reg_idx = i & 7
        val = rng()
        regs[reg_idx] = val & 0xFFFFFFFF
    
    # Codegen_Core: 0x30 = 48 iterations
    # Each iteration:
    #   call RandomNum -> store in ecx (operand register selector / value)
    #   call RandomNum -> used for div by 8 to pick jump table entry
    #   the second random number mod 8 selects the operation
    # ASSUMPTION: ecx from first RandomNum is used as register/value operand
    #             ebx (destination register) comes from the second RandomNum used in jmpsub1
    # Looking at jmptbl1-3: stosb the opcode, then call jmpsub1 which presumably
    # provides another random for register selection, and ecx & 0x3F for modrm
    # ASSUMPTION: In reg-reg ops, destination = (ecx>>3)&7, source = ecx&7
    # For reg-val ops: destination = cl & 7, value = next random
    # For rot ops: destination = cl & 7, amount = (next random % 5) + 1
    
    # Re-reading: in Codegen_Core:
    #   first RandomNum -> ecx (this is the 'register' random)
    #   second RandomNum -> eax, then div by 8 -> edx = op selector
    # For reg-reg ops (jmptbl1,2,3): modrm = (ecx & 0x3F) | 0xC0, so dst=(ecx>>3)&7, src=ecx&7
    # For reg-val ops (jmptbl4,5,6): dst = ecx & 7, val = new RandomNum call
    # For rot ops (jmptbl7,8): dst = ecx & 7, amount = (new RandomNum % 5) + 1
    
    for _ in range(0x30):
        ecx = rng()  # first random -> ecx
        eax2 = rng()  # second random -> divide by 8
        op_sel = eax2 % 8  # edx = eax2 mod 8
        
        if op_sel == 0:  # jmptbl1: XOR reg, reg
            modrm = (ecx & 0x3F) | 0xC0
            dst = (modrm >> 3) & 7
            src = modrm & 7
            regs[dst] = (regs[dst] ^ regs[src]) & 0xFFFFFFFF
        elif op_sel == 1:  # jmptbl2: ADD reg, reg
            modrm = (ecx & 0x3F) | 0xC0
            dst = (modrm >> 3) & 7
            src = modrm & 7
            regs[dst] = (regs[dst] + regs[src]) & 0xFFFFFFFF
        elif op_sel == 2:  # jmptbl3: SUB reg, reg
            modrm = (ecx & 0x3F) | 0xC0
            dst = (modrm >> 3) & 7
            src = modrm & 7
            regs[dst] = (regs[dst] - regs[src]) & 0xFFFFFFFF
        elif op_sel == 3:  # jmptbl4: XOR reg, val
            dst = ecx & 7
            val = rng()
            regs[dst] = (regs[dst] ^ val) & 0xFFFFFFFF
        elif op_sel == 4:  # jmptbl5: SUB reg, val
            dst = ecx & 7
            val = rng()
            regs[dst] = (regs[dst] - val) & 0xFFFFFFFF
        elif op_sel == 5:  # jmptbl6: ADD reg, val
            dst = ecx & 7
            val = rng()
            regs[dst] = (regs[dst] + val) & 0xFFFFFFFF
        elif op_sel == 6:  # jmptbl7: ROL reg, val
            dst = ecx & 7
            amt_rand = rng()
            amt = (amt_rand % 5) + 1
            v = regs[dst]
            regs[dst] = ((v << amt) | (v >> (32 - amt))) & 0xFFFFFFFF
        elif op_sel == 7:  # jmptbl8: ROR reg, val
            dst = ecx & 7
            amt_rand = rng()
            amt = (amt_rand % 5) + 1
            v = regs[dst]
            regs[dst] = ((v >> amt) | (v << (32 - amt))) & 0xFFFFFFFF
    
    return regs[0]  # EAX


def serial_to_hex(serial_str):
    """Convert serial string (decimal digits) to integer.
    ASSUMPTION: SerialToHex converts the decimal string to integer."""
    try:
        return int(serial_str) & 0xFFFFFFFF
    except ValueError:
        return 0


def verify(name, serial):
    """Verify name/serial pair. Returns True if valid."""
    if len(name) < 4:
        return False
    
    # Get last character of name
    last_char_val = ord(name[-1]) & 0xFFFFFFFF
    
    # Convert serial to hex value
    serial_val = serial_to_hex(serial)
    
    # Simulate the generated code; must return 0 for valid serial
    result = simulate_generated_code(serial_val, last_char_val)
    return result == 0


def keygen(name):
    """Generate a valid serial for the given name by brute-force search.
    ASSUMPTION: The serial space is searched; a smarter approach would
    reverse the generated code (as described in the writeup) but the
    exact reverse procedure is not fully specified in the text."""
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")
    
    last_char_val = ord(name[-1]) & 0xFFFFFFFF
    
    # ASSUMPTION: Serial is a decimal number entered by user
    # The writeup mentions reversing the code but doesn't give full details.
    # We try a limited brute-force range.
    for candidate in range(0, 1000000):
        serial_val = candidate & 0xFFFFFFFF
        result = simulate_generated_code(serial_val, last_char_val)
        if result == 0:
            return str(candidate)
    
    # ASSUMPTION: Try larger values if small ones fail
    import random
    for _ in range(100000):
        candidate = random.randint(0, 0xFFFFFFFF)
        result = simulate_generated_code(candidate, last_char_val)
        if result == 0:
            return str(candidate)
    
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
