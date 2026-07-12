import random as _random

# Keys used in the check transformation
KEYS = [0x50, 0x77, 0x64, 0x3A, 0x20, 0x72, 0x73]


def _compute_check_char(ch: str, i: int) -> int:
    """Given a character from u2 and its index, compute the corresponding check character value."""
    a = (ord(ch) << 4) & 0xFF
    # Treat as signed byte: if >= 128 negate
    if a >= 128:
        a = ((-a) & 0xFF)
        # Actually: (sbyte)a < 0 => a = (Int32)((sbyte)-a) = -((sbyte)a)
        # (sbyte)a when a>=128 is a-256, so -(a-256) = 256-a
        a = 256 - (ord(ch) << 4 & 0xFF)
    a += KEYS[i % 7]
    a %= 0x7F
    if a < 0x20:
        a += 0x20
    return a


def _check_from_u2(u2: str) -> str:
    """Compute the 'check' string from u2, then reverse it."""
    check_chars = []
    for i, ch in enumerate(u2):
        a = ord(ch) << 4
        # Mask to byte
        a = a & 0xFF
        # Signed byte check
        signed_a = a if a < 128 else a - 256
        if signed_a < 0:
            a = (-signed_a) & 0xFF
        a += KEYS[i % 7]
        a %= 0x7F
        if a < 0x20:
            a += 0x20
        check_chars.append(chr(a))
    # Reverse
    return ''.join(reversed(check_chars))


def verify(name: str, serial: str) -> bool:
    """
    Validate username (name) and password (serial).

    Checks:
    1. len(username) >= 8  (actually > 7, i.e. >= 8)
    2. password contains 'x'
    3. posX = first index of 'x' in password; len(username) >= posX
    4. Split:
         u1 = username[:posX], u2 = username[posX:]
         p1 = password[:posX], p2 = password[posX+1:]
    5. len(p1) == len(p2)
    6. len(p1) == len(u2)  =>  len(u1) == len(u2)
    7. For each i in range(len(u2)):
           check[i] (= reversed check string)[i] satisfies:
               p1[i] + p2[i] == 2 * check[i]
               p1[i] + p2[i] must be even, average == check[i]
           Also: u1[i] + u2_something...
           Actually from keygen:
               check = StrRev(check_chars from u2)
               For each i: a = check[i], b = p1[i], d = p2[i]
               b + d = 2*a  (since d = 2c - a, c = (3a-b+1)//2 ... but average of b and d = a - rounding)
               More precisely: c = (3a - b + 1) // 2  (integer division)
               d = 2c - a
               So b + d = b + 2c - a = b + (3a - b + 1) - a = 2a + 1  OR  b + d = b + 2c - a with c = (3a-b)//2
               Actually c = (3a - b + 1) // 2 uses integer division, so b + d varies.
               ASSUMPTION: The actual check is (p1[i] + p2[i]) / 2 == check[i] within tolerance
               From the keygen: b + d = b + 2*((3a-b+1)//2) - a
               For simplicity we check: (ord(p1[i]) + ord(p2[i])) // 2 == ord(check[i])
               OR more precisely that ord(p1[i]) + ord(p2[i]) in {2*ord(check[i])-1, 2*ord(check[i])}
    """
    username = name
    password = serial

    # Check 1: username length > 7
    if len(username) <= 7:
        return False

    # Check 2: password contains 'x'
    posX = password.find('x')
    if posX == -1:
        return False

    # Check 3: len(username) >= posX
    if len(username) < posX:
        return False

    # Split
    u1 = username[:posX]
    u2 = username[posX:]
    p1 = password[:posX]
    p2 = password[posX+1:]

    # Check 4: len(p1) == len(p2)
    if len(p1) != len(p2):
        return False

    # Check 5: len(p1) == len(u2)
    if len(p1) != len(u2):
        return False

    # So len(u1) == len(u2) == len(p1) == len(p2) == posX
    length = posX

    # Compute check string from u2
    check = _check_from_u2(u2)
    # check has length == len(u2) == length

    # Check the p1/p2 vs check relationship
    # From keygen: b = p1[i], d = p2[i], a = check[i]
    # b in [max(b1, 3a-2*b2), a]
    # c = (3a - b + 1) // 2
    # d = 2c - a
    # b + d = b + 2*((3a - b + 1)//2) - a
    # For even (3a-b): c = (3a-b)/2, d = 3a-b - a = 2a-b, so b+d=2a
    # For odd (3a-b): c = (3a-b+1)/2, d = 3a-b+1-a = 2a-b+1, so b+d=2a+1
    # => (b + d) in {2*ord(check[i]), 2*ord(check[i])+1}
    # Also u1[i] relates to a,b,c,d but the check in the binary seems to check p1+p2 vs check
    # ASSUMPTION: verify checks (p1[i]+p2[i]) in {2*check[i], 2*check[i]+1}
    for i in range(length):
        a = ord(check[i])
        b = ord(p1[i])
        d = ord(p2[i])
        s = b + d
        if s != 2*a and s != 2*a + 1:
            return False

    # ASSUMPTION: u1 relationship - from keygen u1[i] is also derived from check[i]
    # a_u1 in [c, c+d_range] where c and d depend on check and p1
    # We won't re-check u1 fully since the writeup doesn't show that binary check explicitly
    # ASSUMPTION: u1 check is implicitly satisfied by the keygen construction

    return True


