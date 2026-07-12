import hashlib

# Based on the writeup by synak for DarioX CrackMe v1.5
# The algorithm:
# 1. Take the first 9 characters of the entered serial
# 2. Concatenate the name to get a 'base string' of length (9 + len(name))
# 3. Compute what appears to be an MD5 hash of that base string (the writeup shows a 32-char hex string)
# 4. For each character position beyond the first 9 in the final serial:
#    a. Take 5 hex chars from the hash starting at an offset
#    b. Prepend '&H' and convert to integer (int('0x' + chunk, 16))
#    c. Divide by 0x28 (40) and take the REMAINDER
#    d. Use remainder+1 as 1-based index into the hardcoded lookup string
#    e. Pick that character as the next serial character
# 5. The final serial = first_9_chars + computed_chars
#
# The hardcoded lookup string observed in the writeup:
HARDCODED = "aAbBcCeEfFGgHhlLpPaAbBcCeEfFGgHhlLpPzZxX"

# ASSUMPTION: The hash used is MD5 (the 32-char lowercase hex string seen in SmartCheck matches MD5 output length)
# ASSUMPTION: The 5-char hex window moves forward by 5 each iteration (stepping through the hash)
# ASSUMPTION: The number of characters to generate after the first 9 depends on a fixed total serial length
# ASSUMPTION: Total serial length observed is 24 chars (aaaaabbbbeHaPBalCClfcchgA = 24), so 15 chars generated
# ASSUMPTION: The first 9 chars used are arbitrary (can be any 9 chars, keygen uses 'aaaaabbbb')
# ASSUMPTION: The 5-char chunks are taken at offsets 0,5,10,15,20,25 (cycling or stopping at hash end)

def _compute_hash(base_string):
    # ASSUMPTION: MD5 hash of the base string, lowercased hex
    return hashlib.md5(base_string.encode('latin-1')).hexdigest()

def _generate_serial_chars(hash_str, num_chars):
    result = []
    for i in range(num_chars):
        offset = i * 5
        # If we run out of hash characters, wrap around
        # ASSUMPTION: wrapping with modulo
        hash_len = len(hash_str)
        chunk = ''
        for j in range(5):
            chunk += hash_str[(offset + j) % hash_len]
        # Convert chunk as hex integer
        val = int(chunk, 16)
        # Divide by 0x28, take remainder
        remainder = val % 0x28
        # Use remainder as 0-based index into hardcoded string (writeup shows 0x18=24 decimal -> 25th char = index 24)
        idx = remainder  # 0-based index
        char = HARDCODED[idx % len(HARDCODED)]
        result.append(char)
    return ''.join(result)

def keygen(name, prefix='aaaaabbbb'):
    """Generate a valid serial for the given name.
    The serial = first 9 chars (prefix) + computed chars.
    The base string for hashing = prefix + name.
    Total serial length appears to be 24 chars = 9 prefix + 15 computed.
    """
    # ASSUMPTION: prefix can be any 9 chars; the keygen just uses 'aaaaabbbb'
    if len(prefix) != 9:
        prefix = (prefix + 'a' * 9)[:9]
    base_string = prefix + name
    hash_str = _compute_hash(base_string)
    # ASSUMPTION: 15 characters are generated after the 9-char prefix (total=24)
    generated = _generate_serial_chars(hash_str, 15)
    serial = prefix + generated
    return serial

def verify(name, serial):
    """Verify a name/serial pair.
    Reconstructs the expected serial from the first 9 chars of the entered serial + name,
    then compares.
    """
    if len(serial) < 9:
        return False
    # Strip spaces if entered with spaces
    serial_clean = serial.replace(' ', '')
    if len(serial_clean) < 9:
        return False
    prefix = serial_clean[:9]
    base_string = prefix + name
    hash_str = _compute_hash(base_string)
    num_generated = len(serial_clean) - 9
    if num_generated <= 0:
        # ASSUMPTION: if serial is exactly 9 chars, nothing to check beyond prefix (unlikely to be valid)
        return False
    generated = _generate_serial_chars(hash_str, num_generated)
    expected = prefix + generated
    return serial_clean == expected


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
