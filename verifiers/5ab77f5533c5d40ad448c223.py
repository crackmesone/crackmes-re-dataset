import ctypes

def nameToNumber1(name):
    """call1 from solution 3 / nameToNumber1 from solution 2.
    Returns a 16-bit value (ECX) computed from the name.
    Algorithm reconstructed from the ASM in solution 3 (call1 proc).
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    length = len(name_bytes)
    dx = 0
    for b in name_bytes:
        ax = b & 0xFFFF
        # ADD DX, AX
        dx = (dx + ax) & 0xFFFF
        # IMUL DX, AX
        dx = (dx * ax) & 0xFFFF
        # XOR DX, AX
        dx = (dx ^ ax) & 0xFFFF
        # SHL DX, 2
        dx = (dx << 2) & 0xFFFF
        # SHR AX, 2
        ax_shifted = (ax >> 2) & 0xFFFF
        # XOR DX, AX (original ax >> 2)
        dx = (dx ^ ax_shifted) & 0xFFFF
        # ADD DX, DX
        dx = (dx + dx) & 0xFFFF
        # SUB DX, AX (original ax)
        dx = (dx - ax) & 0xFFFF
        # ROR DX, 4
        dx = ((dx >> 4) | (dx << (16 - 4))) & 0xFFFF
        # XOR DX, AX (original ax)
        dx = (dx ^ ax) & 0xFFFF
        # SUB DX, AX
        dx = (dx - ax) & 0xFFFF
        # XOR DX, AX
        dx = (dx ^ ax) & 0xFFFF
    # MOVZX ECX, DX -> return as 32-bit zero-extended
    return dx & 0xFFFF


def nameToNumber2(name):
    """call2 from solution 3 / nameToNumber2 from solution 2.
    Returns a 16-bit value (EDX) computed from the name.
    Algorithm reconstructed from the ASM in solution 3 (call2 proc).
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    bx = 0
    for b in name_bytes:
        ax = b & 0xFFFF
        # ADD BX, AX
        bx = (bx + ax) & 0xFFFF
        # XOR BX, AX
        bx = (bx ^ ax) & 0xFFFF
        # SUB BX, AX
        bx = (bx - ax) & 0xFFFF
        # AND BX, AX
        bx = (bx & ax) & 0xFFFF
    # MOVZX EDX, BX -> return as 32-bit zero-extended
    return bx & 0xFFFF


def to_third(value):
    """Raise value to power 3, limited to 32-bit (truncated).
    The Power proc in solution 3 uses IMUL which truncates to 32 bits.
    """
    # 32-bit truncation at each step
    result = 1
    for _ in range(3):
        result = ctypes.c_uint32(result * value).value
    return result


def compute_serial_parts(name):
    """Core serial generation algorithm from solution 2 (keygen2.cpp) and solution 3 (KeyGen_KKR2.asm).
    
    Note: Solutions 2 and 3 differ slightly in the final step.
    Solution 2 uses: val = xor ^ and_val + and_val, then makes even.
    Solution 3 uses a slightly different final formula.
    We follow solution 2 (C++ keygen) as it is clearer.
    """
    n1 = nameToNumber1(name)
    n2 = nameToNumber2(name)

    # Apply transformation: x^3 - x (32-bit truncated)
    n1 = ctypes.c_uint32(to_third(n1) - n1).value
    n2 = ctypes.c_uint32(to_third(n2) - n2).value

    # From solution 2 (C++ keygen):
    val = ctypes.c_uint32((n1 ^ n2) & n2 + n2).value
    # ASSUMPTION: operator precedence in C: & has lower precedence than +
    # so val = (n1 ^ n2) & (n2 + n2) -- but let's follow the C code literally:
    # val = numberFromName ^ numberFromName2; val &= numberFromName2; val += numberFromName2;
    val = ctypes.c_uint32(n1 ^ n2).value
    val = ctypes.c_uint32(val & n2).value
    val = ctypes.c_uint32(val + n2).value

    # Make even
    if val % 2 != 0:
        val = ctypes.c_uint32(val + 1).value

    compare_value = val
    serial1 = ctypes.c_uint32(compare_value // 2).value
    serial2 = serial1

    # Adjust if divisible by 3 (and non-zero)
    if serial1 != 0 and (serial1 % 3) == 0:
        serial1 = ctypes.c_uint32(serial1 + 1).value
        serial2 = ctypes.c_uint32(serial2 - 1).value

    return serial1, serial2


def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters long")
    s1, s2 = compute_serial_parts(name)
    return f"{s1}-{s2}"


def verify(name, serial):
    """Verify a name/serial pair.
    The crackme splits the serial at '-', then compares the two halves
    (as decimal integers) against expected values derived from the name.
    
    ASSUMPTION: The verification compares the numeric values of the two parts
    of the serial against the expected serial1 and serial2 computed from the name.
    The exact comparison logic in the crackme binary was not fully shown in the writeup,
    but based on the keygen logic, we reconstruct it here.
    """
    if len(name) < 4:
        return False
    if '-' not in serial:
        return False
    
    parts = serial.split('-', 1)
    if len(parts) != 2:
        return False
    
    try:
        entered_s1 = int(parts[0])
        entered_s2 = int(parts[1])
    except ValueError:
        return False
    
    expected_s1, expected_s2 = compute_serial_parts(name)
    
    # ASSUMPTION: Direct equality check on both parts
    return entered_s1 == expected_s1 and entered_s2 == expected_s2



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
