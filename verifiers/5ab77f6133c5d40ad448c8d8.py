import ctypes

# Predefined sbox constants from solution 2 (Form1.cs)
CONSTB = [
    0x408112f1,
    0x1a3b0b51,
    0x2957c9fd,
    0x1b327d1d,
    0xa38d0af1,
    0x2ad5e941,
]

def u32(x):
    return x & 0xFFFFFFFF

# Custom CRC-like hash (ytrewq.nhash / qwerty) from Form1.cs
def build_crc_table():
    num = 0xbaadf00d
    tqepq = [0] * 0x100
    for i in range(0x100):
        num2 = i
        for j in range(8, 0, -1):
            if (num2 & 1) == 1:
                num2 = u32((num2 >> 1) ^ num)
            else:
                # num / num == 1 always (num != 0), so shift by 1
                num2 = num2 >> 1
        tqepq[i] = num2
    return tqepq

CRC_TABLE = build_crc_table()

def nhash(data: bytes) -> int:
    num = 0xFFFFFFFF  # ~0 as uint32
    for b in data:
        index = (num & 0xFF) ^ b
        num = u32((num >> 8) ^ CRC_TABLE[index])
    return u32(~num)

# .NET String.GetHashCode() for ASCII strings (Framework 2.0/3.5 32-bit)
# ASSUMPTION: .NET GetHashCode for string is version/platform dependent.
# This reimplements the known .NET 2.0 32-bit algorithm for ASCII strings.
def dotnet_hashcode(s: str) -> int:
    # .NET 2.0 x86 String.GetHashCode:
    # int hash1 = 5381; int hash2 = hash1;
    # process pairs of chars
    chars = [ord(c) for c in s]
    hash1 = 5381
    hash2 = 5381
    i = 0
    while i < len(chars):
        hash1 = u32(u32(((hash1 << 5) + hash1)) ^ chars[i])
        if i + 1 < len(chars):
            hash2 = u32(u32(((hash2 << 5) + hash2)) ^ chars[i + 1])
        i += 2
    result = u32(hash1 + u32(hash2 * 1566083941))
    # Convert to signed then back to unsigned to match C# (uint) cast
    return result

def encrypt(blocks, sbox, key):
    """TEA-like encrypt as shown in solution 2 Encrypt() method."""
    rounds = 0
    b2 = u32(blocks[0])
    b1 = u32(blocks[1])
    key_shift = 0
    while rounds < 32:
        b1 = u32(b1 + (u32((u32(b2 << 4) ^ u32(b2 >> 5)) + b2) ^ u32(key_shift + sbox[key_shift & 3])))
        rounds += 1
        b2 = u32(b2 + rounds)
        key_shift = u32(key_shift + key)
        b2 = u32(b2 + ((u32((u32(b1 << 4) ^ u32(b1 >> 5)) + b1) ^ u32(key_shift + sbox[(key_shift >> 11) % 4])) - rounds))
    blocks[0] = b1
    blocks[1] = b2

def decrypt(blocks, sbox, key):
    """Reverse of encrypt: TEA-like decrypt."""
    # Derive final key_shift after 32 rounds
    # Each round does key_shift += key, so after 32 rounds: key_shift = key * 32
    rounds = 32
    key_shift = u32(key * 32)
    b1 = u32(blocks[0])
    b2 = u32(blocks[1])
    while rounds > 0:
        b2 = u32(b2 - ((u32((u32(b1 << 4) ^ u32(b1 >> 5)) + b1) ^ u32(key_shift + sbox[(key_shift >> 11) % 4])) - rounds))
        key_shift = u32(key_shift - key)
        b2 = u32(b2 - rounds)
        b1 = u32(b1 - (u32((u32(b2 << 4) ^ u32(b2 >> 5)) + b2) ^ u32(key_shift + sbox[key_shift & 3])))
        rounds -= 1
    blocks[0] = b2
    blocks[1] = b1

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 5 or len(name) > 27:
        raise ValueError("Name length must be between 5 and 27 characters")

    name_bytes = name.encode('ascii')
    tmp = nhash(name_bytes)          # custom CRC hash (num5 equivalent)
    hash_code = dotnet_hashcode(name) # .NET GetHashCode

    # Choose key such that (pgdsfa % 0x39) - 1 == 32  => pgdsfa % 0x39 == 33
    # pgdsfa = 0x8ffe2225 ^ fsfsdf = 0x8ffe2225 ^ (p3 ^ hash_code)
    # We want pgdsfa = 33, so: fsfsdf = 0x8ffe2225 ^ 33 = 0x8ffe2204
    # fsfsdf = p3 ^ hash_code  => p3 = hash_code ^ 0x8ffe2204
    # But we can also pick any key with key % 0x39 == 33 mod 0x39
    # Using the simplified approach from solution 1:
    key = u32(33)  # pgdsfa value that gives num=32
    p3 = u32(hash_code ^ 0x8ffe2225 ^ key)

    # Now encrypt [hash_code, tmp] using key=33 and sbox=CONSTB
    inblock = [hash_code, tmp]
    encrypt(inblock, CONSTB, key)

    p1 = inblock[0]
    p2 = inblock[1]

    serial = f"{p1:08X}-{p2:08X}-{p3:08X}"
    return serial

def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair by simulating the crackme check."""
    if len(name) < 5 or len(name) > 27:
        return False
    if len(serial) != 26:
        return False
    if serial[8] != '-' or serial[17] != '-':
        return False

    try:
        p1 = int(serial[0:8], 16)
        p2 = int(serial[9:17], 16)
        p3 = int(serial[18:26], 16)
    except ValueError:
        return False

    name_bytes = name.encode('ascii')
    num5 = nhash(name_bytes)
    hash_code = dotnet_hashcode(name)

    fsfsdf = u32(p3 ^ hash_code)
    pgdsfa = u32(0x8ffe2225 ^ fsfsdf)
    num = u32(pgdsfa % 0x39) - 1
    if num == 0 or num > 0xFFFFFF00:  # num==0 => vxzzz returns false; overflow check
        return False

    # Decrypt [p1, p2] with key=pgdsfa, sbox=CONSTB
    inblock = [p1, p2]
    # ASSUMPTION: The simplified algorithm with num=32 (key=33) corresponds to
    # the TEA-like decrypt in solution 2. We use the full decrypt here.
    decrypt(inblock, CONSTB, pgdsfa)

    recovered_hash = inblock[0]
    recovered_num5 = inblock[1]

    return recovered_hash == hash_code and recovered_num5 == num5


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
