# Crackme.02.32 by geyslan
# Algorithm recovered from solution writeups:
# 1. The password transformation: each input char is OR'd with 0x90
# 2. The result is compared byte-by-byte with the hardcoded array:
#    cypher = [0xf7, 0xf8, 0xf1, 0xf4, 0xf1, 0xf8, 0xb3, 0xfc, 0xfc]
# 3. Password must be exactly 9 characters long
# 4. For verify: transform each char of input with OR 0x90, compare with cypher
# 5. For keygen: find all chars c such that (c | 0x90) == cypher[i], prefer ascii range

cypher = [0xf7, 0xf8, 0xf1, 0xf4, 0xf1, 0xf8, 0xb3, 0xfc, 0xfc]
KEY = 0x90  # 0b10010000
# The four possible OR combinations with 0x90:
# comb[0] = 0b10010000 = 0x90
# comb[1] = 0b00010000 = 0x10
# comb[2] = 0b00000000 = 0x00
# comb[3] = 0b10000000 = 0x80
COMB = [0b10010000, 0b00010000, 0b00000000, 0b10000000]


def transform(password: str) -> list:
    """Apply the OR 0x90 transformation to each character of the password."""
    return [(ord(c) | KEY) & 0xFF for c in password]


def verify(name: str, serial: str) -> bool:
    """Verify that a serial (password) is correct.
    
    The crackme does NOT use the name; only the password matters.
    The password must be exactly 9 chars, and each char OR'd with 0x90
    must match the corresponding byte in the hardcoded cypher array.
    """
    # ASSUMPTION: 'name' is not used in the check - only 'serial' (the password) matters
    if len(serial) != len(cypher):
        return False
    transformed = transform(serial)
    return transformed == cypher


def _get_candidates_for_index(idx: int):
    """Return all ASCII-safe chars that, when OR'd with 0x90, equal cypher[idx]."""
    target = cypher[idx]
    candidates = []
    for combval in COMB:
        # candidate = (target & ~KEY) | combval
        candidate = (target & (~KEY & 0xFF)) | combval
        # verify it produces the target
        if (candidate | KEY) & 0xFF == target:
            # only include ascii-safe chars (0..127)
            if 0 <= candidate <= 127:
                candidates.append(chr(candidate))
    return candidates


def keygen(name: str) -> str:
    """Generate the first valid serial (password) for the given name.
    
    Returns a 9-character password string.
    ASSUMPTION: name is not used; any valid 9-char password works.
    """
    result = []
    for i in range(len(cypher)):
        candidates = _get_candidates_for_index(i)
        if not candidates:
            # ASSUMPTION: if no ascii-safe candidate, fall back to raw (target & ~KEY) | KEY
            fallback = (cypher[i] & (~KEY & 0xFF)) | KEY
            result.append(chr(fallback))
        else:
            result.append(candidates[0])
    return ''.join(result)


def keygen_all(name: str):
    """Generate ALL valid serials (passwords) using only ascii-safe chars."""
    import itertools
    candidate_lists = [_get_candidates_for_index(i) for i in range(len(cypher))]
    # filter out positions with no candidates
    valid_lists = [lst if lst else ['?'] for lst in candidate_lists]
    for combo in itertools.product(*valid_lists):
        yield ''.join(combo)



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
