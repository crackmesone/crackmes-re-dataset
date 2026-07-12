# Reverse-engineered keygen/verifier for benladan's first_iranian_obfuscator_crackme
# Based on the writeup by gyver75. The crackme uses a multi-step hash of the username
# to derive a serial. The writeup describes three hashing routines applied in sequence,
# but the full arithmetic details of each step are only partially described in the
# truncated PDF text. The structure below is based on what was recoverable.

# ASSUMPTION: The crackme hashes the username through 3 hash routines (described as
# 'first hashing routine', 'second hashing routine', 'third hashing routine') and
# then applies a crypto routine to produce the serial string.
# ASSUMPTION: Since the full arithmetic of each hash step is not given in the truncated
# writeup, the sub-steps below are placeholders that represent the described structure.

def _hash_init(name: str) -> list:
    """Initialize hashing state from the name string."""
    # ASSUMPTION: The init routine converts the name characters to their ordinal values
    # and builds an array (or accumulator) used in subsequent routines.
    result = [ord(c) for c in name]
    return result

def _hash_routine1(state: list) -> int:
    """First hashing routine as described in section 1.7.2."""
    # ASSUMPTION: Iterates over name bytes, accumulating via addition/XOR/rotation.
    acc = 0
    for i, v in enumerate(state):
        acc = ((acc << 5) | (acc >> 27)) & 0xFFFFFFFF  # rotate left 5
        acc = (acc ^ v) & 0xFFFFFFFF
        acc = (acc + (i * 0x11)) & 0xFFFFFFFF
    return acc

def _hash_routine2(state: list, h1: int) -> int:
    """Second hashing routine as described in section 1.7.3."""
    # ASSUMPTION: Uses h1 as seed, processes name bytes differently (multiply/XOR).
    acc = h1
    for i, v in enumerate(state):
        acc = (acc * 0x1505 + v) & 0xFFFFFFFF  # djb2-like
        acc = acc ^ (v << (i % 8))
        acc = acc & 0xFFFFFFFF
    return acc

def _hash_routine3(state: list, h2: int) -> int:
    """Third hashing routine as described in section 1.7.4."""
    # ASSUMPTION: A finalizing mix using h2.
    acc = h2
    for i, v in enumerate(state):
        acc = (acc + v * (i + 1)) & 0xFFFFFFFF
        acc = ((acc >> 13) | (acc << 19)) & 0xFFFFFFFF  # rotate right 13
        acc = acc ^ 0xDEADBEEF
        acc = acc & 0xFFFFFFFF
    return acc

def _crypto_routine(h3: int) -> str:
    """Crypto/formatting routine described in section 1.8.
    Converts the final hash to a serial string."""
    # ASSUMPTION: The serial is the uppercase hex of the final 32-bit hash,
    # possibly formatted in groups. The writeup mentions a 'crypto routine' but
    # does not give the exact output format.
    # We format as XXXX-XXXX (two 16-bit groups) as a common Delphi crackme pattern.
    hi = (h3 >> 16) & 0xFFFF
    lo = h3 & 0xFFFF
    return f"{hi:04X}-{lo:04X}"

def keygen(name: str) -> str:
    """Generate a serial for the given name."""
    if not name:
        return ""
    state = _hash_init(name)
    h1 = _hash_routine1(state)
    h2 = _hash_routine2(state, h1)
    h3 = _hash_routine3(state, h2)
    return _crypto_routine(h3)

def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    expected = keygen(name)
    return serial.upper() == expected.upper()


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
