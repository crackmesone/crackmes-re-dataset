import ctypes
import time

# The serial is generated using C's rand() seeded with time(NULL).
# We replicate the exact 32-bit arithmetic used in the crackme.

# C standard library rand() state (LCG as used by MSVC)
# MSVC rand(): state = state * 214013 + 2531011; return (state >> 16) & 0x7FFF

def _msvc_srand(seed):
    """Returns initial state for MSVC rand."""
    return ctypes.c_uint32(seed).value

def _msvc_rand(state):
    """MSVC LCG rand. Returns (new_state, rand_value)."""
    state = ctypes.c_uint32(state * 214013 + 2531011).value
    return state, (state >> 16) & 0x7FFF

def _digit_from_rand(r):
    """
    Replicates the assembly:
      ecx = rand()
      eax = 0x66666667
      edx:eax = eax * ecx  (signed 32x32->64)
      edx >>= 2  (arithmetic)
      eax = ecx >> 31  (sign bit)
      edx -= eax
      eax = edx
      eax <<= 2
      eax += edx
      eax += eax          -> eax = edx * 10
      ecx -= eax          -> ecx = ecx - (ecx//10)*10 = ecx % 10
      al += 0x30          -> ascii digit

    This computes: digit = rand() % 10, then + 0x30 for ASCII.
    """
    ecx = ctypes.c_int32(r).value
    # 64-bit signed multiply: 0x66666667 * ecx
    product = ctypes.c_int64(0x66666667).value * ecx
    # edx = high 32 bits
    edx = ctypes.c_int32((product >> 32) & 0xFFFFFFFF).value
    # sar edx, 2
    edx = edx >> 2
    # eax = ecx >> 31 (sign bit of ecx)
    eax = ctypes.c_int32(ecx).value >> 31
    # edx -= eax
    edx = ctypes.c_int32(edx - eax).value
    # eax = edx; shl eax,2; add eax,edx; add eax,eax  => eax = edx*10
    eax = ctypes.c_int32(edx).value
    eax = ctypes.c_int32(eax << 2).value
    eax = ctypes.c_int32(eax + edx).value
    eax = ctypes.c_int32(eax + eax).value
    # ecx -= eax  => remainder
    ecx = ctypes.c_int32(ecx - eax).value
    # add al, 0x30
    digit_char = chr((ecx & 0xFF) + 0x30)
    return digit_char

def _generate_serial(seed):
    """Generate the 30-character serial from a given time seed."""
    state = _msvc_srand(seed)
    serial = []
    for _ in range(0x1E):  # 0 to 0x1D inclusive = 30 iterations
        state, r = _msvc_rand(state)
        serial.append(_digit_from_rand(r))
    return ''.join(serial)

def keygen(name=None):
    """
    Generate the serial for the current time.
    The crackme uses time(NULL) as the seed, so this must be called
    at the same second as the crackme runs (or in a bat file together).
    """
    # ASSUMPTION: We use int(time.time()) to match C's time(NULL).
    seed = int(time.time())
    return _generate_serial(seed)

def verify(name, serial):
    """
    The crackme compares the user input with the generated serial via strcmp.
    Since the serial is time-based, we check against the current second
    and a small window around it.
    """
    # ASSUMPTION: Allow a small time window (+/- 2 seconds) for timing drift.
    t = int(time.time())
    for delta in range(-2, 3):
        if serial == _generate_serial(t + delta):
            return True
    return False


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
            print(_sv)
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
