import struct

def _stage1(eax, ebx):
    """
    Simulates the stage1 assembly loop.
    Runs EBX iterations of the arithmetic sequence on EAX.
    All arithmetic is 32-bit signed/unsigned (we use masks).
    """
    MASK = 0xFFFFFFFF

    def to_signed32(n):
        n = n & MASK
        if n >= 0x80000000:
            n -= 0x100000000
        return n

    def idiv32(eax, ecx):
        # signed division
        return int(to_signed32(eax) / ecx)  # truncate toward zero

    eax = eax & MASK
    ebx = ebx & MASK
    ecx = 0
    edx = 0

    count = ebx
    for _ in range(count):
        ecx = eax
        edx = 0x746
        eax = (eax * eax) & MASK
        eax = (eax * 4) & MASK
        ecx = (ecx * 9) & MASK
        eax = (eax + ecx) & MASK
        eax = (eax + edx) & MASK
        edx = 0
        ecx = 5
        eax = idiv32(eax, ecx) & MASK
        edx = 0x153F
        ecx = eax
        eax = (eax * eax) & MASK
        eax = (eax * 2) & MASK
        ecx = (ecx * 4) & MASK
        eax = (eax + ecx) & MASK
        eax = (eax + edx) & MASK
        ecx = 0x15F1F
        eax = (eax - ecx) & MASK
        edx = 0
        ecx = 4
        eax = idiv32(eax, ecx) & MASK
        ecx = 0x5A2D9
        eax = (eax + ecx) & MASK
        eax = (eax - 0xBBD59) & MASK

    return eax


def _stage3(eax):
    """
    Converts eax to binary string (like stage3 in the writeup).
    Repeatedly divides by 2, collecting remainders, then reverses.
    """
    result = []
    ecx = 2
    edx = 0
    while True:
        edx = eax % ecx
        eax = eax // ecx
        result.append(chr(edx + 0x30))
        edx = 0
        if eax == 0:
            break
    result.reverse()
    return ''.join(result)


# ASSUMPTION: The serial format is: PART1-PART2-PART3
# where PART1 is 3 digits, PART2 is 5 digits, PART3 is 8 digits
# Based on the solution bruteforce results:
# Stage 1: serial length -> stage1(length, 1) == 0xFFFCF2C0  => length determined
# Stage 2: first 3 digits -> stage1(digits, 0x1C4) == 0x33F9E44F
# Stage 3: next 5 digits -> complex check involving stage3 then stage1 == 0x0A3B5E6C
# Stage 4: last 8 digits -> stage3(stage1(digits, 0x921371)) == '100011110001001111000010001001'

# The solution found fixed values (not name-dependent), so this is a fixed serial crackme.
# ASSUMPTION: serial is not name-dependent (no name field visible in analysis)

# Pre-computed answers from the bruteforce solution:
# Stage 1: serial length = ? (bruteforced to satisfy stage1(len,1)==0xFFFCF2C0)
# Stage 2: first 3 digits = ? (bruteforced to satisfy stage1(val,0x1C4)==0x33F9E44F)
# Stage 3: next 5 digits = ? (bruteforced)
# Stage 4: last 8 digits = ? (bruteforced to satisfy stage3(stage1(val,0x921371))=='100011110001001111000010001001')

def _find_serial_length():
    """Bruteforce stage1 to find serial length where stage1(len, 1) == 0xFFFCF2C0"""
    target = 0xFFFCF2C0
    for i in range(1, 10000):
        if _stage1(i, 1) == target:
            return i
    return None


def _find_part1():
    """Bruteforce stage2: stage1(val, 0x1C4) == 0x33F9E44F, val in [100,999]"""
    target = 0x33F9E44F
    for i in range(100, 1000):
        if _stage1(i, 0x1C4) == target:
            return i
    return None


def _find_part2(var_ebx):
    """
    Bruteforce stage3: for val in [10000, 99999]
    binary_str = stage3(val)
    part_a = int(binary_str[:8])  # first 8 chars as decimal number
    part_b = int(binary_str[9:])  # after position 9
    result = part_a ^ part_b ^ 1
    stage1(result, 0x1D3E) == 0x0A3B5E6C
    """
    target = 0x0A3B5E6C
    for i in range(10000, 100000):
        bin_str = _stage3(i)
        if len(bin_str) < 9:
            continue
        try:
            part_a = int(bin_str[:8])
            part_b = int(bin_str[9:])
        except ValueError:
            continue
        val = part_a ^ part_b ^ 1
        if _stage1(val, 0x1D3E) == target:
            return i
    return None


def _find_part3():
    """Bruteforce stage4: stage3(stage1(val, 0x921371)) == '100011110001001111000010001001', val in [10000000, 99999999]"""
    target_bin = '100011110001001111000010001001'
    for i in range(10000000, 100000000):
        r = _stage1(i, 0x921371)
        bs = _stage3(r)
        if bs == target_bin:
            return i
    return None


# Cache computed serial (fixed serial, not name-based)
_SERIAL_CACHE = {}


def _compute_serial():
    if 'serial' in _SERIAL_CACHE:
        return _SERIAL_CACHE['serial']
    p1 = _find_part1()
    # ASSUMPTION: var_ebx value carried from stage1 into stage2 bruteforce is from stage1 loop init (0x1C4 = 452)
    p2 = _find_part2(0x1C4)
    p3 = _find_part3()
    if p1 is None or p2 is None or p3 is None:
        return None
    serial = f"{p1}-{p2}-{p3}"
    _SERIAL_CACHE['serial'] = serial
    return serial


def verify(name, serial):
    """
    Verify serial against the expected fixed serial.
    ASSUMPTION: name is not used in serial validation (fixed serial crackme).
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    try:
        p1 = int(parts[0])
        p2 = int(parts[1])
        p3 = int(parts[2])
    except ValueError:
        return False

    # Stage 1 check: total serial length
    # ASSUMPTION: serial string length triggers the stage1 length check
    serial_len = len(serial)
    target_len = _find_serial_length()
    if target_len is not None and serial_len != target_len:
        return False

    # Stage 2 check
    if _stage1(p1, 0x1C4) != 0x33F9E44F:
        return False

    # Stage 3 check
    bin_str = _stage3(p2)
    if len(bin_str) < 9:
        return False
    try:
        pa = int(bin_str[:8])
        pb = int(bin_str[9:])
    except ValueError:
        return False
    val = pa ^ pb ^ 1
    if _stage1(val, 0x1D3E) != 0x0A3B5E6C:
        return False

    # Stage 4 check
    r = _stage1(p3, 0x921371)
    bs = _stage3(r)
    if bs != '100011110001001111000010001001':
        return False

    return True


def keygen(name):
    """
    Generate valid serial. ASSUMPTION: name is not used.
    This performs bruteforce as in the original solution.
    Warning: stage 4 bruteforce over 8-digit range is very slow in Python.
    """
    p1 = _find_part1()
    p2 = _find_part2(0x1C4)
    p3 = _find_part3()
    if p1 and p2 and p3:
        return f"{p1}-{p2}-{p3}"
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
