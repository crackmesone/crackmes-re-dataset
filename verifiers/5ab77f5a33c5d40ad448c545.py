import ctypes

def ror_byte(byte, n):
    byte = byte & 0xFF
    for _ in range(n):
        if byte & 1:
            byte = ((byte >> 1) | 0x80) & 0xFF
        else:
            byte = (byte >> 1) & 0xFF
    return byte

def rol_byte(byte, n):
    byte = byte & 0xFF
    for _ in range(n):
        if byte & 0x80:
            byte = ((byte << 1) | 1) & 0xFF
        else:
            byte = (byte << 1) & 0xFF
    return byte

def transform(serial_bytes):
    """Apply the three transformation loops and return 11 bytes."""
    s = list(serial_bytes[:11])
    if len(s) != 11:
        return None

    # Step 0: XOR last byte with 0x18
    s[10] = (s[10] ^ 0x18) & 0xFF

    # Step 1: transform first 10 bytes
    for i in range(10):
        v = s[i] & 0xFF
        v = rol_byte(v, 2)
        v = (v ^ 0xFF) & 0xFF
        v = (v + 8) & 0xFF
        v = (v ^ 0x22) & 0xFF
        v = (v << 4) & 0xFF
        v = (v ^ 0x63) & 0xFF
        s[i] = v

    # Step 2: transform first 5 bytes using bytes 5-9
    for i in range(5):
        var1 = s[i]
        var2 = s[i + 5]
        var1 = (var1 >> 2) & 0xFF
        var2 = (var2 ^ 0xFF) & 0xFF
        var2 = (var2 << 2) & 0xFF
        var1 = (var1 ^ var2) & 0xFF
        var1 = ror_byte(var1, 2)
        var1 = (var1 + 0x0A) & 0xFF
        var2 = (var2 >> 2) & 0xFF
        var2 = (var2 + 0x14) & 0xFF
        var1 = (var1 ^ var2 ^ (i + 1)) & 0xFF
        s[i] = var1

    # Step 3: transform bytes 5-9 using updated bytes 0-4
    for i in range(5):
        var1 = s[i]
        var2 = s[i + 5]
        var1 = (var1 >> 2) & 0xFF
        var2 = (var2 ^ 0x7E) & 0xFF
        var2 = (var2 << 2) & 0xFF
        var1 = (var1 ^ var2) & 0xFF
        var1 = ror_byte(var1, 2)
        var1 = (var1 + 0x19) & 0xFF
        var2 = (var2 >> 2) & 0xFF
        var2 = (var2 + 0x0A) & 0xFF
        var1 = (var1 ^ var2) & 0xFF
        s[i + 5] = var1

    return s

TARGET_HEX = "312E363D3430DF70F0705F"
TARGET = bytes.fromhex(TARGET_HEX)

def verify(name, serial):
    """Verify serial string (11 chars). name is not used in the algorithm."""
    # ASSUMPTION: name is not used in the algorithm; only serial matters
    if len(serial) != 11:
        return False
    s = [ord(c) for c in serial]
    result = transform(s)
    if result is None:
        return False
    result_hex = ''.join('%02X' % b for b in result)
    return result_hex == TARGET_HEX

def keygen(name=None):
    """Brute-force generate all valid serials using printable ASCII chars.
    The last character must produce 0x5F after XOR with 0x18,
    so serial[10] ^ 0x18 == 0x5F => serial[10] = 0x47 = 'G'.
    The first 10 chars are pairs (serial[i], serial[i+5]) for i in 0..4.
    ASSUMPTION: name is not used in the algorithm.
    """
    # Fixed last char: 0x47 ^ 0x18 = 0x5F, which is one of the target bytes
    # Actually the last byte after xor becomes 0x5F which matches TARGET[10]=0x5F
    fixed_last = chr(0x5F ^ 0x18)  # = 'G'

    # Find valid pairs for each of the 5 positions
    valid_pairs = [[] for _ in range(5)]
    char_range = range(0x20, 0x7F)  # printable ASCII

    for i in range(5):
        for c1 in char_range:
            for c2 in char_range:
                # Apply transform to pair (c1, c2) for position i
                v1 = c1 & 0xFF
                v1 = rol_byte(v1, 2)
                v1 = (v1 ^ 0xFF) & 0xFF
                v1 = (v1 + 8) & 0xFF
                v1 = (v1 ^ 0x22) & 0xFF
                v1 = (v1 << 4) & 0xFF
                v1 = (v1 ^ 0x63) & 0xFF
                tmp1 = v1

                v2 = c2 & 0xFF
                v2 = rol_byte(v2, 2)
                v2 = (v2 ^ 0xFF) & 0xFF
                v2 = (v2 + 8) & 0xFF
                v2 = (v2 ^ 0x22) & 0xFF
                v2 = (v2 << 4) & 0xFF
                v2 = (v2 ^ 0x63) & 0xFF
                tmp2 = v2

                # Loop 2
                var1 = tmp1
                var2 = tmp2
                var1 = (var1 >> 2) & 0xFF
                var2 = (var2 ^ 0xFF) & 0xFF
                var2 = (var2 << 2) & 0xFF
                var1 = (var1 ^ var2) & 0xFF
                var1 = ror_byte(var1, 2)
                var1 = (var1 + 0x0A) & 0xFF
                var2s = (var2 >> 2) & 0xFF
                var2s = (var2s + 0x14) & 0xFF
                var1 = (var1 ^ var2s ^ (i + 1)) & 0xFF
                out1 = var1

                # Loop 3
                var1b = out1
                var2b = tmp2
                var1b = (var1b >> 2) & 0xFF
                var2b = (var2b ^ 0x7E) & 0xFF
                var2b = (var2b << 2) & 0xFF
                var1b = (var1b ^ var2b) & 0xFF
                var1b = ror_byte(var1b, 2)
                var1b = (var1b + 0x19) & 0xFF
                var2b2 = (var2b >> 2) & 0xFF
                var2b2 = (var2b2 + 0x0A) & 0xFF
                var1b = (var1b ^ var2b2) & 0xFF
                out2 = var1b

                if out1 == TARGET[i] and out2 == TARGET[i + 5]:
                    valid_pairs[i].append((chr(c1), chr(c2)))

    # Generate all combinations
    def combinations(pairs_list, idx=0, current=[]):
        if idx == 5:
            s1 = ''.join(p[0] for p in current)
            s2 = ''.join(p[1] for p in current)
            yield s1 + s2 + fixed_last
            return
        for pair in pairs_list[idx]:
            yield from combinations(pairs_list, idx + 1, current + [pair])

    results = list(combinations(valid_pairs))
    if results:
        return results[0]  # return first valid serial
    return None


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
