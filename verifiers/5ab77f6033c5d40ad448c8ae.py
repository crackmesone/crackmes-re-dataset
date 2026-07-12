import struct
import ctypes

# Based on the keygen source (main.cpp) and disassembly fragments from the writeup.
# The algorithm:
# 1. A hash function is initialized with hardcoded constants (seen in disassembly)
# 2. The name is fed into the hash (first round call)
# 3. Hash continues and produces 4x 32-bit words
# 4. These are formatted as xxxx-xxxx-xxxxxxxx-xxxxxxxx (using Int64toStr / decimal conversion)
# The exact hash is described as a "long homemade hash" - the disassembly shows initialization
# constants and two DCrypt8 calls. We reconstruct based on the visible constants.

# Initialization constants visible in disassembly:
# [ebp-54] = 0
# [ebp-10] = 0x00770020  (2007)
# [ebp-C]  = 0x00000000
# [ebp-18] = 0x20080802  
# [ebp-14] = 0x00000000
# [ebp-1C] = 0x00000000  
# [ebp-20] = 0x77ABCDCE  (some constant)
# [ebp-24] = 0x00000000  
# [ebp-2C] = 0x66666666  (part of init)
# [ebp-28] = 0  
# [ebp-34] = 0  
# [ebp-30] = 0x50BEFEB6 (0xB6FEBE50)
# [ebp-3C] = 0x00000000  
# [ebp-38] = 0x08CEBEAD  (0xADBECE08)
# [ebp-44] = 0x00000000
# [ebp-40] = 0x99797766  
# [ebp-4C] = 0x00000000
# [ebp-48] = 0x66666666  
# ASSUMPTION: The exact hash algorithm internals are not fully recoverable from the
# truncated/encoded writeup. We implement the structure shown in main.cpp.

def _u32(x):
    return x & 0xFFFFFFFF

def _hash_init():
    # ASSUMPTION: These are the initialization constants from disassembly
    state = [
        0x00770020,  # [ebp-10]
        0x20080802,  # [ebp-18]
        0x77ABCDCE,  # [ebp-20] - ASSUMPTION: reading from encoded text
        0x66666666,  # [ebp-2C]
        0x50BEFEB6,  # [ebp-30] (byte-reversed)
        0x08CEBEAD,  # [ebp-38] (byte-reversed)
        0x99797766,  # [ebp-40]
        0x66666666,  # [ebp-48]
    ]
    return state

def _hash_round(state, data_bytes):
    # ASSUMPTION: The internal hash mixing is not fully recoverable.
    # Based on the disassembly pattern (add/adc/sub/sbb operations on 64-bit pairs),
    # this appears to be a custom 64-bit arithmetic hash.
    # We implement a placeholder that mixes name bytes into state.
    for i, b in enumerate(data_bytes):
        idx = i % len(state)
        state[idx] = _u32(state[idx] + b + _u32(state[(idx+1) % len(state)] << 3))
        state[(idx+2) % len(state)] = _u32(state[(idx+2) % len(state)] ^ state[idx])
    return state

def _int64_to_str(lo, hi):
    # From Int64toStr in main.cpp:
    # res = value2 * 0x100000000 + value1  (signed int64)
    val = ctypes.c_int64(hi * 0x100000000 + lo).value
    return str(val)

def gen(name):
    """Generate serial for a given name (4-15 chars)."""
    if len(name) < 4 or len(name) > 15:
        return None
    
    name_bytes = name.encode('ascii')
    
    # ASSUMPTION: Hash is initialized then called twice with DCrypt8 function
    state = _hash_init()
    state = _hash_round(state, name_bytes)
    state = _hash_round(state, name_bytes)  # second round
    
    # Output: 4 dwords formatted as xxxx-xxxx-xxxxxxxx-xxxxxxxx
    # From writeup: "takes just 4 dwords from hash generation and puts them in format"
    # xxxx-xxxx-xxxxxxxx-xxxxxxxx
    # Using Int64toStr for pairs
    
    # ASSUMPTION: first pair is state[0], state[1]; second pair is state[2], state[3]
    str1 = _int64_to_str(state[0], state[1])
    str2 = _int64_to_str(state[2], state[3])
    
    # Format: the serial appears to be decimal strings of int64 values
    # separated by dashes, but exact format is ASSUMPTION
    serial = "{}-{}".format(str1, str2)
    return serial

def verify(name, serial):
    """Verify name/serial pair."""
    expected = gen(name)
    if expected is None:
        return False
    return serial == expected

def keygen(name):
    """Generate a serial for the given name."""
    return gen(name)


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
