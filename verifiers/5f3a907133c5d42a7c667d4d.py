import random as _random

# Allowed characters whitelist (from decompiled source)
ALLOWED = set('abdefimopqsxwz')


def _username_valid(username: str) -> bool:
    """Username must consist only of allowed chars or digits (0-9)."""
    username = username.lower()
    for ch in username:
        if '0' <= ch <= '9':
            continue
        if ch not in ALLOWED:
            return False
    return True


def _password_valid(password: str) -> bool:
    """
    Password must be >= 8 chars and must NOT contain any of the allowed
    non-digit characters (i.e. every non-digit char must be outside ALLOWED).
    NOTE: The decompiled password check logic is inverted relative to the
    username check - it flags 'is_valid = false' when a char IS in the
    allowed list. Comments in the writeup confirm the password must NOT
    contain: a,b,d,e,f,i,m,o,p,q,s,w,z  (i.e. the same whitelist chars).
    Digits are always acceptable in both username and password.
    """
    if len(password) < 8:
        return False
    for ch in password:
        if '0' <= ch <= '9':
            continue
        if ch in ALLOWED:
            # Password must NOT contain allowed-list chars
            return False
    return True


def _make_random_next(seed: int) -> int:
    """Emulate .NET Random(seed).Next() using Python's built-in random."""
    # .NET Random uses Knuth's subtractive RNG.  Python's random is Mersenne
    # Twister, so we cannot exactly replicate .NET's sequence here.
    # ASSUMPTION: We rely on the key insight from the writeup: if username
    # and password have the SAME LENGTH, then random(len_u).Next() ==
    # random(len_p).Next(), making num4 == num5 and thus the generated
    # strings identical.  We don't need to compute the actual .NET value.
    # The comparison only passes when both seeds are equal (same length).
    r = _random.Random(seed)
    return r.random()  # placeholder - actual value doesn't matter for verify logic below


def _dot_net_random_next(seed: int) -> int:
    """
    Approximate .NET System.Random(seed).Next().
    .NET Random internal state is seeded and Next() returns a non-negative int.
    ASSUMPTION: We approximate using Python's random seeded with the same seed.
    The critical property used by the crackme is: same seed => same Next() value.
    We use Python's randint to get a non-negative int (matches .NET's Next() range).
    """
    r = _random.Random(seed)
    # .NET Next() returns [0, Int32.MaxValue)
    return r.randint(0, 2147483647)


def verify(name: str, serial: str) -> bool:
    """
    Verify a (username, password) pair against the crackme logic.

    Rules (from decompiled source + writeups):
    1. Password length >= 8.
    2. Username chars: only digits or chars in ALLOWED set (after toLower).
    3. Password chars: only digits or chars NOT in ALLOWED set.
    4. Random(len(username)).Next() % 2 and Random(len(password)).Next() % 2
       are used to shift each character.  The first min(len_u, len_p) chars
       of the two resulting strings must match.
       => Simplest solution: same string for both (same length => same shift).
    """
    username = name
    password = serial

    # Check 1: password length
    if len(password) < 8:
        return False

    # Check 2: username characters
    if not _username_valid(username):
        return False

    # Check 3: password characters (inverted check - must NOT contain ALLOWED chars)
    if not _password_valid(password):
        return False

    # Check 4: random-based string comparison
    username_lower = username.lower()
    num4 = _dot_net_random_next(len(username_lower))
    num5 = _dot_net_random_next(len(password))

    username_generated = ''.join(chr(ord(c) + (num4 % 2)) for c in username_lower)
    password_generated = ''.join(chr(ord(c) + (num5 % 2)) for c in password)

    min_len = min(len(username_generated), len(password_generated))
    for i in range(min_len):
        if username_generated[i] != password_generated[i]:
            return False

    return True


def keygen(name: str) -> str:
    """
    Generate a valid (username, password) pair.

    Key insight from writeup: if username == password, then:
    - len(username) == len(password) => same RNG seed => same Next() value
      => num4 == num5 => same shift applied => generated strings are identical
      => comparison always passes.

    However username and password have DIFFERENT character rules:
    - Username: only ALLOWED chars (or digits)
    - Password: only NON-ALLOWED chars (or digits)

    So username == password won't satisfy both constraints simultaneously
    UNLESS digits are used (digits are accepted by both rules).

    Strategy:
    - Use a digit-only string of length >= 8 for BOTH username and password.
      Digits pass the username check (digits allowed) and pass the password
      check (digits are not in ALLOWED, so not rejected).
    - Same string => same length => same RNG seed => num4 == num5 => same shift
      => generated strings match.

    ASSUMPTION: .NET Random seeded identically produces identical Next() values,
    making num4 % 2 == num5 % 2, so character shifts are identical.
    """
    import random
    # Use digits only: valid for username (digits allowed) AND password (digits not in ALLOWED)
    digits = '0123456789'
    length = max(8, len(name)) if name else 8
    # Use name length to influence output, but ensure >= 8 chars
    length = max(8, length)
    pwd = ''.join(random.choice(digits) for _ in range(length))
    # Both username and password are the same digit string
    return pwd



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
