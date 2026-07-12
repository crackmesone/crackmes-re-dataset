# Reverse-engineered algorithm for KeyWizard 1 by disasmdisease
# Based on ILDasm writeup by MCxCodex
#
# Key observations from the writeup:
# 1. Name must be >= 6 characters long
# 2. nstr = name, wstr = name
# 3. var0 starts at 65 (0x41 = 'A')
# 4. A loop processes the name string, building the serial
#    - Chr(var0) and Chr(var0 - 19) are used (suggesting Caesar-like ops)
#    - var0 -= 19 (0x13) subtraction is used
# 5. The writeup was truncated before showing the full loop/serial construction
#
# ASSUMPTION: The algorithm iterates over each character of the name,
# performs arithmetic on character ordinal values, and concatenates results
# to form the serial. The exact loop body and serial format are not fully shown.
#
# From the partial IL we can see:
#   wstr = name
#   var0 = 65
#   Then: Chr(var0) and Chr(var0 - 19) are computed
#   The subtraction suggests: Chr(65) = 'A', Chr(65-19) = Chr(46) = '.'
#
# ASSUMPTION: Based on common .NET crackme patterns and the visible IL,
# the serial is likely constructed by processing each character of the name
# with some arithmetic transformation. The loop likely:
#   - takes each char ordinal from the name
#   - applies some operation involving 65 and/or 19
#   - builds a serial string
#
# Since the writeup is truncated, we implement what we know for certain
# and mark assumptions clearly.

def _vb_chr(n):
    """VB Strings.Chr equivalent"""
    return chr(n & 0xFFFF)

def verify(name, serial):
    """Check if serial is valid for name."""
    if len(name) < 6:
        return False
    expected = keygen(name)
    return serial == expected

def keygen(name):
    """
    Generate serial for name.
    
    ASSUMPTION: The full loop was not shown in the writeup (truncated).
    Based on what IS shown:
    - wstr = name
    - var0 = 65
    - The code uses Chr(var0) and Chr(var0 - 19) for each step
    
    ASSUMPTION: The serial is built by iterating over name characters,
    XORing or adding the char ordinal with some base value derived from
    var0=65, and the subtraction of 19 may relate to a checksum or
    separator/transformation step.
    
    ASSUMPTION: A common pattern for this style of crackme is:
      serial_char = Chr((Ord(name_char) + some_constant) mod 256)
    or the name chars are used to index into a computed alphabet.
    
    Since the writeup is truncated and the exact serial construction
    is not shown, this keygen is a best-effort reconstruction.
    """
    if len(name) < 6:
        return None
    
    nstr = name
    wstr = name
    var0 = 65  # 0x41
    
    # ASSUMPTION: The loop processes each character of wstr (the name)
    # and builds serial parts. The two Chr() calls suggest pairs of chars
    # or a two-part serial token per name character.
    # ASSUMPTION: var0 is updated each iteration based on name char ordinal.
    
    serial_parts = []
    for ch in wstr:
        ch_ord = ord(ch)
        # ASSUMPTION: The serial segment is computed as:
        # part1 = Chr(ch_ord + var0 - some_base) or similar
        # The only confirmed operation is: Chr(var0) and Chr(var0 - 19)
        # and var0 starts at 65
        
        # ASSUMPTION: var0 is updated by the character ordinal each iteration
        var0 = (var0 + ch_ord) % 256
        if var0 < 32:
            var0 += 32  # keep printable
        
        part1 = _vb_chr(var0)
        part2 = _vb_chr(var0 - 19) if var0 - 19 >= 32 else _vb_chr(var0 + 19)
        serial_parts.append(part1 + part2)
    
    # ASSUMPTION: parts are joined, possibly with a separator like '-'
    serial = '-'.join(serial_parts)
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
