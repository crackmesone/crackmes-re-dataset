import struct
import ctypes

# VB6 Random Number Generator (LCG-based)
# VB6 uses a specific LCG for Rnd()
# The internal state after VB app load (before any Randomize) always produces 0.7055475115776062464 on first Rnd() call
# VB6 RNG state: seed is a 24-bit value, initial seed = 0x50000 (approx)
# The VB6 Rnd() formula: new_seed = (seed * 0x43FD43FD + 0xC39EC3) & 0xFFFFFF
# result = new_seed / 0x1000000

# ASSUMPTION: VB6 RNG implementation details - using known constants
VB6_MULTIPLIER = 0x43FD43FD
VB6_INCREMENT  = 0xC39EC3
VB6_MODULUS    = 0x1000000

# Known initial seed that produces 0.7055475... on first call
# 0.7055475115776062464 * 0x1000000 = 11831609 approximately
VB6_INITIAL_SEED = 0x50000  # ASSUMPTION: actual initial seed

def vb6_rnd_from_seed(seed):
    """Single VB6 Rnd() step, returns (float_result, new_seed)"""
    new_seed = (seed * VB6_MULTIPLIER + VB6_INCREMENT) & 0xFFFFFF
    result = new_seed / VB6_MODULUS
    return result, new_seed

def vb6_rnd_negative(neg_val):
    """
    Rnd(negative_number) in VB6 seeds the RNG with the negative value
    and returns a deterministic number.
    ASSUMPTION: VB6 uses abs(neg_val) as seed bits for Rnd(negative)
    The seed is derived from the single-precision float bits of the negative number.
    """
    # Convert negative float to single precision and use as seed
    packed = struct.pack('<f', float(neg_val))
    bits = struct.unpack('<I', packed)[0]
    seed = bits & 0xFFFFFF
    result, _ = vb6_rnd_from_seed(seed)
    return result, seed

def compute_id(name):
    """
    Step 1: Get first Rnd() value (VB6 default first call = 0.7055475...)
    The crackme does: rnd_val * 10000, convert to string like '7055,475' or '7055.475'
    
    ASSUMPTION: We use the known constant 0.7055475115776062464
    """
    rnd_val = 0.7055475115776062464
    mul_result = rnd_val * 10000.0  # ~ 7055.475
    
    # Convert to string - VB6 uses locale (comma vs dot)
    # ASSUMPTION: using dot as decimal separator
    rnd_str = '{:.3f}'.format(mul_result)  # '7055.475'
    # In VB6 it might be '7055,475' with comma - ASSUMPTION: use dot form
    
    return rnd_str

def akdd_function(input_str):
    """
    The akdd() function processes the string (from step 1) and generates the ID.
    
    Algorithm (from writeup):
    - Mul and Temp2 initialized to 1.0
    - For i = 1 to Len(input_str):
        - char = Mid(input_str, i, 1)
        - asc_val = Asc(char)  # ASCII value
        - Temp1 = Temp2 * i
        - Temp1 = Temp1 * asc_val  (from FMUL)
        - Temp2 = Temp1 (update for next iteration) -- ASSUMPTION
        - Call Rnd(-1) which seeds RNG with some value
        - Call Randomize(Temp2) to load RNG with Temp2
        - Generate several pseudo-random numbers
        - Multiply each by the 'Number' parsed to akdd()
        - Convert result to Hex and concatenate
    
    ASSUMPTION: Many details of this function are not fully described.
    We implement what we can derive.
    """
    # ASSUMPTION: 'Number' parsed to akdd is the float mul_result (7055.475)
    # ASSUMPTION: Temp2 starts at 1.0, Mul starts at 1.0
    Temp2 = 1.0
    Mul = 1.0
    
    id_parts = []
    
    for i in range(1, len(input_str) + 1):
        char = input_str[i-1]
        asc_val = ord(char)
        
        # Temp1 = Temp2 * i
        Temp1 = Temp2 * i
        # Temp1 = Temp1 * asc_val
        Temp1 = Temp1 * asc_val
        
        # ASSUMPTION: Temp2 is updated to Temp1
        Temp2 = Temp1
        
        # Rnd(-1) call - seeds with negative value, returns deterministic result
        # ASSUMPTION: the negative value used is -Temp2 or -1
        rnd_neg_result, neg_seed = vb6_rnd_negative(-1)
        
        # Randomize(Temp2) - loads RNG with Temp2
        # ASSUMPTION: seed is derived from Temp2's float bits
        packed = struct.pack('<f', float(Temp2) if abs(Temp2) < 3.4e38 else 1.0)
        bits = struct.unpack('<I', packed)[0]
        current_seed = bits & 0xFFFFFF
        
        # Generate pseudo-random number and multiply
        rnd_val, current_seed = vb6_rnd_from_seed(current_seed)
        
        # ASSUMPTION: multiply rnd_val by the input number (7055.475)
        # and convert to hex
        # The writeup says result is converted to Hex and concatenated
        product = rnd_val * 7055.475
        hex_part = '{:X}'.format(int(product) & 0xFFFF)
        id_parts.append(hex_part)
    
    return ''.join(id_parts)

def compute_key(id_str):
    """
    ASSUMPTION: Key is computed similarly to ID but using the ID string as input
    or using a different set of random calls. The writeup says both ID and Key
    are computed by parsing a string to the same random engine function.
    The key likely uses the name or the ID as input to a similar akdd()-style function.
    """
    # ASSUMPTION: key is computed by running akdd on the name directly
    # or on the ID - not fully clear from writeup
    # We just re-run the same function with id_str as input
    Temp2 = 1.0
    key_parts = []
    
    for i in range(1, len(id_str) + 1):
        char = id_str[i-1]
        asc_val = ord(char)
        
        Temp1 = Temp2 * i
        Temp1 = Temp1 * asc_val
        Temp2 = Temp1
        
        packed = struct.pack('<f', float(Temp2) if abs(Temp2) < 3.4e38 else 1.0)
        bits = struct.unpack('<I', packed)[0]
        current_seed = bits & 0xFFFFFF
        
        rnd_val, current_seed = vb6_rnd_from_seed(current_seed)
        
        product = rnd_val * 7055.475
        hex_part = '{:X}'.format(int(product) & 0xFFFF)
        key_parts.append(hex_part)
    
    return ''.join(key_parts)

def generate_id_and_key(name):
    """
    Full generation: ID and Key both derived from the VB RNG seeded by the name.
    From the writeup: 'Both ID and Key are computed by parsing a String to a function
    that will explore the weak VB Random Number Engine'
    ASSUMPTION: The 'string' parsed is the name for ID, and something else for Key.
    """
    rnd_str = compute_id(name)
    the_id  = akdd_function(rnd_str)
    the_key = compute_key(name)  # ASSUMPTION
    return the_id, the_key

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: serial corresponds to the Key computed from name.
    The crackme stores ID in Key32a and Key in Key32 in the registry.
    We check if the serial matches the computed key.
    """
    _, expected_key = generate_id_and_key(name)
    return serial.upper() == expected_key.upper()

def keygen(name):
    """
    Generate a valid serial for the given name.
    Returns the computed key.
    """
    _, key = generate_id_and_key(name)
    return key


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
