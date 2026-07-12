import ctypes

def _compute_serial_value(name: str) -> int:
    """
    Compute the numeric part of the serial.
    
    The C keygen does:
        sum = sum of all char values in name
        sum += 0x3A2F49   (== 3813193)
        sum <<= (name[0] & 0xff)   # left shift by first char value
        sum ^= 0x1337             # XOR with 4919
    
    The C code uses unsigned long arithmetic (32-bit on x86 Linux).
    The Python solution (Drew) uses: (number + 3813193 << (firstInt & 31) ^ 4919)
    which due to Python operator precedence is:
        ((number + 3813193) << (firstInt & 31)) ^ 4919
    but only masks shift by 31 (not full byte).
    
    The C keygen.c from niel does:
        sum += 0x3a2f49;
        sum <<= (c[1][0] & 0xff);  // shift by full first char value
        sum ^= 0x1337;
    and prints with %lu (unsigned long, 32-bit on x86).
    
    We follow the C keygen exactly, using 32-bit unsigned arithmetic.
    """
    char_vals = [ord(c) for c in name]
    # sum of all character values
    s = sum(char_vals)
    # add 0x3A2F49
    s = (s + 0x3A2F49) & 0xFFFFFFFF
    # left shift by first character value (full byte), masked to 32 bits
    shift = char_vals[0] & 0xFF
    s = (s << shift) & 0xFFFFFFFF
    # XOR with 0x1337
    s = s ^ 0x1337
    return s


def keygen(name: str) -> str:
    """
    Generate the valid serial for a given name.
    Format: ~1337#<number>#~
    where <number> is the computed unsigned long value.
    """
    if not name:
        raise ValueError('Name must not be empty')
    val = _compute_serial_value(name)
    return '~1337#{}#~'.format(val)


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    The crackme computes the expected c0de string and does strcmp against user input.
    """
    if not name:
        return False
    expected = keygen(name)
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
