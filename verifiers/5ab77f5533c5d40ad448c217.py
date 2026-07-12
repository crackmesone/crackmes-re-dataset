def keygen(name: str) -> int:
    """
    Algorithm (from writeup):
    1. Append 'Sorry, wrong!' to the name -> combined string
    2. Seed hash = 0x15D
    3. For each character in combined string:
       a. Convert to uppercase
       b. hash += ord(char)
       c. hash += 0x381
    4. The serial is the lower 16 bits of the hash (word-sized comparison in 16-bit Pascal)
    
    Note: The assembly does a 32-bit accumulation but compares only a 16-bit word (cwd + compare),
    so we return hash & 0xFFFF as the serial.
    """
    suffix = "Sorry, wrong!"
    combined = name + suffix
    
    if len(combined) < 2:
        raise ValueError("Name too short (combined string must be >= 2 chars)")
    
    # ASSUMPTION: hash is accumulated as a 32-bit value but serial comparison uses only
    # the lower 16 bits (word_20BE), confirmed by 'cwd' + compare in the disassembly.
    hash_val = 0x15D
    
    for ch in combined:
        ch_upper = ch.upper()
        hash_val += ord(ch_upper)  # add ASCII value of uppercased char
        hash_val += 0x381           # add 0x381 per iteration
        # Keep as 32-bit to match Pascal's 32-bit accumulation
        hash_val &= 0xFFFFFFFF
    
    # Serial is the lower 16-bit word
    serial = hash_val & 0xFFFF
    return serial


def verify(name: str, serial) -> bool:
    """
    Verify that the given serial matches the expected serial for name.
    serial can be an int or a string (will be converted to int).
    """
    try:
        serial_int = int(serial)
    except (ValueError, TypeError):
        return False
    
    expected = keygen(name)
    # The program uses 'cwd' (convert word to double) before comparing,
    # meaning the entered serial is sign-extended from 16-bit.
    # The comparison is: cmp dx, word_20C0 / cmp ax, word_20BE
    # word_20C0 (DumbNumber) is always 0, so serial must be non-negative 16-bit value.
    # ASSUMPTION: serial is compared as a plain 16-bit unsigned word.
    serial_word = serial_int & 0xFFFF
    return serial_word == expected



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
