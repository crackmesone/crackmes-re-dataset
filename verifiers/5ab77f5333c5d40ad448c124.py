# Reconstruction of crackme2 by spoke3fff
# Based on the keygen C++ source and disassembly hints from the tutorial
# The tutorial (encoded in a non-standard encoding) describes the algorithm in detail
# but is partially garbled. The C++ keygen snippet is also truncated.
# We reconstruct from the known valid pair: name='Whivel', serial='623-80BDF84373A06'
# and from the structural hints in the disassembly commentary.

# From the tutorial/disassembly commentary we can extract the following algorithm:
# 1. Take the name string.
# 2. Compute a sum of ASCII values of all name characters (routine around 0x00401CA8)
#    - for each char c in name: if c != 0x25 ('%'), multiply accumulated value by 0x3FFF,
#      result added to esi; esi is initialized to name_length
#    - ascii value compared with 0x25; if equal jump away
#    - otherwise: eax = ascii(char), XOR with value at some address (0x00403FF0 -> 0x00770077?)
#      add to esi; shift esi right 7, increment esi
#    This produces an intermediate 'n' (first part of serial)
#
# 3. The first part of serial is 'n' formatted as decimal with a '-' appended.
#
# 4. The second part: iterate over name chars, for each char c:
#    - take FFTTSSRR chars (4th, 3rd, 2nd, 1st of a rolling window?)
#    - XOR with 0x00777777
#    - add to ebx (initialized from second keygen routine result)
#    - XOR ebx with value at 0x00404E57 (0x00077777)
#    - add to esi
#    - SHR esi, 7; INC esi
#    - then XOR with 0x0000BAFE
#    - add to ebx; DEC edx; loop
#    Format ebx as hex string (uppercase), join with first part.
#
# ASSUMPTION: The exact constants and operations are not fully recoverable from
# the garbled tutorial. We verify against the known pair and implement a best-effort.

def _compute_serial_part1(name):
    """Compute first part (decimal number before '-')"""
    # ASSUMPTION: sum of ascii values of name chars with some transform
    # From disassembly: esi initialized to name_length
    # each char: if char != '%' (0x25): esi = esi * 0x3FFF ... but this seems large
    # Let's try simpler: sum of ord(c) then some modular arithmetic
    # Verified against: name='Whivel' -> part1 should be '623'
    n = len(name)
    esi = n
    for c in name:
        val = ord(c)
        if val != 0x25:
            # ASSUMPTION: based on disassembly hints
            # multiply by 0x3FFF and add ascii, then shift
            esi = esi + val
    # That gives 87+104+105+118+101+108 = 623, plus initial 0 (if esi starts at 0)
    # Let's check: W=87,h=104,i=105,v=118,e=101,l=108 -> sum=623
    # So part1 = sum of ASCII values of name chars (esi starts at 0, not n)
    esi2 = sum(ord(c) for c in name)
    return esi2

def _compute_serial_part2(name):
    """Compute second part (hex string after '-')"""
    # From tutorial: second part = '80BDF84373A06' for 'Whivel'
    # ASSUMPTION: The algorithm processes name chars building a value
    # From disassembly hints:
    # - eax = FFTTSSRR pattern (ascii of chars at positions)
    # - XOR with 0x00777777
    # - various add/xor operations with constants 0x00077777, 0x0000BAFE
    # - result formatted as hex
    # We implement a best-effort reconstruction:
    
    n = len(name)
    # Initialize ebx from second routine (lstrlen result + 1 stored in edx)
    # edx = n (from lstrcat usage, edx stored string length+1)
    edx = n  # ASSUMPTION
    ebx = 0  # initialized by second keygen routine result (ASSUMPTION: 0 start)
    
    # Process chars
    esi = n  # from lstrcat: esi = length to join + 1 -> ASSUMPTION
    
    for i in range(n):
        c = name[i]
        val = ord(c)
        # Pack FFTTSSRR: take 4 consecutive chars (with wrapping)
        # ASSUMPTION: simplified to single char processing
        # XOR with 0x00777777
        xval = val ^ (0x00777777 & 0xFF)  # ASSUMPTION: only low byte relevant
        ebx = (ebx + xval) & 0xFFFFFFFF
        # XOR ebx with 0x00077777
        ebx = ebx ^ (0x00077777 & 0xFFFF)  # ASSUMPTION
        esi = (esi + ebx) & 0xFFFFFFFF
        # SHR esi, 7
        esi = (esi >> 7) & 0xFFFFFFFF
        esi += 1
        # XOR with 0x0000BAFE
        ebx = (ebx ^ 0x0000BAFE) & 0xFFFFFFFF
        ebx = (ebx + esi) & 0xFFFFFFFF
        edx -= 1
    
    return format(ebx, 'X').upper()

def keygen(name):
    """
    Generate serial for given name.
    Known valid: keygen('Whivel') should return '623-80BDF84373A06'
    ASSUMPTION: The exact algorithm constants are partially guessed.
    The part1 (decimal sum of ASCII) is confirmed correct for 'Whivel'.
    Part2 hex is reconstructed with assumptions.
    """
    part1 = _compute_serial_part1(name)
    part2 = _compute_serial_part2(name)
    return f"{part1}-{part2}"

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: We compare against keygen output.
    The real crackme may have additional checks not fully recovered.
    """
    if not name or len(name) < 5:
        return False
    expected = keygen(name)
    return serial == expected

# Test against known valid pair

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
