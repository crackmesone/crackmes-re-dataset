# Reconstructed from the writeup for bswap keygenme 0.51
# The writeup describes the validation rules as found by reverse engineering.
#
# Rules (from the writeup):
#   Name:
#     - Must be <= '`' (0x60) in character values (each char)
#     # ASSUMPTION: 'must be =< `' likely means each character's ASCII value <= 0x60
#     # The writeup says length is not important.
#
#   Serial:
#     - Must be >= '@' (0x40) and <= 'o' (0x6F) in character values (each char)
#     - Must be at least 13 characters long
#     - Characters at positions 10, 11, 12, 13 (1-indexed, i.e. indices 9,10,11,12)
#       set bits in EAX which are compared against a value derived from the name.
#
# The actual comparison at 0x401488-0x401497 is:
#   eax = [004030BC]  (derived from serial chars 10-13)
#   ebx = [0040309C]  (derived from name)
#   if (eax - ebx) == 0 => registered
#
# ASSUMPTION: The exact transformation of serial chars 10-13 into EAX and
# name chars into EBX is not described in the writeup. We assume a simple
# sum or XOR of the relevant characters.
#
# From the working example: name='AAAAA' (or 'A'), serial='AAAAAAAAAAAAAAAAAAAAAA'
# 'A' = 0x41. Serial chars at indices 9,10,11,12 are all 'A' (0x41).
# Name chars are all 'A' (0x41).
#
# ASSUMPTION: EBX = sum of name character ASCII values (mod some word size)
# ASSUMPTION: EAX = sum of serial[9], serial[10], serial[11], serial[12] ASCII values
# This would make: name='A' => EBX=0x41, serial indices 9-12='BCDE' => EAX=0x42+0x43+0x44+0x45=0x10E != 0x41
# But the example 'A' / 'BBBBBBBBBCDEF' works, so let's check:
# serial[9]='C'=0x43, serial[10]='D'=0x44, serial[11]='E'=0x45, serial[12]='F'=0x46
# sum=0x43+0x44+0x45+0x46=0x112, name='A'=0x41 -- doesn't match with simple sum.
#
# ASSUMPTION: Perhaps EBX = ord(name[0]) or some single-char operation,
# and EAX = ord(serial[9]) (just using position 10, 1-indexed = index 9).
# name='A'=0x41, serial[9]='C'=0x43 -- still doesn't match.
#
# ASSUMPTION: Given the working examples all use same repeated char for both
# name and serial, the simplest consistent model is:
# EBX = ord(name[0]) (or some function of first char)
# EAX = ord(serial[9]) (char at index 9)
# And the example 'AAAAA'/'AAAAAA...' works because both are 0x41.
# The example 'A'/'BBBBBBBBBCDEF': serial[9]='C'=0x43 != 'A'=0x41
# BUT the writeup claims this works! So maybe there's an offset/transform.
#
# ASSUMPTION: We cannot determine the exact algorithm from the writeup alone.
# We implement a best-effort based on the constraints described and the examples.
# The core check is likely: f(serial[9:13]) == g(name)
# We'll assume EAX = ord(serial[9]) and EBX = ord(name[0]) as the simplest model
# and note this may be wrong for the 'A'/'BBBBBBBBBCDEF' example.

def _name_value(name):
    """Compute EBX from name. ASSUMPTION: sum of ord of all name chars."""
    return sum(ord(c) for c in name) & 0xFFFFFFFF

def _serial_value(serial):
    """Compute EAX from serial chars at positions 10-13 (indices 9-12).
    ASSUMPTION: sum of those four chars."""
    if len(serial) < 13:
        return None
    return sum(ord(serial[i]) for i in range(9, 13)) & 0xFFFFFFFF

def _name_valid(name):
    """Each char in name must be <= '`' (0x60)."""
    if not name:
        return False
    return all(ord(c) <= 0x60 for c in name)

def _serial_chars_valid(serial):
    """Each char in serial must be >= '@' (0x40) and <= 'o' (0x6F)."""
    return all(0x40 <= ord(c) <= 0x6F for c in serial)

def verify(name, serial):
    # Check name constraints
    if not _name_valid(name):
        return False
    # Check serial length
    if len(serial) < 13:
        return False
    # Check serial character range
    if not _serial_chars_valid(serial):
        return False
    # Check the core comparison
    eax = _serial_value(serial)
    ebx = _name_value(name)
    if eax is None:
        return False
    return eax == ebx

def keygen(name):
    """Generate a valid serial for the given name."""
    if not _name_valid(name):
        raise ValueError(f"Name contains invalid characters (must all be <= '`'): {name!r}")
    target = _name_value(name)
    # We need 4 chars in range [0x40, 0x6F] that sum to target.
    # ASSUMPTION: Distribute target across 4 chars.
    # Each char is in range [0x40, 0x6F], so valid range per char: 64..111
    # Max sum of 4 chars = 4*111 = 444, min = 4*64 = 256
    if not (256 <= target <= 444):
        # Fall back: adjust target modulo valid range
        # ASSUMPTION: the algorithm might use modular arithmetic
        # For safety, pick a fixed working prefix and adjust
        # We cannot guarantee correctness here
        raise ValueError(f"Cannot keygen for name {name!r}: target={target} out of range [256,444]")
    # Distribute: use three chars of 0x40 and compute the last
    remaining = target - 3 * 0x40
    if 0x40 <= remaining <= 0x6F:
        key_chars = chr(0x40) * 3 + chr(remaining)
    else:
        # Try to balance
        # Split remaining across chars
        chars = [0x40, 0x40, 0x40, 0x40]
        rem = target - sum(chars)
        for i in range(4):
            add = min(rem, 0x6F - chars[i])
            chars[i] += add
            rem -= add
            if rem == 0:
                break
        if rem != 0:
            raise ValueError(f"Cannot generate serial for name {name!r}")
        key_chars = ''.join(chr(c) for c in chars)
    # Build serial: 9 padding chars + 4 key chars
    # Padding chars must be in [@, o] range
    padding = '@' * 9
    serial = padding + key_chars
    return serial


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
