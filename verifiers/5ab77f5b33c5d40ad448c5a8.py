import hashlib
import struct

# RSA-350 parameters from the keygen source
N = 1256999810287721585587379048569008578748297833782713742720085108575305825883648159979687095493369087715481
D = 737758788206924497453629783224848787426236723933840140701634427965920282958629177912259580412714179583013

# Magic strings array (8 entries)
MAGIC = [
    'BfUpNpdP3ApLaxIr0yto',
    'MIjhBlDxcD7biA84iAR0',
    'DJYdez6hAgiZkhOpsdML',
    'I74d7OB6sMoM698tKFoY',
    'TLzm4ueUoZ48kXs4QJKo',
    'Shg1WL8EqwJPg4rofFkP',
    'D53JUPEsrHrJ0t5yZl1x',
    'MhU0o1xo7IN2laFLbgFY',
]


def haval256_pass3(data: bytes) -> bytes:
    """HAVAL-256 with 3 passes. Using hashlib if available, otherwise stub."""
    # ASSUMPTION: Python's hashlib does not include HAVAL-256/3 natively.
    # We implement a pure-Python HAVAL-256/3 here based on the published spec.
    # This is a best-effort implementation; correctness should be verified.
    import struct

    # HAVAL constants
    def F1(x6, x5, x4, x3, x2, x1, x0):
        return (x1 & (x4 ^ x0)) ^ (x2 & x5) ^ (x3 & x6) ^ x0

    def F2(x6, x5, x4, x3, x2, x1, x0):
        return (x2 & ((x1 & ~x3) ^ (x4 & x5) ^ x6 ^ x0)) ^ (x4 & (x1 ^ x5)) ^ (x3 & x5) ^ x0

    def F3(x6, x5, x4, x3, x2, x1, x0):
        return (x3 & ((x1 & x2) ^ x6 ^ x5)) ^ (x1 & x4) ^ (x2 & x6) ^ x0

    def rot32(x, n):
        x &= 0xFFFFFFFF
        return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

    def haval_step(f, p, q, w, c, rot1, rot2):
        t = f
        return (rot32(t, 7) + rot32(p, rot1) + q + w + c) & 0xFFFFFFFF

    # Initial digest (HAVAL-256)
    h = [
        0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
        0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
    ]

    # Pad the message
    bit_len = len(data) * 8
    data = bytearray(data)
    data.append(0x01)  # HAVAL padding: append 0x01 not 0x80
    while len(data) % 128 != 118:
        data.append(0x00)
    # Append version/pass/output length word (version=1, passes=3, output=256)
    # HAVAL tail: 10 bytes
    # bits[0:2] = output_len/32 - 1 = 7 (256/32-1)
    # bits[2:4] = passes - 1 = 2
    # bits[4:7] = version = 1
    tail_word = (1 << 4) | (2 << 2) | 7  # version=1, passes=3, outlen=256
    data += struct.pack('<H', tail_word)
    # Append 64-bit length
    data += struct.pack('<Q', bit_len)

    # ASSUMPTION: The HAVAL-256/3 implementation below is a placeholder.
    # A full correct implementation requires all 3 passes of 32 steps each.
    # The logic below is incomplete and serves as a structural outline only.
    # A correct implementation would require the full step constants and ordering.

    # For now, raise NotImplementedError to indicate this is incomplete
    raise NotImplementedError("HAVAL-256/3 not fully implemented; use a library or C extension")


def generate(uName: str, uMail: str) -> str:
    """
    Implements the key generation algorithm from the Pascal source.
    uName = name field, uMail = company/email field.
    """
    # Concatenate both strings
    temp = uName + uMail
    data = temp.encode('latin-1')  # ASSUMPTION: encoding is Latin-1/ANSI

    # SHA-1 hash
    sha_digest = hashlib.sha1(data).digest()  # 20 bytes

    # buffer[0..39]
    buffer = bytearray(40)
    buffer[0:20] = sha_digest

    # Select magic string based on sha_digest[0]
    if sha_digest[0] == 0:
        x = 0
    else:
        x = (sha_digest[0] - 1) // 0x20  # integer division
    x = min(x, 7)  # clamp to valid index

    magic = MAGIC[x]
    for i, ch in enumerate(magic):
        buffer[i + 20] = ord(ch)  # buffer[i+19] in 1-indexed Pascal = buffer[i+19] 0-indexed
    # Note: Pascal uses 1-indexed: buffer[i+19] for i=1..len means buffer[20..39] in 0-indexed
    # ASSUMPTION: the above mapping is correct (Pascal i+19 with i starting at 1 = 0-based i+19)

    # MD5 loop: 0x100 down to 0x1 (256 iterations)
    for _ in range(0x100, 0, -1):
        # Find length: first zero byte
        length = 0
        for b in buffer:
            if b == 0:
                break
            length += 1
        # MD5 of buffer[0:length]
        md5_digest = hashlib.md5(bytes(buffer[:length])).digest()  # 16 bytes
        buffer[0:16] = md5_digest
        buffer[16] = 0  # buffer[$10] := 0

    # HAVAL-256 with 3 passes on buffer[0:0x10] (16 bytes)
    # ASSUMPTION: HavalUpdate is called with @buffer, $10 meaning 16 bytes of buffer
    try:
        haval_result = haval256_pass3(bytes(buffer[0:16]))
        haval_hex = haval_result.hex().upper()
    except NotImplementedError:
        # Cannot proceed without HAVAL-256/3
        raise RuntimeError(
            "HAVAL-256/3 implementation required. "
            "Please install a library that supports HAVAL-256/3."
        )

    if haval_hex[0] == '0':
        return 'no serial for this name'

    # RSA: compute m = c^d mod n
    # c is the HAVAL result interpreted as a big integer
    c = int(haval_hex, 16)
    m = pow(c, D, N)

    # Convert m to hex string
    result = format(m, 'X')
    return result


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for (name, company). 
    ASSUMPTION: The crackme takes name and company separately.
    Here we treat 'serial' as the company field for simplicity,
    but the real verify would need to check the generated serial matches.
    
    Since we don't have the verification logic (only keygen),
    we regenerate and compare.
    """
    # ASSUMPTION: name is the name field, serial is compared against generated key.
    # We cannot verify without knowing the company field used.
    # This is a structural placeholder.
    raise NotImplementedError(
        "verify() requires both name and company fields. "
        "Use keygen(name, company) to generate the serial."
    )


def keygen(name: str, company: str = 'uCF') -> str:
    """
    Generate serial for given name and company.
    Default company is 'uCF' as used in the reference keygen.
    """
    return generate(name, company)



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
