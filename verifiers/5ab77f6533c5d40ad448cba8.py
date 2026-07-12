import ctypes

def _u32(x):
    return x & 0xFFFFFFFF

def _i32(x):
    x = x & 0xFFFFFFFF
    if x >= 0x80000000:
        return x - 0x100000000
    return x

# ---- Level 1 ----
# Input: a decimal integer string (len >= 3, only digits allowed)
# The integer string itself is iterated byte by byte
def level1_serial(int_str):
    """
    mov esi, offset szInt
    mov ecx, len
    xor eax, eax
    mov edx, len
    loop:
        xor eax, eax
        lodsb
        add eax, ebx
        add eax, edx
        mov ebx, eax
        add edx, 5
        dec ecx
        jnz loop
    xor edx, 198723h
    xor ebx, 286095h
    add edx, ebx
    xor edx, 781h
    => edx is the serial (decimal)
    """
    data = int_str.encode('ascii')
    length = len(data)
    eax = 0
    ebx = 0
    edx = length
    for b in data:
        eax = 0
        eax = _u32(eax + b)
        eax = _u32(eax + ebx)
        eax = _u32(eax + edx)
        ebx = eax
        edx = _u32(edx + 5)
    edx = _u32(edx ^ 0x198723)
    ebx = _u32(ebx ^ 0x286095)
    edx = _u32(edx + ebx)
    edx = _u32(edx ^ 0x781)
    return edx

# ---- Level 2 ----
# Uses crackme author's name "~Hellsp@wN~" and the level1 serial string
# Part A: sum of chars of author name starting from 0x42C568
AUTHOR_NAME = b'~Hellsp@wN~'

def level2_serial(int_str):
    """
    Part A: namesum
    mov esi, offset szAuthorName  ; "~Hellsp@wN~"
    mov ecx, sizeof szAuthorName
    mov edx, 42C568h
    xor eax, eax
    loop:
        lodsb
        add edx, eax
        dec ecx
        jnz loop
    => namesum = edx

    Part B: uses level1 serial string
    mov esi, offset szLevel1   ; level1 serial as decimal string
    mov ecx, sizeof szLevel1
    xor edx, edx
    xor ebx, ebx
    loop:
        lodsb
        add edx, eax
        imul edi, ebx
        add edi, namesum
        dec ebx
        dec ecx
        jnz loop
    add edi, namesum
    => edi is level2 serial number part
    prefix: "Cracker-"
    """
    # Part A: namesum
    edx = 0x42C568
    for b in AUTHOR_NAME:
        edx = _u32(edx + b)
    namesum = edx

    # level1 serial as decimal string
    l1 = level1_serial(int_str)
    szLevel1 = str(l1).encode('ascii')
    length = len(szLevel1)

    # Part B
    edx2 = 0
    ebx = 0
    edi = 0
    # ASSUMPTION: edi starts at 0, ebx starts at 0, and ebx decrements (goes negative in 32-bit)
    for b in szLevel1:
        eax = b
        edx2 = _u32(edx2 + eax)
        # imul edi, ebx  => edi = edi * ebx
        edi = _u32(_i32(edi) * _i32(ebx) & 0xFFFFFFFF)
        edi = _u32(edi + namesum)
        ebx = _u32(ebx - 1)  # dec ebx
    edi = _u32(edi + namesum)
    return 'Cracker-' + str(_u32(edi))

# ---- Level 3 ----
# Conditions:
# (serialhex - 0x3D0900) mod 9 == 0
# The serial as hex is used as a virtual address (called as a function pointer)
# The working value found in solution: 4218196 decimal = 0x404D54 hex
# which points to a NOP before code that enables the next level button
# ASSUMPTION: the only truly valid serial for level3 is 4218196
LEVEL3_SERIAL = 4218196

# ---- Level 4 ----
# Input: the same integer string
# Uses first 2 chars of level1 serial
def level4_serial(int_str):
    """
    mov esi, offset inputint   ; the integer string bytes
    mov ebx, len
    mov ecx, len
    xor eax, eax
    xor edx, edx
    loop:
        lodsb
        add edx, eax
        imul edx, ebx
        dec ecx
        jnz loop
    => result = edx

    then get first 2 chars of level1 serial string, convert to hex (as 2-digit hex?)
    # ASSUMPTION: "convert to hex" means parse first 2 decimal chars as a hex number
    multiply by len of inputint
    multiply that by result above
    xor with 22062004h
    => level4 serial
    """
    data = int_str.encode('ascii')
    length = len(data)
    ebx = length
    ecx = length
    edx = 0
    for b in data:
        eax = b
        edx = _u32(edx + eax)
        # imul edx, ebx (signed)
        edx = _u32(_i32(edx) * _i32(ebx) & 0xFFFFFFFF)
    result = edx

    l1 = level1_serial(int_str)
    szL1 = str(l1)
    # ASSUMPTION: first 2 chars of level1 serial string, interpreted as hex digits
    first2 = szL1[:2]
    first2_val = int(first2, 16)

    # multiply by len of inputint
    tmp = _u32(first2_val * length)
    # multiply by result
    tmp = _u32(_i32(tmp) * _i32(result) & 0xFFFFFFFF)
    # xor with 22062004h
    tmp = _u32(tmp ^ 0x22062004)
    return tmp


def verify(name, serial):
    """
    ASSUMPTION: 'name' here is the integer string entered in the bottom edit box.
    The crackme uses a single integer input across all levels.
    Serial is expected as a dict with keys 'level1', 'level2', 'level3', 'level4'
    or as a tuple (l1, l2, l3, l4).
    For a simple verify, we check all four levels.
    """
    # Validate name: must be >= 3 chars, all digits
    if len(name) < 3:
        return False
    if not name.isdigit():
        return False

    if isinstance(serial, dict):
        s1 = serial.get('level1')
        s2 = serial.get('level2')
        s3 = serial.get('level3')
        s4 = serial.get('level4')
    elif isinstance(serial, (list, tuple)) and len(serial) == 4:
        s1, s2, s3, s4 = serial
    else:
        return False

    ok1 = (str(level1_serial(name)) == str(s1))
    ok2 = (level2_serial(name) == str(s2))
    ok3 = (str(LEVEL3_SERIAL) == str(s3))
    ok4 = (str(level4_serial(name)) == str(s4))
    return ok1 and ok2 and ok3 and ok4


def keygen(name):
    """
    Given an integer string (name), generate all four serials.
    Returns a dict.
    """
    if len(name) < 3 or not name.isdigit():
        raise ValueError("name must be a decimal integer string of at least 3 digits")
    l1 = level1_serial(name)
    l2 = level2_serial(name)
    l3 = LEVEL3_SERIAL
    l4 = level4_serial(name)
    return {
        'level1': str(l1),
        'level2': l2,
        'level3': str(l3),
        'level4': str(l4),
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
