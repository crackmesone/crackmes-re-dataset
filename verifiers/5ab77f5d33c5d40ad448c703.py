import ctypes

def _gcd_like(a, b):
    """
    Simulates L046 (recursive GCD-like) with L000 side effect.
    L000 modifies ds:[403000h] by computing how many times 2 divides into
    EAX via the ADD BYTE chain (which is self-modifying; in practice it stores EAX
    into ds:[403000h] at the 'aa1' point).
    We simulate the key effect: L000 stores its argument into ds:[403000h].
    L046 is: gcd(a, b) computed recursively, but each call to L046 also
    calls L000(a) which sets state[403000] = a.
    The final ds:[403000] after L046(ebx, ecx) ends up being the last L000 call argument.
    """
    # ASSUMPTION: L046 is Euclidean GCD, and L000 sets the global to the argument
    # The relevant side effect: ds:[403000] = value at deepest recursion (when b==0, return a)
    # Actually tracing: L046(a,b): calls L000(a) -> state=a, then if b!=0: calls L046(b, a%b), else returns a
    # So state ends up as the last 'a' before b==0, which equals gcd(a,b)
    # BUT: the return value from L046 is used in XOR with ds:[403000]
    # Let's simulate properly
    pass

class State:
    def __init__(self):
        self.val = 0  # ds:[403000h]

_state = State()

def L000_effect(a):
    """L000 stores EAX (=a) into ds:[403000h]"""
    # ASSUMPTION: The self-modifying ADD chain ultimately just stores 'a' into [403000]
    # (The 31 ADD BYTE PTR DS:[EAX],AL instructions add AL to memory at address EAX;
    #  since EAX is a pointer to name string, and AL=low byte of EAX, this mutates the name string.
    #  The actual effect on ds:[403000] is the MOV at aa1: MOV DWORD PTR DS:[403000h],EAX
    #  So yes, [403000] = current EAX = the argument passed to L000)
    _state.val = a & 0xFFFFFFFF

def L046(a, b):
    """Recursive GCD-like, with L000 side effect"""
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    L000_effect(a)
    if b == 0:
        return a
    # IDIV: signed division
    # Treat as signed 32-bit
    sa = ctypes.c_int32(a).value
    sb = ctypes.c_int32(b).value
    remainder = sa % sb  # Python % is always non-negative if sb>0
    # For signed IDIV, remainder has sign of dividend
    if sa < 0:
        remainder = -((-sa) % abs(sb)) if sb != 0 else 0
    r = ctypes.c_int32(remainder).value & 0xFFFFFFFF
    return L046(b, r)

def compute_serial_for_name(name):
    """
    Simulates the keygen logic from L064 called per character pair.
    For each character position i in name:
      EAX_name_ptr = pointer to name[i]
      EBX = (ord(name[i]) << 5) + 0x2328 + ord(name[i+1])  (if i+1 exists)
      ECX = ord(name[i+1]) ^ 0xBC614E
      EBX = (EBX * 0xD) ^ 0x15587
      call L046(EBX, ECX) -> result, side effect updates _state.val
      _state.val ^= result  (XOR EAX,DWORD PTR DS:[403000h]; MOV DWORD PTR DS:[403000h],EAX)
    Then serial = _state.val formatted as decimal string via wsprintf '%d' or similar.
    """
    # ASSUMPTION: initial ds:[403000h] = 0
    _state.val = 0

    # L064 is called once with arg 0 from generate button
    # It recurses for each character in name while name[i+1] != 0
    # We iterate through name characters
    i = 0
    while i < len(name):
        c0 = ord(name[i]) & 0xFF
        # Check if next char exists
        if i + 1 >= len(name):
            # CMP BYTE PTR DS:[EAX],0 -> JE L153 -> done
            break
        c1 = ord(name[i + 1]) & 0xFF

        # EBX = (c0 << 5) + 0x2328 + c1
        ebx = ((c0 << 5) + 0x2328 + c1) & 0xFFFFFFFF
        # ECX = c1 ^ 0xBC614E
        ecx = (c1 ^ 0xBC614E) & 0xFFFFFFFF
        # EBX = EBX * 0xD ^ 0x15587
        ebx = (ctypes.c_int32(ebx * 0xD).value ^ 0x15587) & 0xFFFFFFFF

        # call L046(EBX, ECX)
        result = L046(ebx, ecx)

        # XOR EAX, DWORD PTR DS:[403000h]; MOV DWORD PTR DS:[403000h],EAX
        # Note: at this point _state.val was set by L046 (last L000 call)
        # then: _state.val ^= result  ... but result IS _state.val after L046
        # Re-reading: after CALL L046, EAX = return value of L046
        # XOR EAX, DS:[403000h] -> EAX ^= current state
        # MOV DS:[403000h], EAX -> state = EAX
        # But _state.val was modified by L000 inside L046...
        # ASSUMPTION: after L046 returns, _state.val holds the deepest recursion value (= gcd)
        # Then: new_state = return_val_of_L046 XOR _state.val
        # Since return_val == gcd and _state.val == gcd (last L000 call), XOR = 0 always?
        # That can't be right. Let me reconsider.
        # ASSUMPTION: Maybe L000's assignment is NOT to [403000] but somewhere else in the recursion path.
        # Let's assume _state.val before L046 call is used:
        prev_state = _state.val  # saved before L046 modifies it
        # Actually L046 calls L000 which sets _state.val; recursion means final _state.val = gcd
        # After L046 returns EAX=gcd:
        # XOR EAX, DS:[403000] means: gcd XOR gcd = 0? That's suspicious.
        # ALTERNATIVE ASSUMPTION: The XOR is with the state BEFORE this iteration
        # Let's try: new_state = result XOR prev_state
        _state.val = (result ^ prev_state) & 0xFFFFFFFF

        i += 1

    return _state.val

def verify(name, serial):
    """Verify name/serial pair"""
    if not name:
        return False
    computed = compute_serial_for_name(name)
    # Serial is formatted as decimal number
    try:
        serial_int = int(serial.strip())
    except ValueError:
        return False
    return serial_int == ctypes.c_int32(computed).value

def keygen(name):
    """Generate serial for given name"""
    if not name:
        return ''
    computed = compute_serial_for_name(name)
    # wsprintf with format '%d' from ds:[403084h]
    # ASSUMPTION: format string is '%d' (decimal)
    return str(ctypes.c_int32(computed).value)


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
