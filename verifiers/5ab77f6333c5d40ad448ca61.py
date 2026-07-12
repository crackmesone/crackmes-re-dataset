import hashlib
import struct

# The crackme 'keygenme_2' by scarebyte uses RIPEMD-160 as its core hash.
# The solution writeup includes a full RIPEMD-160 implementation (rmd160.c/h)
# and a keygen GUI (keygen.rc) that takes Name, Company, and Serial fields.
#
# ASSUMPTION: The serial is derived by computing RIPEMD-160 of (name + company)
# or some combination, then formatting the hash bytes as a hex or grouped string.
# The exact input combination (name only, name+company, etc.) and the serial
# format (hex groups, decimal, etc.) are not fully specified in the truncated writeup.
#
# We implement verify() and keygen() based on the most common pattern for
# RIPEMD-160 keygens: hash = RIPEMD160(name + company), serial = hex(hash).

def ripemd160(data: bytes) -> bytes:
    """Compute RIPEMD-160 using hashlib (Python 3.6+ with OpenSSL support)."""
    try:
        h = hashlib.new('ripemd160')
        h.update(data)
        return h.digest()
    except ValueError:
        # Fallback: pure-Python RIPEMD-160
        return _ripemd160_pure(data)


def _ripemd160_pure(msg: bytes) -> bytes:
    """Pure-Python RIPEMD-160 implementation based on the reference rmd160.c."""
    # Initial hash values
    h0 = 0x67452301
    h1 = 0xEFCDAB89
    h2 = 0x98BADCFE
    h3 = 0x10325476
    h4 = 0xC3D2E1F0

    def rol32(x, n):
        x &= 0xFFFFFFFF
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    def F(x, y, z): return x ^ y ^ z
    def G(x, y, z): return (x & y) | (~x & z)
    def H(x, y, z): return (x | ~y) ^ z
    def I(x, y, z): return (x & z) | (y & ~z)
    def J(x, y, z): return x ^ (y | ~z)

    # Padding
    msg_len = len(msg)
    msg = bytearray(msg)
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('<QQ', msg_len * 8, 0)[:8]  # 64-bit little-endian length
    # Actually RIPEMD-160 uses 64-bit length
    # Fix: append 8 bytes for bit length
    # Re-do padding correctly
    msg = bytearray(msg[:len(msg)-8])  # remove what we added
    msg += struct.pack('<Q', msg_len * 8)  # correct 64-bit LE bit length

    # left-round constants
    KL = [0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xA953FD4E]
    # right-round constants
    KR = [0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x7A6D76E9, 0x00000000]

    # Message schedule indices
    RL = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
          7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8,
          3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12,
          1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2,
          4,0,5,9,7,12,2,10,14,1,3,8,11,6,15,13]
    RR = [5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12,
          6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2,
          15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13,
          8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14,
          12,15,10,4,1,5,8,7,6,2,13,14,0,3,9,11]

    # Shift amounts
    SL = [11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8,
          7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12,
          11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5,
          11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12,
          9,15,5,11,6,8,13,12,5,12,13,14,11,8,5,6]
    SR = [8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6,
          9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11,
          9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5,
          15,5,8,11,14,14,6,14,6,9,12,9,12,5,15,8,
          8,5,12,9,12,5,14,6,8,13,6,5,15,13,11,11]

    def round_func(j):
        if   j < 16: return F
        elif j < 32: return G
        elif j < 48: return H
        elif j < 64: return I
        else:        return J

    def round_func_r(j):
        if   j < 16: return J
        elif j < 32: return I
        elif j < 48: return H
        elif j < 64: return G
        else:        return F

    result = bytearray()
    for block_start in range(0, len(msg), 64):
        block = msg[block_start:block_start+64]
        X = list(struct.unpack('<16I', block))

        al, bl, cl, dl, el = h0, h1, h2, h3, h4
        ar, br, cr, dr, er = h0, h1, h2, h3, h4

        for j in range(80):
            f = round_func(j)
            T = (al + f(bl, cl, dl) + X[RL[j]] + KL[j//16]) & 0xFFFFFFFF
            T = (rol32(T, SL[j]) + el) & 0xFFFFFFFF
            al = el
            el = dl
            dl = rol32(cl, 10)
            cl = bl
            bl = T

            f = round_func_r(j)
            T = (ar + f(br, cr, dr) + X[RR[j]] + KR[j//16]) & 0xFFFFFFFF
            T = (rol32(T, SR[j]) + er) & 0xFFFFFFFF
            ar = er
            er = dr
            dr = rol32(cr, 10)
            cr = br
            br = T

        T = (h1 + cl + dr) & 0xFFFFFFFF
        h1 = (h2 + dl + er) & 0xFFFFFFFF
        h2 = (h3 + el + ar) & 0xFFFFFFFF
        h3 = (h4 + al + br) & 0xFFFFFFFF
        h4 = (h0 + bl + cr) & 0xFFFFFFFF
        h0 = T

    return struct.pack('<5I', h0, h1, h2, h3, h4)


def _compute_serial(name: str, company: str = '') -> str:
    """Compute RIPEMD-160 of name+company and format as serial.
    ASSUMPTION: Input is name concatenated with company (or just name).
    ASSUMPTION: Serial is the hex digest of RIPEMD-160, possibly grouped.
    """
    # ASSUMPTION: The crackme hashes the concatenation of name and company
    data = (name + company).encode('ascii', errors='replace')
    digest = ripemd160(data)
    # ASSUMPTION: Serial is upper-case hex of the 20-byte digest
    hex_str = digest.hex().upper()
    # ASSUMPTION: Serial may be grouped in blocks of 8 chars separated by '-'
    # e.g. AABBCCDD-EEFF0011-22334455-66778899-AABBCCDD
    groups = [hex_str[i:i+8] for i in range(0, 40, 8)]
    return '-'.join(groups)


def verify(name: str, serial: str, company: str = '') -> bool:
    """Verify name/serial pair. Company defaults to empty string.
    ASSUMPTION: Serial validation is done by computing RIPEMD-160 of
    (name + company) and comparing to the provided serial (case-insensitive,
    ignoring dashes).
    """
    expected = _compute_serial(name, company)
    # Normalize both serials for comparison
    def normalize(s):
        return s.replace('-', '').upper()
    return normalize(expected) == normalize(serial)


def keygen(name: str, company: str = '') -> str:
    """Generate a valid serial for the given name (and optionally company)."""
    return _compute_serial(name, company)



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
