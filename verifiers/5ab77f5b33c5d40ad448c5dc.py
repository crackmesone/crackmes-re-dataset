import struct
import math

# VB6 Random Number Generator (Rnd function) implementation
# Based on the assembly code shown in the writeup:
# The VB6 RNG state is a 24-bit integer stored internally.
# Rnd(-1) resets/seeds based on the argument (but since we call Randomize(seed) after, this just resets state).
# Rnd() with no args advances state and returns a float in [0,1)

# From the assembly:
# if arg < 0: use arg bits as seed directly
# new_seed = (old_seed * 0x2BC03 + 0xC39EC3) & 0xFFFFFF  (roughly)
# Actually from the code:
# ECX = seed
# ECX = ECX * 0x2BC03
# EAX = 0xFFC39EC3
# EAX = EAX - ECX
# EAX = EAX & 0xFFFFFF
# result = EAX / 0x1000000

# ASSUMPTION: The VB6 RNG internal state is 24 bits.
# The formula derived from the assembly:
#   new_state = (0xFFC39EC3 - old_state * 0x2BC03) & 0xFFFFFF
# But Randomize(seed) sets the internal state based on seed.
# ASSUMPTION: Randomize(x) seeds the RNG by XORing/mixing x into the current state.
# The exact Randomize seeding is not fully described; we approximate it.

# VB6 RNG state
_rng_state = 0

def _vb6_rnd_negative(val):
    """Rnd(negative) - seeds the generator from the negative float32 bits."""
    global _rng_state
    # Pack as float32 and use lower 24 bits of the integer representation
    packed = struct.pack('<f', val)
    int_val = struct.unpack('<I', packed)[0]
    # From assembly: SHR ECX,18 + ADD + AND 0xFFFFFF
    ecx = int_val
    ecx2 = (ecx >> 24) + ecx  # SHR 18 is 0x18 = 24
    ecx2 = ecx2 & 0xFFFFFF
    # Then: new = (0xFFC39EC3 - ecx2 * 0x2BC03) & 0xFFFFFF
    new_state = (0xFFC39EC3 - ecx2 * 0x2BC03) & 0xFFFFFF
    _rng_state = new_state
    return new_state / 0x1000000

def _vb6_rnd_next():
    """Rnd() - advance state and return next value."""
    global _rng_state
    new_state = (0xFFC39EC3 - _rng_state * 0x2BC03) & 0xFFFFFF
    _rng_state = new_state
    return new_state / 0x1000000

def _vb6_randomize(seed_float):
    """Randomize(x) - mixes seed into RNG state.
    ASSUMPTION: Randomize XORs the float32 bits of seed with current state upper bits.
    This is an approximation; exact VB6 Randomize behavior not fully described.
    """
    global _rng_state
    # Pack seed as float32
    try:
        packed = struct.pack('<f', seed_float)
    except (OverflowError, struct.error):
        packed = struct.pack('<f', 0.0)
    int_val = struct.unpack('<I', packed)[0]
    # VB6 Randomize: XOR lower 24 bits of seed mantissa with current state
    # ASSUMPTION: mix = (current_state XOR (int_val & 0xFFFFFF))
    _rng_state = (_rng_state ^ (int_val & 0xFFFFFF)) & 0xFFFFFF

def akdd(text, number):
    """Implements the akdd routine from the crackme."""
    # Step 1: Compute Temp2 from the text
    mul = 1.0
    temp2 = 1.0
    for i in range(1, len(text) + 1):
        ch = text[i - 1]
        asc_val = ord(ch)
        temp1 = temp2 * i          # Temp1 = Temp2 * i
        mul = asc_val * temp1       # Mul = Asc(char) * Temp1
        temp2 = math.sqrt(abs(mul)) # Temp2 = Sqr(Mul)
    
    # Step 2: Rnd(-1) - called with -1 (literal), resets/seeds RNG
    _vb6_rnd_negative(-1.0)
    
    # Step 3: Randomize(Temp2)
    _vb6_randomize(temp2)
    
    # Step 4: Generate 4 pseudo-random numbers, multiply by number, hex-concat
    result = ""
    for i in range(4):
        r = _vb6_rnd_next()
        val = int(number * r)  # number * Rnd()
        result += hex(val)[2:].upper()  # Hex($4)
    
    return result

def generate_serial(name):
    """Generate serial for a given name by chaining akdd calls."""
    # ASSUMPTION: The serial is formed by concatenating outputs of 4 akdd calls.
    # akdd 2.1: number=18, input=name
    # akdd 2.2: number=13, input=output of akdd 2.1
    # akdd 2.3: number=15, input=output of akdd 2.2
    # akdd 2.4: number=110, input=output of akdd 2.3
    # ASSUMPTION: Based on writeup: "The Username is just parsed to the first call,
    #             the next calls use the output of the previous call(s)"
    out1 = akdd(name, 18)
    out2 = akdd(out1, 13)
    out3 = akdd(out2, 15)
    out4 = akdd(out3, 110)
    # ASSUMPTION: The final serial is the concatenation or one of these outputs.
    # The writeup says "check for MaxLength" suggesting serial has fixed length.
    serial = out1 + out2 + out3 + out4
    return serial

def keygen(name):
    return generate_serial(name)

def verify(name, serial):
    """Verify name/serial pair."""
    expected = generate_serial(name)
    return serial == expected


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
