import struct

KEYCHARS = "Q1WE2RT3ZU4IO5PA6SD7FG8HJ9KL0YXCVBNMQ1WE2RT3ZU4IO5PA6SD7FG8HJ9KL0YXCVBNM"

def _get_key_offset(seed):
    """Modifies seed and returns offset 0-35. seed is treated as unsigned 32-bit."""
    seed = seed & 0xFFFFFFFF
    if seed & 0x80000000:
        seed = (seed + 0x7FFFFFFF) & 0xFFFFFFFF
    div1 = seed // 0x1F31D
    rem1 = seed % 0x1F31D
    mul1 = (div1 * 0x0B14) & 0xFFFFFFFF
    new_seed = ((rem1 * 0x41A7) - mul1) & 0xFFFFFFFF
    offset = new_seed % 0x24
    return new_seed, offset


def _calculate_key(username):
    """Compute the internal 24-char key string (with hyphens) from username."""
    if not username:
        return ""
    n = len(username)
    seed = 0
    for i, c in enumerate(username):
        seed += ord(c) * (n - i)
    seed = seed & 0xFFFFFFFF

    key_chars = []
    for _ in range(24):
        seed, offset = _get_key_offset(seed)
        key_chars.append(KEYCHARS[offset])

    # Place hyphens
    key_chars[4] = '-'
    key_chars[9] = '-'
    key_chars[14] = '-'
    key_chars[19] = '-'
    return ''.join(key_chars)


def _reverse_key(name_key):
    """Transform the internal key into the final serial that the crackme accepts."""
    if not name_key:
        return ""

    # Strip hyphens
    key = [c for c in name_key if c != '-']
    if len(key) != 20:
        return ""

    # Shift each character left 18 positions in KEYCHARS (rfind then -18)
    new_key = []
    for c in key:
        pos = KEYCHARS.rfind(c)
        if pos == -1 or pos < 18:
            return ""  # invalid character
        new_key.append(KEYCHARS[pos - 18])
    key = new_key

    # Groups of 4
    g1 = key[0:4]
    g2 = key[4:8]
    g3 = key[8:12]
    g4 = key[12:16]
    g5 = key[16:20]

    # Reorganize: group3 + group4 + group1 + group5 + group2
    key = g3 + g4 + g1 + g5 + g2

    # Insert hyphens every 4 chars (positions 4,9,14,19 in 24-char string)
    result = []
    char_count = 0
    for i, c in enumerate(key):
        result.append(c)
        char_count += 1
        if char_count == 4 and i < len(key) - 1:
            result.append('-')
            char_count = 0

    return ''.join(result)


def keygen(name):
    """Generate the valid serial for the given name."""
    name_key = _calculate_key(name)
    serial = _reverse_key(name_key)
    return serial


def verify(name, serial):
    """Verify that serial is valid for the given name."""
    expected = keygen(name)
    if not expected:
        return False
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
