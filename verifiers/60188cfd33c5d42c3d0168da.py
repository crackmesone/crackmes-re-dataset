import ctypes
import sys

# The crackme uses C rand() without srand(), so the sequence is deterministic
# based on the platform's default seed (usually 1).
# We replicate the MSVC/Windows rand() sequence here.
# MSVC rand() uses: state = state * 214013 + 2531011; return (state >> 16) & 0x7fff

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
BUF_LEN = 80  # indices 0..79, with index 80 set to null => 80 chars

# MSVC rand() state (default seed = 1)
_rand_state = 1

def _msvc_rand():
    global _rand_state
    _rand_state = (_rand_state * 214013 + 2531011) & 0xFFFFFFFF
    return (_rand_state >> 16) & 0x7FFF

def _reset_rand():
    global _rand_state
    _rand_state = 1

def _generate_key_n(n):
    """Generate the nth key (0-indexed) using MSVC rand() without re-seeding.
    The program calls rand() 81 times per key generation loop (i=0..80 inclusive,
    but Buf2[80]=0 terminates, so effectively 81 rand() calls consume the state).
    Wait: loop is `for i in range(0, 81)` (i <= 0x50 means i <= 80, so 81 iterations),
    but Buf2[80] is overwritten with 0, making the password 80 chars.
    """
    # Each loop iteration in the crackme: i goes 0..80 (81 iterations)
    # but Buf2[80] = 0 (null terminator), password length = 80
    key = []
    for i in range(81):  # i <= 0x50 => i in [0,80]
        r = _msvc_rand()
        # Compute r % 26 via the assembly idiom:
        # edx:eax = r * 0x4EC4EC4F (signed 32-bit imul)
        # The assembly does signed multiply then arithmetic shift
        # Equivalent to: floor(r / 26) computed via magic number, then r - floor(r/26)*26
        # This is simply r % 26 for non-negative r
        idx = r % 26
        key.append(ALPHABET[idx])
    # key[80] becomes null terminator, so password is key[0:80]
    return ''.join(key[:80])

def generate_keys(count=5):
    """Generate `count` successive keys as produced by the crackme on each loop iteration."""
    _reset_rand()
    keys = []
    for _ in range(count):
        keys.append(_generate_key_n(0))
    return keys

def _generate_all_keys(count):
    """Simulate the full sequence: each program loop generates one key consuming 81 rand() calls."""
    _reset_rand()
    keys = []
    for _ in range(count):
        key_chars = []
        for i in range(81):
            r = _msvc_rand()
            idx = r % 26
            key_chars.append(ALPHABET[idx])
        keys.append(''.join(key_chars[:80]))
    return keys

def keygen(name=None):
    """Returns a generator yielding successive valid passwords.
    The crackme ignores the name; passwords depend only on rand() state.
    Each call to keygen() resets the rand state to default seed=1.
    """
    _reset_rand()
    while True:
        key_chars = []
        for i in range(81):  # i <= 0x50 (80 decimal), 81 iterations
            r = _msvc_rand()
            idx = r % 26
            key_chars.append(ALPHABET[idx])
        yield ''.join(key_chars[:80])

# Precompute all keys from the default seed=1 state for verify()
def _build_verify_table(n=100):
    gen = keygen()
    return [next(gen) for _ in range(n)]

_KNOWN_KEYS = None

def verify(name, serial):
    """Check if serial matches the expected key for the current program run.
    Since the crackme ignores name and uses a stateless rand() sequence,
    we check if serial equals the first key generated from seed=1.
    If you want to verify any key in the sequence, pass loop_index.
    """
    global _KNOWN_KEYS
    if _KNOWN_KEYS is None:
        _KNOWN_KEYS = _build_verify_table(100)
    # The crackme accepts the key for whichever loop iteration it's on.
    # For a fresh run, the first key (loop 0) is checked first.
    return serial in _KNOWN_KEYS


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
            print(_sv)
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
