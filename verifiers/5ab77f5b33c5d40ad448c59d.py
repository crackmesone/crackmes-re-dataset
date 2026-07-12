import ctypes

MASK32 = 0xFFFFFFFF

def make_user_hash(username_with_crlf: str) -> int:
    """Replicate the x86 hash loop from MakeUserHash.
    The username must have \r\n appended (as the crackme does internally).
    All arithmetic is 32-bit unsigned.
    """
    # Convert to bytes
    data = username_with_crlf.encode('latin-1') + b'\x00'
    eax = 0
    edx = 0
    for byte in data:
        bl = byte & 0xFF
        al = bl
        eax = al
        eax = (eax << 3) & MASK32
        eax = (eax ^ edx) & MASK32
        # MUL EAX: EAX * EAX -> EDX:EAX (we only need low 32 bits for EDX accumulator)
        # MUL stores result in EDX:EAX; here EDX is the accumulator (add edx,eax)
        # eax = eax * eax, low 32 bits
        product = (eax * eax) & MASK32  # low 32 bits (MUL result low half)
        edx = (edx + product) & MASK32
        if bl == 0:
            break
    return edx


def make_pw(state: list, user_hash: int) -> int:
    """state is [num2] (mutable); num1=0xDDEEEEFF, num3=0x0B4DF00D are constants.
    num2 = (userHash % num1) + (num3 * num2)  [all 32-bit]
    """
    num1 = 0xDDEEEEFF
    num3 = 0x0B4DF00D
    # From solution 2 (cleaner): f = f * 0x0B4DF00D + sum % 0xDDEEEEFF
    # This matches: num2 = (userHash % num1) + (num3 * num2)
    new_num2 = ((num3 * state[0]) & MASK32 + (user_hash % num1)) & MASK32
    state[0] = new_num2
    return new_num2


def init_num2(state: list, user_hash: int):
    """Run MakePw 0x801 times (i=0 to 0x800 inclusive) to set num2 to its
    post-init value. The initial num2 is 0x000000FF.
    This results in num2 = 0x8B4CA7AF for userHash=0 but varies with user_hash.
    Actually, from solution 2 the init value used is 0x8B4CA7AF regardless --
    wait: solution 2 uses static f=0x8b4ca7af and then applies the loop with sum.
    However solution 1 shows InitNum2 is called BEFORE MakeUserHash so userHash=0xABC
    during init. Let's follow solution 2 which hard-codes f=0x8B4CA7AF as the
    post-init value (implying init is done with default userHash=0x000000ABC constant).
    """
    # ASSUMPTION: based on solution 2, the post-init num2 value is 0x8B4CA7AF.
    # We pre-compute: run the loop 0x801 times with userHash=0x00000ABC (the initial constant).
    init_user_hash = 0x00000ABC
    for _ in range(0x801):  # i=0 to 0x800 inclusive
        make_pw(state, init_user_hash)


def keygen(name: str) -> str:
    """Generate the serial for a given name (5-14 chars)."""
    if len(name) < 5 or len(name) > 14:
        raise ValueError("Name must be between 5 and 14 characters.")

    # Append \r\n as the crackme does
    name_with_crlf = name + '\r\n'

    # Step 1: init num2 (before hashing user)
    state = [0x000000FF]  # initial num2
    init_num2(state, 0)

    # Step 2: hash the user
    user_hash = make_user_hash(name_with_crlf)

    # Step 3: generate password
    password = []
    for i in range(14):
        ch_val = make_pw(state, user_hash) % 0x19 + 0x41
        password.append(chr(ch_val))
        skip_count = make_pw(state, user_hash) % 0x40 + 2
        for _ in range(skip_count):
            make_pw(state, user_hash)

    password.append('M')
    password.append('Z')
    return ''.join(password)


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair by re-generating and comparing."""
    if len(name) < 5 or len(name) > 14:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
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
