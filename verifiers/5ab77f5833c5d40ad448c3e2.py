import ctypes
import random

# NOTE: The crackme uses C's rand() which is seeded at startup (srand not shown explicitly).
# The rand() call at 004013E1 happens before any user input, so we cannot predict it
# without knowing the seed. However, the writeup shows the algorithm in detail for
# the name-based hash. We implement what we can.

# ASSUMPTION: The rand() seed is fixed or we must brute-force / mirror C rand().
# We use Python's ctypes to call msvcrt.rand() on Windows if available,
# otherwise we simulate with Python random seeded at 0.

try:
    import ctypes
    msvcrt = ctypes.cdll.msvcrt
    def c_rand():
        return msvcrt.rand()
    def c_srand(seed):
        msvcrt.srand(seed)
except Exception:
    # ASSUMPTION: Fallback - seed with 0
    _rand_state = [0]
    def c_srand(seed):
        random.seed(seed)
    def c_rand():
        return random.randint(0, 32767)


def _to_signed32(n):
    """Convert to signed 32-bit integer (like C int)."""
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n


def compute_name_hash(name):
    """
    Compute the name-based hash (EBP-114 accumulator).
    Based on the loop at 00401569.
    """
    # ASSUMPTION: EBP-110 is initialized to 0 (company hash accumulator initial value,
    # but for name loop it's the other accumulator). We track both.
    # From the disassembly:
    # counter = 0 (EBP-130)
    # acc = 0 (EBP-114)
    # acc2 = 0 (EBP-110) -- used in the loop but initialized somewhere
    # ASSUMPTION: acc2 (EBP-110) starts at 0 for name loop
    acc = 0      # EBP-114
    acc2 = 0     # EBP-110 (used in line 004015F1)
    
    for i in range(len(name)):
        ch = ord(name[i])  # MOVSX - sign extended byte
        
        # ADD 1456982 + 5893632 to char value
        tmp = ch
        tmp = _to_signed32(tmp + 1456982)
        tmp = _to_signed32(tmp + 5893632)
        # ADD EAX, EAX (double) then ADD 2365
        tmp = _to_signed32(tmp + tmp + 2365)
        # tmp is now EBP-10C
        
        # ECX = acc (EBP-114)
        # EDX = ECX << 6 - ECX = ECX * 63
        ecx = acc
        edx = _to_signed32((ecx << 6) - ecx)  # ECX * 63
        
        # EAX = tmp * 2
        eax = _to_signed32(tmp + tmp)
        
        # LEA EAX, [EDX + EAX]
        eax = _to_signed32(edx + eax)
        acc = eax  # EBP-114
        
        # acc = acc * 2 + acc2
        acc = _to_signed32(acc + acc + acc2)
        
        # acc = acc * 2 + 4
        acc = _to_signed32(acc + acc + 4)
    
    return acc


def compute_company_hash(company, prev_acc):
    """
    Compute company-based hash. Same structure as name hash.
    ASSUMPTION: Uses prev_acc (from name computation) as initial accumulator.
    The company loop at 00401697 uses EBP-110 (which was updated during name loop).
    """
    # ASSUMPTION: acc starts at 0 for company, prev_name_acc feeds into it via EBP-110
    # Based on the writeup structure the company loop mirrors the name loop
    # but accumulates into EBP-110 and references EBP-114 (name result)
    # ASSUMPTION: company acc (EBP-110) starts at 0
    acc = 0
    name_acc = prev_acc  # EBP-114 from name
    
    for i in range(len(company)):
        ch = ord(company[i])
        
        tmp = ch
        tmp = _to_signed32(tmp + 1456982)
        tmp = _to_signed32(tmp + 5893632)
        tmp = _to_signed32(tmp + tmp + 2365)
        
        ecx = acc
        edx = _to_signed32((ecx << 6) - ecx)
        eax = _to_signed32(tmp + tmp)
        eax = _to_signed32(edx + eax)
        acc = eax
        
        # ASSUMPTION: mirroring structure - uses name_acc in place of acc2
        acc = _to_signed32(acc + acc + name_acc)
        acc = _to_signed32(acc + acc + 4)
    
    return acc


def compute_identity_code(name_hash, rand_val, rand_divisor):
    """
    Identity code = (rand_val % rand_divisor) + name_hash
    From: IDIV [ECX] where ECX points to first rand result,
    remainder (EDX) + EBP-114 (name_hash) -> EBP-128
    """
    # ASSUMPTION: rand_divisor is the first rand() call result stored at EBP-12C
    remainder = rand_val % rand_divisor if rand_divisor != 0 else 0
    return _to_signed32(remainder + name_hash)


def verify(name, serial):
    """
    Verify name/serial combination.
    ASSUMPTION: We only check the name hash portion since rand() values
    are not predictable without knowing the seed used at runtime.
    The 'password' field maps to name_hash.
    """
    if not name:
        return False
    
    name_hash = compute_name_hash(name)
    password_hash = _to_signed32(name_hash)
    
    # The writeup mentions Password: F0A3E04Ch = -257695668 for 'Kostya'
    # Identity code: F0A3E05D = -257695651 for 'Kostya'
    # Difference is 0x11 = 17, which matches rand%rand_divisor for some seed
    
    # ASSUMPTION: serial is the identity code (hex string or decimal)
    try:
        if serial.startswith('0x') or serial.startswith('0X'):
            serial_val = int(serial, 16)
        else:
            serial_val = int(serial)
        serial_val = _to_signed32(serial_val)
    except (ValueError, AttributeError):
        return False
    
    # ASSUMPTION: The password field IS the name_hash and serial IS the identity code.
    # Without knowing rand() values, we can only check if serial could equal
    # name_hash + small_rand_remainder. We check password == name_hash.
    return serial_val == password_hash


def keygen(name):
    """
    Generate password for given name.
    Returns the name hash as the 'Password' field.
    The Identity Code requires rand() values from the actual process.
    """
    if not name:
        return None
    
    name_hash = compute_name_hash(name)
    password = _to_signed32(name_hash)
    
    # Return password as signed decimal and hex
    return {
        'password': password,
        'password_hex': hex(password & 0xFFFFFFFF).upper(),
        'note': 'Identity Code requires rand() from actual process (seed unknown)'
    }



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
