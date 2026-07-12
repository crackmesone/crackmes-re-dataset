import ctypes

# Constants from the crackme
BASE_ADDR = 0x0043F200
CONSTANT = 0x4D6


def do_username(name: str):
    """
    Compute the name checksum and the serial base address.
    Returns (GOAL, uAddr) as Python ints (unsigned 32-bit).
    """
    # Sum all character values mod 256
    val = 0
    for ch in name:
        val = (val + ord(ch)) & 0xFF

    # GOAL: the address we must reach
    goal = (BASE_ADDR + val) & 0xFFFFFFFF

    # uAddr: starting point for serial hash
    # From the assembly:
    #   ecx = goal  (nameCheckSum)
    #   eax = goal ^ 0x43F200  (XOR with base)
    #   eax = goal + (goal ^ 0x43F200)  (ADD)
    #   i.e. uAddr = goal + (goal XOR 0x43F200) + 0x10  ???
    # From Solution 1 (TCM): uAddr = addrOne + (addrOne ^ 0x43F200) + 0x10
    # From Solution 2 (keygen.cpp): i5 = nameCheckSum + i1 + 0x10
    #   where i1 is the raw byte sum (val)
    # The assembly at 0x401503-0x401509:
    #   ebx = eax ^ 0x43F200  (where eax = goal = BASE + val)
    #   eax = eax + ebx  = goal + (goal ^ 0x43F200)
    # That is the value used as starting point for serial (no +0x10 seen in asm,
    # but +0x10 appears in TCM's writeup). We follow the assembly directly.
    # ASSUMPTION: uAddr = goal + (goal XOR 0x43F200), matching the assembly lines
    # 0x401503-0x401509. The +0x10 in TCM's code may account for something else.
    xored = goal ^ 0x43F200
    u_addr = (goal + xored) & 0xFFFFFFFF
    return goal, u_addr


def do_serial(serial: str, u_addr: int) -> int:
    """
    Compute the serial hash starting from u_addr.
    Returns the result as an unsigned 32-bit integer.
    """
    # Use ctypes to simulate 32-bit unsigned arithmetic
    addr = u_addr

    n = len(serial)

    # Round 1: add all character values
    for i in range(n):
        addr = (addr + ord(serial[i])) & 0xFFFFFFFF

    # Round 2: subtract characters at even indices (0,2,4,...) going from n-2 downward
    # From TCM: count = strlen(serial)-2; count >= 0; count -= 2  => indices n-2, n-4, ..., 0
    # From asm solution2 keygen: subtracts chars at positions i*2 (0,2,4,...)
    # Both agree: subtract characters at even positions (0-indexed: 0,2,4,...)
    i = n - 2
    while i >= 0:
        addr = (addr - ord(serial[i])) & 0xFFFFFFFF
        i -= 2

    # Round 3: subtract (char << 4) for every 4th character (indices 0,4,8,...)
    i = 0
    while i < n:
        c = ord(serial[i]) & 0xFF
        addr = (addr - (c << 4)) & 0xFFFFFFFF
        i += 4

    # Add the constant
    addr = (addr + CONSTANT) & 0xFFFFFFFF
    return addr


def verify(name: str, serial: str) -> bool:
    """Return True if the serial is valid for the given name."""
    goal, u_addr = do_username(name)
    result = do_serial(serial, u_addr)
    return result == goal


def _char_for_diff(diff: int) -> str:
    """
    Given a positive diff value, pick a printable ASCII character.
    Clamp to printable range.
    """
    if diff <= 0:
        return '0'
    if diff >= 0x7A:  # 'z'
        return 'z'
    if diff >= 0x61:  # 'a'
        return chr(diff)
    if diff >= 0x5A:  # 'Z'
        return 'Z'
    if diff >= 0x41:  # 'A'
        return chr(diff)
    if diff >= 0x39:  # '9'
        return '9'
    if diff >= 0x30:  # '0'
        return chr(diff)
    return chr(max(0x20, diff))


