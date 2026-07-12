import ctypes

def _imul32(a, b):
    """Simulate 32-bit signed IMUL (truncates to 32-bit signed result)."""
    result = a * b
    # Truncate to 32 bits
    result = result & 0xFFFFFFFF
    # Convert to signed 32-bit
    if result >= 0x80000000:
        result -= 0x100000000
    return result

def _sar32(value, shift):
    """Arithmetic shift right on 32-bit signed integer."""
    # Ensure value is treated as 32-bit signed
    value = value & 0xFFFFFFFF
    if value >= 0x80000000:
        value -= 0x100000000
    return value >> shift

def _shr32(value, shift):
    """Logical shift right on 32-bit unsigned integer."""
    value = value & 0xFFFFFFFF
    return value >> shift

def compute_serial(username_len, computername_len):
    """
    Compute the valid serial given username length and computer name length.
    All arithmetic is 32-bit signed (as in x86 IMUL).
    """
    # Part 1: [404128] = len(username) + 0x64
    v128 = username_len + 0x64  # Add 100

    # Part 2: [40412C] = len(computername) + 0xC8
    v12C = computername_len + 0xC8  # Add 200

    # Part 3: [404130] = v12C * v128
    v130 = _imul32(v12C, v128)

    # Part 4: [404134] = v128 * v12C + v130 = 2 * v130
    v134 = _imul32(v128, v12C)
    v134_val = v134 & 0xFFFFFFFF
    v130_val = v130 & 0xFFFFFFFF
    v134_sum = (v134_val + v130_val) & 0xFFFFFFFF
    if v134_sum >= 0x80000000:
        v134_sum -= 0x100000000
    v134 = v134_sum

    # Part 5: [404138] = v134 - v128
    v138 = (v134 - v128) & 0xFFFFFFFF
    if v138 >= 0x80000000:
        v138 -= 0x100000000

    # Part 6: [40413C] = v134 + v138 - v130 + v128 - v12C
    v13C = v134 + v138 - v130 + v128 - v12C
    v13C = v13C & 0xFFFFFFFF
    if v13C >= 0x80000000:
        v13C -= 0x100000000

    # Part 7: [404140] = v13C / 2 (arithmetic)
    # SAR EAX, 1F -> if positive, EAX=0; SHR EAX, 1F -> EAX=0 (for non-negative)
    # LEA EAX, [EDX+EAX] -> EAX = v13C + adjustment
    # SAR EAX, 1 -> divide by 2 arithmetic
    # For positive numbers this is simply v13C // 2
    # The SAR 1F / SHR 1F trick: for signed 32-bit x, result is (x + (x >> 31 & 1)) >> 1
    # which handles rounding for negative odd numbers. For our examples it's just integer division.
    edx = v13C
    eax = _sar32(edx, 0x1F)  # sign extend -> 0 if positive, -1 if negative
    eax_u = _shr32(eax, 0x1F)  # logical shift right -> 0 if was 0, 1 if was -1 (0xFFFFFFFF)
    eax_sum = (edx + eax_u) & 0xFFFFFFFF
    if eax_sum >= 0x80000000:
        eax_sum -= 0x100000000
    v140 = _sar32(eax_sum, 1)

    # Part 8: [404154]
    # EAX = v13C
    # EAX *= v140
    # EAX *= v13C
    # EAX *= v138
    # EAX *= v134
    # EAX *= v130
    # EAX *= v12C
    # EDX = EAX * v128
    # then divide by 2 (same trick)
    eax = v13C
    eax = _imul32(eax, v140)
    eax = _imul32(eax, v13C)
    eax = _imul32(eax, v138)
    eax = _imul32(eax, v134)
    eax = _imul32(eax, v130)
    eax = _imul32(eax, v12C)
    edx = _imul32(eax, v128)

    # Same divide-by-2 trick
    eax2 = _sar32(edx, 0x1F)
    eax2_u = _shr32(eax2, 0x1F)
    eax2_sum = (edx + eax2_u) & 0xFFFFFFFF
    if eax2_sum >= 0x80000000:
        eax2_sum -= 0x100000000
    v154 = _sar32(eax2_sum, 1)

    # Part 9: [404124] (final serial)
    # EAX = v154 * v140 * v134 * v13C * 0x1BB
    eax = v154
    eax = _imul32(eax, v140)
    eax = _imul32(eax, v134)
    eax = _imul32(eax, v13C)
    eax = _imul32(eax, 0x1BB)  # 0x1BB = 443

    serial = eax
    return serial

def verify(name, serial):
    """
    Verify a serial for a given username.
    NOTE: The crackme uses both username AND computer name.
    This verify function only takes 'name' as the username.
    ASSUMPTION: We cannot know the computer name at verify time without it being provided.
    This function will return True only if the serial matches for the given username_len
    and some computer name length.
    """
    # ASSUMPTION: We don't have the computer name, so we try to match
    # by computing expected serial with username length only.
    # The keygen needs both username and computer name.
    username_len = len(name)
    # Try common computer name lengths (1-15)
    for comp_len in range(1, 64):
        expected = compute_serial(username_len, comp_len)
        if expected == serial:
            return True
    return False

def keygen(name, computername=None):
    """
    Generate a valid serial given a username (and optionally a computer name).
    The crackme reads the actual Windows username and computer name.
    ASSUMPTION: If computername is not provided, we default to len 7 (as in the example).
    """
    username_len = len(name)
    if computername is None:
        # ASSUMPTION: default computer name length of 7 (from the writeup example)
        comp_len = 7
    else:
        comp_len = len(computername)
    return compute_serial(username_len, comp_len)


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
