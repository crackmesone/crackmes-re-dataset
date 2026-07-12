import struct

# RIPEMD-128 implementation based on the assembly source provided in the writeup
# The keygen:
# 1. Gets the hostname
# 2. Computes RIPEMD-128 of the hostname
# 3. Writes (hostname + null byte + hash) to oorja.dat
# The crackme reads oorja.dat, verifies hostname matches and hash is correct

def _f(x, y, z): return x ^ y ^ z
def _g(x, y, z): return (x & y) | (~x & z)
def _h(x, y, z): return (x | ~y) ^ z
def _i(x, y, z): return (x & z) | (y & ~z)

def _rol32(x, n): return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def ripemd128(msg):
    if isinstance(msg, str):
        msg = msg.encode('latin-1')
    
    # Init
    h0 = 0x67452301
    h1 = 0xEFCDAB89
    h2 = 0x98BADCFE
    h3 = 0x10325476
    
    # Padding
    orig_len = len(msg)
    msg = bytearray(msg)
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    # Append length in bits as 64-bit little-endian
    msg += struct.pack('<Q', orig_len * 8)
    
    # Process each 512-bit block
    for i in range(0, len(msg), 64):
        block = msg[i:i+64]
        X = list(struct.unpack('<16I', block))
        
        a, b, c, d = h0, h1, h2, h3
        aa, bb, cc, dd = h0, h1, h2, h3
        
        # Left rounds
        # Round 1: FF
        RL1 = [11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8]
        XL1 = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        for j in range(16):
            t = (a + _f(b,c,d) + X[XL1[j]]) & 0xFFFFFFFF
            a = _rol32(t, RL1[j])
            a, b, c, d = d, a, b, c
        
        # Round 2: GG
        RL2 = [7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12]
        XL2 = [7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8]
        for j in range(16):
            t = (a + _g(b,c,d) + X[XL2[j]] + 0x5A827999) & 0xFFFFFFFF
            a = _rol32(t, RL2[j])
            a, b, c, d = d, a, b, c
        
        # Round 3: HH
        RL3 = [11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5]
        XL3 = [3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12]
        for j in range(16):
            t = (a + _h(b,c,d) + X[XL3[j]] + 0x6ED9EBA1) & 0xFFFFFFFF
            a = _rol32(t, RL3[j])
            a, b, c, d = d, a, b, c
        
        # Round 4: II
        RL4 = [11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12]
        XL4 = [1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2]
        for j in range(16):
            t = (a + _i(b,c,d) + X[XL4[j]] + 0x8F1BBCDC) & 0xFFFFFFFF
            a = _rol32(t, RL4[j])
            a, b, c, d = d, a, b, c
        
        # Right rounds
        # Round 1: III
        RR1 = [8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6]
        XR1 = [5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12]
        for j in range(16):
            t = (aa + _i(bb,cc,dd) + X[XR1[j]] + 0x50A28BE6) & 0xFFFFFFFF
            aa = _rol32(t, RR1[j])
            aa, bb, cc, dd = dd, aa, bb, cc
        
        # Round 2: HHH
        RR2 = [9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11]
        XR2 = [6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2]
        for j in range(16):
            t = (aa + _h(bb,cc,dd) + X[XR2[j]] + 0x5C4DD124) & 0xFFFFFFFF
            aa = _rol32(t, RR2[j])
            aa, bb, cc, dd = dd, aa, bb, cc
        
        # Round 3: GGG
        RR3 = [9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5]
        XR3 = [15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13]
        for j in range(16):
            t = (aa + _g(bb,cc,dd) + X[XR3[j]] + 0x6D703EF3) & 0xFFFFFFFF
            aa = _rol32(t, RR3[j])
            aa, bb, cc, dd = dd, aa, bb, cc
        
        # Round 4: FFF
        RR4 = [11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12]
        XR4 = [8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14]
        for j in range(16):
            t = (aa + _f(bb,cc,dd) + X[XR4[j]]) & 0xFFFFFFFF
            aa = _rol32(t, RR4[j])
            aa, bb, cc, dd = dd, aa, bb, cc
        
        # Combine
        t = (h1 + c + dd) & 0xFFFFFFFF
        h1 = (h2 + d + aa) & 0xFFFFFFFF
        h2 = (h3 + a + bb) & 0xFFFFFFFF
        h3 = (h0 + b + cc) & 0xFFFFFFFF
        h0 = t
    
    return struct.pack('<4I', h0, h1, h2, h3)


def keygen(name):
    """Generate the content that should be written to oorja.dat for the given name.
    The file format is: name bytes + null byte + RIPEMD-128 hash bytes
    The serial/keyfile content is returned as hex string of the hash."""
    if isinstance(name, str):
        name_bytes = name.encode('latin-1')
    else:
        name_bytes = name
    hash_bytes = ripemd128(name_bytes)
    # The file written is: name (len+1 bytes including null) then hash
    # Return the hash as hex (this is the 'serial' embedded in the keyfile)
    return hash_bytes.hex()


def verify(name, serial):
    """Verify that serial matches the RIPEMD-128 hash of name.
    serial should be a hex string of 32 chars (16 bytes = 128 bits)."""
    if isinstance(name, str):
        name_bytes = name.encode('latin-1')
    else:
        name_bytes = name
    expected = ripemd128(name_bytes)
    try:
        serial_bytes = bytes.fromhex(serial)
    except Exception:
        return False
    return serial_bytes == expected



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
