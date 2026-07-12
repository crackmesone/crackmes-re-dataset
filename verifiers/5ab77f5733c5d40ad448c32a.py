# crackmev5 by logan - serial validation algorithm
# Reconstructed from TELOPHASE/TEAM ICU writeup
#
# Constraints:
#   - Username must be exactly 5 characters
#   - Serial must be exactly 11 characters
#   - Serial format: XXXXX-XXXXX  (5 chars, dash, 5 chars)
#
# The DLL function ?crap@@YA_NQAD0@Z validates name+serial.
# It calls ?check@@YAHQAD@Z (getHash) in a loop.
#
# From the assembly:
#
# PART 1 (first 5 chars of serial):
#   for i in range(5):
#       count = i  (global counter used by check())
#       hash_val = check(name)   # returns hash depending on global counter
#       ecx = ord(name[i]) - i
#       expected = hash_val + ecx
#       serial[i] must equal expected
#
# PART 2 (serial[5] must be '-')
#
# PART 3 (last 5 chars of serial, serial[6..10]):
#   for i in range(5):
#       count = i  (reset to 0, then incremented)
#       hash_val = check(name)
#       edx = ord(name[i]) - i
#       eax = hash_val + edx - 6
#       serial[i+6] must equal eax
#
# The ?check@@YAHQAD@Z function is described partially in the writeup.
# The writeup shows assembly for getHash but it is truncated.
# From the writeup C++ pseudocode and the assembly we can reconstruct:
#
# The hash function uses 'count' (global) and processes the name string.
# The writeup shows it uses IDIV by 0x0A and the magic number 0x66666667
# which is a division-by-10 trick. The truncated part prevents full recovery.
#
# ASSUMPTION: Based on the visible assembly snippet and common patterns for
# such crackmes, the check() function computes a hash of the name string
# using the current global counter value. The truncated assembly shows
# repeated division by 10 (digit extraction), suggesting the hash
# accumulates digit sums or similar. We reconstruct a plausible version
# based on what is visible:
#
#   The assembly loop does: EDI += EDX (remainder of ECX / 10), then
#   updates ESI with the quotient * something. This looks like it sums
#   the decimal digits of the character value.
#   The counter (count/i) is used as an index into the name for the
#   per-iteration character fetch outside check().
#
# ASSUMPTION: check(name) with global counter=i computes a running hash
# that depends on name[0..i] or just name[i]. Given the assembly shows
# ESI loaded from 't' (the char x), it operates on a single character.
# The visible part: sums decimal digits of (char_value) repeatedly.
# We'll implement a digit-sum hash as the most consistent interpretation.

import ctypes

def _check(name_char_val):
    """
    Reconstructed hash function from partial assembly.
    The assembly shows: load char into ESI, XOR EDI=0, then loop:
      ECX = ESI, EBX = 10, EAX = ECX, CDQ, IDIV EBX => EDX = ECX%10, EAX=ECX//10
      magic multiply by 0x66666667 (fast div by 10 variant)
      EDI += EDX
    This appears to sum the decimal digits of the value.
    ASSUMPTION: loop continues while ESI > 0 (digit sum of char value)
    The writeup is truncated so this is a best-guess reconstruction.
    """
    # ASSUMPTION: hash = sum of decimal digits of the character's ASCII value
    t = name_char_val & 0xFFFFFFFF
    edi = 0
    esi = t
    if esi == 0:
        return 0
    while esi > 0:
        ecx = esi
        edx = ecx % 10
        esi = ecx // 10
        edi += edx
    return edi & 0xFF


def _check_full(name):
    """
    The ?check@@YAHQAD@Z function takes the name string and uses the global
    counter. From assembly at 100010F8:
      PUSH ESI (ESI = name ptr)
      CALL check
    The counter is read inside or outside. Looking more carefully:
    The counter [1000E138] is set before the call, and after the call
    EAX = hash result. The counter is used at 10001107 after the call.
    ASSUMPTION: check() hashes the entire name string into a single value,
    independent of the counter. The counter is only used for indexing
    name[counter] in the outer loop.
    We implement check() as a hash of all name bytes.
    """
    # ASSUMPTION: check() processes all 5 bytes of name
    # and returns some accumulated hash value
    # Most likely it applies the digit-sum hash to each character and accumulates
    result = 0
    for c in name:
        result += _check(ord(c) if isinstance(c, str) else c)
    return result & 0xFF


def _make_serial_char(val):
    """Return the low byte as a character, ensuring printable range if possible."""
    return chr(val & 0xFF)


def keygen(name):
    """
    Generate serial for a 5-character name.
    
    From assembly:
    PART 1: for i in 0..4:
        global_counter = i
        hash_val = check(name)   # EAX after call
        ECX = ord(name[i]) - i   # name[counter] - counter  (10001107-1000110B)
        EDX = hash_val + ECX     # (1000110D)
        serial[i] = EDX & 0xFF
    
    serial[5] = '-'
    
    PART 2: for i in 0..4:
        global_counter = i  (reset)
        hash_val = check(name)
        EDX = ord(name[i]) - i   # (10001143-10001147)
        EAX = hash_val + EDX - 6 # (10001149: LEA EAX,[EAX+EDX-6])
        serial[i+6] = EAX & 0xFF
    
    ASSUMPTION: check() result is the same each call (doesn't depend on counter)
    since counter is only set before the call for the outer loop's use.
    """
    if len(name) != 5:
        raise ValueError("Name must be exactly 5 characters")
    
    serial_chars = [''] * 11
    
    # Part 1: first 5 chars
    for i in range(5):
        # ASSUMPTION: counter=i is set globally before check() call
        # but check() may or may not use it internally
        hash_val = _check_full(name)  # ASSUMPTION: same result each call
        ecx = ord(name[i]) - i
        edx = (hash_val + ecx) & 0xFF
        serial_chars[i] = chr(edx)
    
    # Part 2: dash separator
    serial_chars[5] = '-'
    
    # Part 3: last 5 chars
    for i in range(5):
        hash_val = _check_full(name)  # ASSUMPTION: same result each call
        edx = ord(name[i]) - i
        eax = (hash_val + edx - 6) & 0xFF
        serial_chars[i + 6] = chr(eax)
    
    return ''.join(serial_chars)


def verify(name, serial):
    """
    Verify name/serial pair.
    
    Checks:
    1. len(name) == 5
    2. len(serial) == 11
    3. serial[5] == '-'
    4. First 5 chars of serial match expected (from part 1)
    5. Last 5 chars of serial match expected (from part 3)
    """
    if len(name) != 5:
        return False
    if len(serial) != 11:
        return False
    if serial[5] != '-':
        return False
    
    # Check first 5 chars
    for i in range(5):
        hash_val = _check_full(name)
        ecx = ord(name[i]) - i
        expected = (hash_val + ecx) & 0xFF
        if ord(serial[i]) != expected:
            return False
    
    # Check last 5 chars
    for i in range(5):
        hash_val = _check_full(name)
        edx = ord(name[i]) - i
        expected = (hash_val + edx - 6) & 0xFF
        if ord(serial[i + 6]) != expected:
            return False
    
    return True



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