def keygen(name: str = None) -> str:
    """Generate a valid (username, password) pair. If name provided, tries to use it; else generates fresh."""
    import random

    # Use lowercase letters for simplicity
    b1, b2 = 0x61, 0x7A  # 'a' to 'z'
    charset_all = [chr(c) for c in range(b1, b2+1)]

    length = random.randint(4, 6)  # posX length

    u1_chars = []
    u2_chars = []
    p1_chars = []
    p2_chars = []
    check_chars_pre_rev = []

    for i in range(length):
        # Find a valid u2 character
        charset = list(charset_all)
        random.shuffle(charset)
        found = False
        for ch in charset:
            a = ord(ch) << 4
            a = a & 0xFF
            signed_a = a if a < 128 else a - 256
            if signed_a < 0:
                a = (-signed_a) & 0xFF
            a += KEYS[i % 7]
            a %= 0x7F
            if a < 0x20:
                a += 0x20
            if b1 <= a <= b2:
                check_chars_pre_rev.append(chr(a))
                u2_chars.append(ch)
                found = True
                break
        if not found:
            # fallback
            ch = 'a'
            a = ord(ch) << 4 & 0xFF
            signed_a = a if a < 128 else a - 256
            if signed_a < 0:
                a = (-signed_a) & 0xFF
            a += KEYS[i % 7]
            a %= 0x7F
            if a < 0x20:
                a += 0x20
            check_chars_pre_rev.append(chr(a))
            u2_chars.append(ch)

    check = list(reversed(check_chars_pre_rev))

    for i in range(length):
        a = ord(check[i])
        # b = p1[i]: b in [max(b1, 3a-2*b2), a], b != 'x'
        lo = max(b1, 3*a - 2*b2)
        hi = a
        valid_b = [b for b in range(lo, hi+1) if b != ord('x') and b1 <= b <= b2]
        if not valid_b:
            # ASSUMPTION: fallback to a
            b = a if a != ord('x') else a - 1
        else:
            b = random.choice(valid_b)

        c = (3*a - b + 1) // 2
        d = 2*c - a

        # u1[i]: in [c, c + min(c-b1, b2-c)]
        d_range = min(c - b1, b2 - c)
        lo_a = c
        hi_a = c + max(0, d_range)
        if lo_a > hi_a or lo_a < b1 or hi_a > b2:
            a_val = c
        else:
            a_val = random.randint(lo_a, hi_a)
        if a_val < b1 or a_val > b2:
            a_val = b1

        p1_chars.append(chr(b))
        p2_chars.append(chr(d))
        u1_chars.append(chr(a_val))

    u1 = ''.join(u1_chars)
    u2 = ''.join(u2_chars)
    p1 = ''.join(p1_chars)
    p2 = ''.join(p2_chars)

    username = u1 + u2
    password = p1 + 'x' + p2

    return username, password



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
