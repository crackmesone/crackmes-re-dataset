import sys
import gmpy2
import binascii
import struct
import ctypes

# PANAMA hash implementation in pure Python
# Based on the PANAMA specification by Joan Daemen and Craig Clapp

def rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def t32(x):
    return x & 0xFFFFFFFF

class PanamaContext:
    def __init__(self):
        self.state = [0] * 17
        self.buffer = [[0]*8 for _ in range(32)]
        self.buffer_ptr = 0
        self.data = b''
        self.data_ptr = 0

def panama_step(state, buf, ptr0, inw):
    ptr24 = (ptr0 - 8) & 31
    ptr31 = (ptr0 - 1) & 31

    # BUPDATE
    bup_pairs = [(0,2),(1,3),(2,4),(3,5),(4,6),(5,7),(6,0),(7,1)]
    for n0, n2 in bup_pairs:
        buf[ptr24][n0] ^= buf[ptr31][n2]
        buf[ptr31][n2] ^= inw[n2]

    a = list(state)

    # GAMMA
    g = [0]*17
    for i in range(17):
        n0 = i
        n1 = (i+1) % 17
        n2 = (i+2) % 17
        g[n0] = a[n0] ^ (a[n1] | t32(~a[n2]))

    # PI
    pi_map = [
        (0,  0,  0),
        (1,  7,  1),
        (2, 14,  3),
        (3,  4,  6),
        (4, 11, 10),
        (5,  1, 15),
        (6,  8, 21),
        (7, 15, 28),
        (8,  5,  4),
        (9, 12, 13),
        (10, 2, 23),
        (11, 9,  2),
        (12,16, 14),
        (13, 6, 27),
        (14,13,  9),
        (15, 3, 24),
        (16,10,  8),
    ]
    p = [0]*17
    for dst, src, rot in pi_map:
        p[dst] = rotl32(g[src], rot)

    # THETA via M17
    t = [0]*17
    m17_indices = [
        (0,1,2,4),(1,2,3,5),(2,3,4,6),(3,4,5,7),(4,5,6,8),
        (5,6,7,9),(6,7,8,10),(7,8,9,11),(8,9,10,12),(9,10,11,13),
        (10,11,12,14),(11,12,13,15),(12,13,14,16),(13,14,15,0),
        (14,15,16,1),(15,16,0,2),(16,0,1,3)
    ]
    for n0,n1,n2,n4 in m17_indices:
        t[n0] = p[n0] ^ p[n1] ^ p[n4]

    # SIGMA
    ptr16 = ptr0 ^ 16
    a[0] = t[0] ^ 1
    for i in range(1, 9):
        a[i] = t[i] ^ inw[i-1]
    for i in range(9, 17):
        a[i] = t[i] ^ buf[ptr16][i-9]

    new_ptr0 = ptr31
    return a, buf, new_ptr0

def panama_hash(data):
    """Compute PANAMA hash of data, returns 32-byte digest."""
    state = [0] * 17
    buf = [[0]*8 for _ in range(32)]
    ptr0 = 0

    # Pad data to multiple of 32 bytes with 0x01 then zeros
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % 32 != 0:
        padded.append(0x00)

    # Push phase
    for block_idx in range(len(padded) // 32):
        block = padded[block_idx*32:(block_idx+1)*32]
        inw = [struct.unpack_from('<I', block, i*4)[0] for i in range(8)]
        state, buf, ptr0 = panama_step(state, buf, ptr0, inw)

    # Pull phase (32 iterations with zero input)
    for _ in range(32):
        inw = [0]*8
        state, buf, ptr0 = panama_step(state, buf, ptr0, inw)

    # Output: state[1..8] as little-endian 32-bit words
    out = b''
    for i in range(1, 9):
        out += struct.pack('<I', state[i])
    return out


def compute(name):
    n2 = gmpy2.mpz("0x5A2CA7F4E6CDF2CA496DD866139F04CDEC8EBA61C3C3187152FB2A1093BFC15A0ECC07A62089CC7CBBB9064EE6207FAC3875FC94277F3FF9BDFC1E555D799D19")
    g  = gmpy2.mpz("0x9C0928664535BA873094A7EDA0F4E831BE92E00B895171E99CA67CA0A7B5534C301371E79EB85B4DA250B77A4495A7523ACB0BAD2BEA6129B")
    n  = gmpy2.mpz("0x97EFB4FC28B5B6FD5F99D7116164B5839932A076D1FE8D0863BBD02981F7BC85")
    l  = gmpy2.mpz("0x25FBED3F0A2D6DBF57E675C458592D6081A396234C6C956E2047CB29A9AC7C98")

    name_bytes = bytes(name, 'UTF-8')
    h_bytes = panama_hash(name_bytes)
    h = gmpy2.mpz(int.from_bytes(h_bytes, 'big'))

    x = gmpy2.c_div((gmpy2.powmod(h, l, n2) - 1), n)
    y = gmpy2.c_div((gmpy2.powmod(g, l, n2) - 1), n)
    s1 = (x * gmpy2.invert(y, n)) % n
    x2 = gmpy2.powmod(gmpy2.invert(g, n), s1, n)
    s2 = gmpy2.powmod(h * x2, gmpy2.invert(n, l), n)

    s1h = hex(s1)[2:]
    s2h = hex(s2)[2:]
    serial = s1h[:32] + "-" + s1h[32:] + "-" + s2h[:32] + "-" + s2h[32:]
    return serial


def verify(name, serial):
    """Verify name/serial pair by recomputing the expected serial."""
    try:
        expected = compute(name)
        return serial.lower() == expected.lower()
    except Exception:
        return False


def keygen(name):
    """Generate a valid serial for the given name."""
    return compute(name)



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
