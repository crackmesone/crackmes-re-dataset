import struct
import math
import random
import string

# ---------------------------------------------------------------------------
# SHA1-like hash ("very similar to classic SHA1" but with tweaked constants)
# Based on keygen.c from the writeup
# ---------------------------------------------------------------------------

SHA_MAGIC0 = 0x5a827999
SHA_MAGIC1 = 0x6ed9eba1
SHA_MAGIC2 = 0x8a1bbcdc
SHA_MAGIC3 = 0xca62c1d6

# ASSUMPTION: init constants differ slightly from real SHA1 (last digit changed)
# From keygen.c: 0x67452399 (real SHA1: 0x67452301), etc.
SHA_INIT0 = 0x67452399
SHA_INIT1 = 0xefcdaba9
SHA_INIT2 = 0x98badcfe
SHA_INIT3 = 0x10325486
SHA_INIT4 = 0xc3d2e2f0

MASK = 0xFFFFFFFF

def rol32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK

def make_message(username: str) -> bytes:
    """Replicate make_un() + padding from keygen.c.
    From the (truncated) source:
      msg[ix] = (un_copy[ix] << 2) & 0x23  for ix in range(len)
      then append \x80 + copy of un_copy
      then msg[0x3c] = len << 4  (big-endian length word at end)
    ASSUMPTION: The truncated part means the exact padding is partially guessed.
    We keep as close to the code as possible.
    """
    un_bytes = username.encode('latin-1')
    ln = len(un_bytes)
    msg = bytearray(0x40)

    # First part: transformed chars
    for i in range(ln):
        msg[i] = (un_bytes[i] << 2) & 0x23

    # Append \x80 after the transformed section and copy original + \x80
    un_copy = un_bytes + b'\x80'
    for j, b in enumerate(un_copy):
        if i + j + 1 < 0x3c:
            msg[i + j + 1] = b

    # Length word at 0x3c (big-endian 32-bit)
    # ASSUMPTION: msg[0x3c] = len << 4 as a 32-bit big-endian word
    temp = (ln << 4) & MASK
    msg[0x3c] = (temp >> 24) & 0xFF
    msg[0x3d] = (temp >> 16) & 0xFF
    msg[0x3e] = (temp >> 8) & 0xFF
    msg[0x3f] = temp & 0xFF

    return bytes(msg)

def sha_hash_block(message: bytes):
    """Single-block SHA1-like hash from keygen.c sha_hash()."""
    assert len(message) == 0x40

    m0, m1, m2, m3, m4 = SHA_INIT0, SHA_INIT1, SHA_INIT2, SHA_INIT3, SHA_INIT4

    # Build w_buf[0..15] from message bytes (big-endian 32-bit words)
    w = []
    for ix in range(0x10):
        word = (message[4*ix] << 24) | (message[4*ix+1] << 16) | \
               (message[4*ix+2] << 8) | message[4*ix+3]
        w.append(word)

    # Extend to 80 words
    for ix in range(0x10, 0x50):
        temp = w[ix-3] ^ w[ix-8] ^ w[ix-14] ^ w[ix-16]
        w.append(rol32(temp, 1))

    for ix in range(0x50):
        if ix < 0x14:
            m_index = SHA_MAGIC0
            # Note: (m1 ^ 0xffefffff) instead of ~m1 -- this is the tweak
            temp = (m2 & m1) | ((m1 ^ 0xffefffff) & m3)
        elif ix < 0x28:
            m_index = SHA_MAGIC1
            temp = m1 ^ m2 ^ m3
        elif ix < 0x3c:
            m_index = SHA_MAGIC2
            temp = ((m3 | m2) & m1) | (m3 & m2)
        else:
            m_index = SHA_MAGIC3
            temp = m1 ^ m2 ^ m3

        temp = (temp + rol32(m0, 5) + m4 + w[ix] + m_index) & MASK
        m4 = m3
        m3 = m2
        m2 = rol32(m1, 0x1e)
        m1 = m0
        m0 = temp

    m0 = (SHA_INIT0 + m0) & MASK
    m1 = (SHA_INIT1 + m1) & MASK
    m2 = (SHA_INIT2 + m2) & MASK
    m3 = (SHA_INIT3 + m3) & MASK
    m4 = (SHA_INIT4 + m4) & MASK

    return m0, m1, m2, m3, m4