def keygen(name: str) -> str:
    """
    Generate a valid 8-character serial for the given name.

    Strategy (following TCM's approach):
    - Start with '00000000'
    - Positions that LOWER the hash (subtract in rounds 2&3): odd indices = 1,3,5,7
      and even indices reduce more due to round3. Actually:
      Even positions (0,2,4,6) are subtracted in round2; positions 0,4 also subtract <<4 in round3.
      Odd positions (1,3,5,7) only ADD in round1, never subtracted -> raising the hash value.
      Even positions: add in round1, subtract in round2 (net=0 for those) and 0,4 subtract <<4.
    - We need serial_hash == goal. Adjust characters to close the gap.

    We use a simple iterative approach: compute diff, assign characters one by one.
    """
    goal, u_addr = do_username(name)

    # Start with all '0'
    serial = ['0'] * 8

    # Effect of each position on the serial hash for an 8-char serial:
    # pos 0: +ord - ord - (ord<<4) = ord*(1-1-16) = -16*ord  [rounds 1,2,3]
    # pos 1: +ord                  = +ord           [round 1 only, odd]
    # pos 2: +ord - ord            = 0              [rounds 1,2]
    # pos 3: +ord                  = +ord           [round 1 only, odd] -- WAIT
    # Let me re-check round2: indices n-2, n-4, ..., 0 for n=8: 6,4,2,0
    # So subtracted positions: 0,2,4,6 (even positions)
    # Round3 subtracts positions 0,4
    # Net effect per position (for 8-char serial):
    #   pos 0: +1 -1 -16 = -16  (multiply by ord)
    #   pos 1: +1        = +1
    #   pos 2: +1 -1     =  0
    #   pos 3: +1        = +1
    #   pos 4: +1 -1 -16 = -16
    #   pos 5: +1        = +1
    #   pos 6: +1 -1     =  0
    #   pos 7: +1        = +1
    # So only positions 1,3,5,7 (odd) effectively raise the hash.
    # Positions 0,4 lower it by 16x.
    # Positions 2,6 have zero net effect.
    # We adjust pos 1,3,5,7 upward (raise hash) or pos 0,4 to lower hash.

    for iteration in range(100):
        current = do_serial(''.join(serial), u_addr)
        diff = (goal - current) & 0xFFFFFFFF  # unsigned
        # Interpret as signed 32-bit
        if diff >= 0x80000000:
            diff_signed = diff - 0x100000000
        else:
            diff_signed = diff

        if diff_signed == 0:
            break

        if diff_signed > 0:
            # Need to raise the hash -> use odd positions
            # Odd positions raise by their ord value
            # Pick position to adjust
            for pos in [1, 3, 5, 7]:
                c_val = ord(serial[pos])
                if diff_signed <= 0:
                    break
                # Max we can add with this position
                max_add = 0x7E - c_val  # max printable char
                add = min(diff_signed, max_add)
                if add > 0:
                    serial[pos] = chr(c_val + add)
                    diff_signed -= add
        else:
            # Need to lower the hash -> use positions 0 or 4 (effect = -16 per ascii unit)
            # Or we can raise positions that lower (0,4)
            neg_diff = -diff_signed
            for pos in [0, 4]:
                c_val = ord(serial[pos])
                if neg_diff <= 0:
                    break
                # Increasing this char by 1 lowers hash by 16
                units = (neg_diff + 15) // 16
                max_units = 0x7E - c_val
                units = min(units, max_units)
                if units > 0:
                    serial[pos] = chr(c_val + units)
                    neg_diff -= units * 16

    serial_str = ''.join(serial)
    # Verify and return
    if verify(name, serial_str):
        return serial_str

    # Fallback: brute-force small adjustment on odd positions
    # ASSUMPTION: if iterative adjustment fails, try exhaustive search on pos 1
    for c1 in range(0x20, 0x7F):
        serial[1] = chr(c1)
        for c3 in range(0x20, 0x7F):
            serial[3] = chr(c3)
            if verify(name, ''.join(serial)):
                return ''.join(serial)

    return serial_str  # best effort



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
