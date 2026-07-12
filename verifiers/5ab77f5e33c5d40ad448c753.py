import struct

def _name_to_dword(name):
    # Only first 4 characters matter; pad with nulls if shorter
    b = (name.encode('latin-1') + b'\x00\x00\x00\x00')[:4]
    return struct.unpack('<I', b)[0]

def _encrypt_name(name):
    g = _name_to_dword(name)
    g = (g ^ 0x1337) & 0xFFFFFFFF
    g = (g + 0x2016) & 0xFFFFFFFF
    g = (g * 2)      & 0xFFFFFFFF
    g = (g << 4)     & 0xFFFFFFFF
    return g

def keygen(name):
    """
    Reverse the serial encryption to find the serial that passes the check.
    The final encrypted serial must equal 0x004010FB.
    Serial encryption steps:
        s ^= encrypted_name
        s += 0xDEAD
        s *= 2
        s >>= 3
        s -= 0x1337
    Result must be 0x004010FB.
    Reverse:
        n = 0x4010FB + 0x1337       => undo sub 0x1337
        n = n << 3                  => undo shr 3 (multiply by 8)
        n = n // 2                  => undo mul 2 (divide by 2)
        n = n - 0xDEAD              => undo add 0xDEAD
        n = n ^ encrypted_name      => undo xor
    """
    g = _encrypt_name(name)

    n = (0x4010FB + 0x1337) & 0xFFFFFFFF
    # undo shr 3 -> shl 3
    n = (n << 3) & 0xFFFFFFFF
    # undo mul 2 -> div 2
    n = (n // 2) & 0xFFFFFFFF
    # undo add 0xDEAD -> sub 0xDEAD
    n = (n - 0xDEAD) & 0xFFFFFFFF
    # undo xor with encrypted name
    n = (n ^ g) & 0xFFFFFFFF

    # Convert n to 8-hex-digit string (big-endian display of the 4-byte value)
    # The crackme stores n as little-endian in memory, then reads as hex string pairs.
    # The keygen in the solution uses bswap before wsprintf('%X', eax).
    # From solution 1 (assembly keygen): bswap eax then wsprintf '%X'
    # From solution 2 (Pascal keygen): inttohex(n,8) then reverse byte pairs.
    # Both produce the same result: big-endian hex string of n, but displayed
    # with bytes reversed (little-endian byte order displayed as hex).
    # We'll follow the Pascal approach: inttohex then reverse byte pairs.

    s = '{:08X}'.format(n)
    # s is 8 hex chars representing n in big-endian hex.
    # Apply the 'bug' correction: if even-indexed char (1-based: s[2],s[4],s[6],s[8])
    # is a letter A-F, subtract 2 from the preceding nibble char.
    # Using 0-based indexing: positions 1,3,5,7 are the 'even' chars (1-based 2,4,6,8).
    s = list(s)
    for i in range(0, 8, 2):
        hi_char = s[i]
        lo_char = s[i+1]
        if lo_char in 'ABCDEF':
            # subtract 2 from high nibble, modulo 16
            hi_val = int(hi_char, 16)
            hi_val = (hi_val - 2) % 16
            s[i] = '{:X}'.format(hi_val)
    s = ''.join(s)

    # Reverse byte pairs (bytes 0,1 swap with bytes 6,7 etc)
    serial = s[6:8] + s[4:6] + s[2:4] + s[0:2]
    return serial

def verify(name, serial):
    """
    Simulate what the crackme does:
    1. Encrypt name (4 chars -> dword via VM)
    2. Parse serial as hex string (8 chars) into a dword
    3. Encrypt the serial dword using: xor enc_name, add 0xDEAD, mul 2, shr 3, sub 0x1337
    4. Check result == 0x004010FB
    """
    if not serial or len(serial) < 8:
        return False

    serial8 = serial[:8].upper()

    # Parse serial hex string into bytes (little-endian nibble encoding)
    # Each pair of hex chars encodes one byte.
    # The 'bug': if the second char of a pair is A-F, the first char had 2 added to it.
    # To decode: for each pair, parse normally as hex byte.
    # ASSUMPTION: We just parse the serial directly as a hex number (big-endian of reversed bytes)
    # i.e. serial '78563412' -> bytes 0x78,0x56,0x34,0x12 -> dword 0x12345678 (little-endian)
    try:
        b0 = int(serial8[0:2], 16)
        b1 = int(serial8[2:4], 16)
        b2 = int(serial8[4:6], 16)
        b3 = int(serial8[6:8], 16)
    except ValueError:
        return False

    # Serial stored little-endian in memory: first pair is lowest byte
    # So dword = b0 | (b1<<8) | (b2<<16) | (b3<<24)
    serial_dword = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
    serial_dword &= 0xFFFFFFFF

    g = _encrypt_name(name)

    # Encrypt serial
    r = (serial_dword ^ g) & 0xFFFFFFFF
    r = (r + 0xDEAD)       & 0xFFFFFFFF
    r = (r * 2)            & 0xFFFFFFFF
    r = (r >> 3)           & 0xFFFFFFFF
    r = (r - 0x1337)       & 0xFFFFFFFF

    return r == 0x004010FB



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
