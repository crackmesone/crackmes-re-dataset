import ctypes

def hash1(name_bytes):
    """First hash: NOT each byte, then ROL(eax,7) XOR byte for each char."""
    # NOT each byte in name
    notted = bytes(b ^ 0xFF for b in name_bytes)
    eax = 0
    for b in notted:
        # rol eax, 7 (32-bit)
        eax = ((eax << 7) | (eax >> 25)) & 0xFFFFFFFF
        # xor al, byte
        eax = (eax & 0xFFFFFF00) | ((eax & 0xFF) ^ b)
    return eax

def hash2(name_bytes):
    """Second hash: uses original (NOTted) bytes from name after hash1 processing.
    # ASSUMPTION: The 'sName' buffer at this point contains the NOTted bytes
    # (since hash1 modifies in-place via 'not byte ptr[edx]').
    # So hash2 operates on NOTted bytes.
    """
    notted = bytes(b ^ 0xFF for b in name_bytes)
    ecx = 0
    for b in notted:
        eax = b & 0xFFFFFFFF
        # ror eax, 16
        eax = ((eax >> 16) | (eax << 16)) & 0xFFFFFFFF
        # add al, byte ptr[edx]  (add original notted byte to al)
        eax = (eax & 0xFFFFFF00) | ((eax & 0xFF) + b) & 0xFF
        # xor eax, 0xdeadc0de
        eax = (eax ^ 0xDEADC0DE) & 0xFFFFFFFF
        # ror ecx, 7
        ecx = ((ecx >> 7) | (ecx << 25)) & 0xFFFFFFFF
        # add ecx, eax
        ecx = (ecx + eax) & 0xFFFFFFFF
    return ecx

def hash3(name_bytes):
    """Third hash: uses NOTted bytes.
    # ASSUMPTION: same buffer (NOTted) is used.
    For each byte:
      ecx = 8
      ebx = byte
      loop 8 times: shr ebx,1; adc eax,0; dec ebx; jnz
    Note: 'dec ebx; jnz' - this checks ebx after decrement.
    The loop runs while ebx != 0 after dec.
    This is tricky: after shr ebx,1 and adc eax,0 (carry from shr),
    then dec ebx; if ebx!=0 continue.
    # ASSUMPTION: ecx=8 is the outer loop count but inner loop uses ebx as counter
    # and terminates when ebx==0 after dec. The 'dec ebx; jnz' suggests
    # the loop continues while ebx (the shifted value minus 1) != 0.
    """
    notted = bytes(b ^ 0xFF for b in name_bytes)
    eax = 0
    for b in notted:
        # ecx = 8 (unused as loop counter here based on asm)
        ebx = b & 0xFF
        while True:
            # shr ebx, 1 -> carry = old bit0
            carry = ebx & 1
            ebx = (ebx >> 1) & 0xFFFFFFFF
            # adc eax, 0 -> eax += carry
            eax = (eax + carry) & 0xFFFFFFFF
            # dec ebx
            ebx = (ebx - 1) & 0xFFFFFFFF
            # jnz __extract_bits
            if ebx == 0:
                break
        # xor eax, 0xdeadc0de
        eax = (eax ^ 0xDEADC0DE) & 0xFFFFFFFF
        # rol eax, 5
        eax = ((eax << 5) | (eax >> 27)) & 0xFFFFFFFF
    return eax

def keygen(name):
    """Generate serial for given name (must be > 4 chars)."""
    if len(name) < 5:
        raise ValueError("Name must be longer than 4 characters")
    name_bytes = name.encode('latin-1')
    h1 = hash1(name_bytes)
    h2 = hash2(name_bytes)
    h3 = hash3(name_bytes)
    serial = "{:08X}{:08X}{:08X}".format(h1, h2, h3)
    return serial

def verify(name, serial):
    """Verify name/serial pair."""
    if len(name) < 5:
        return False
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
    except Exception:
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