def hash_to_ascii(h0, h1, h2, h3, h4) -> str:
    """Convert 5 x 32-bit words to hex string (40 hex chars = 160 bits).
    ASSUMPTION: standard hex encoding, lowercase or uppercase -- using lowercase.
    """
    return '%08x%08x%08x%08x%08x' % (h0, h1, h2, h3, h4)

def compute_serial(username: str) -> str:
    msg = make_message(username)
    h = sha_hash_block(msg)
    return hash_to_ascii(*h)

# ---------------------------------------------------------------------------
# Condition 2 (sub_401d36)
# ---------------------------------------------------------------------------
def check_condition2(serial: str) -> bool:
    s0 = 0.0
    for ch in serial:
        c = ord(ch)
        s0 += (c * c) / 32.0
        s0 /= math.cos(1.0 / c)
    return math.ceil(s0) > 3052

# ---------------------------------------------------------------------------
# Condition 3 (sub_401e2a)
# ---------------------------------------------------------------------------
def check_condition3(serial: str) -> bool:
    s1 = 1
    for ch in serial:
        s1 = (s1 + 1) * ord(ch)
    s1 = abs(s1)
    while s1 > 10000:
        s1 >>= 1
    return s1 < 6999

# ---------------------------------------------------------------------------
# Condition 4 (sub_401ea6)
# ---------------------------------------------------------------------------
def check_condition4(serial: str) -> bool:
    import math as _math
    pi = _math.pi
    s2 = pi
    limit = len(serial) << 10
    c0 = ord(serial[0])
    while s2 < limit:
        s2 *= c0
    return 400000.0 <= s2 <= 500000.0

# ---------------------------------------------------------------------------
# Combined verify
# ---------------------------------------------------------------------------
def verify(name: str, serial: str) -> bool:
    """Check all 4 conditions."""
    # Condition 1: serial must equal hash_to_string(SHA1-like(name))
    expected = compute_serial(name)
    if expected != serial:
        return False
    # Condition 2
    if not check_condition2(serial):
        return False
    # Condition 3
    if not check_condition3(serial):
        return False
    # Condition 4
    if not check_condition4(serial):
        return False
    return True

# ---------------------------------------------------------------------------
# Keygen: brute-force random usernames until all conditions satisfied
# ---------------------------------------------------------------------------
def _is_good_string(s: str) -> bool:
    """ASSUMPTION: printable ASCII only, length == TEST_MSG_LEN (0x10 = 16)."""
    return all(0x20 <= ord(c) <= 0x7e for c in s)

def keygen(name: str = None):
    """Generate a valid (username, serial) pair.
    If name is provided, compute its serial and check; return serial if valid.
    Otherwise brute-force random usernames (matching original keygen strategy).
    Returns serial string or raises ValueError if none found.
    """
    if name is not None:
        serial = compute_serial(name)
        if (check_condition2(serial) and
                check_condition3(serial) and
                check_condition4(serial)):
            return serial
        raise ValueError(f'Username {name!r} does not satisfy conditions 2-4')

    # Random search
    charset = [chr(c) for c in range(0x20, 0x7f)]
    for attempt in range(100000):
        # Generate random 16-char printable username
        username = ''.join(random.choices(charset, k=16))
        serial = compute_serial(username)
        if (check_condition2(serial) and
                check_condition3(serial) and
                check_condition4(serial)):
            return username, serial
    raise RuntimeError('No valid pair found after 100000 attempts')

# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

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
