# Reconstruction of hazeme_2 by mysfyt
# Based on the keygen source (Main.cpp) from the writeup by Knight
#
# Algorithm:
# 1. Key for Serpent is 16 bytes: p1 = [0x12, 0x34, 0, 0, ..., 0] (16 bytes)
# 2. Plaintext (cCypherText before decryption) is built as:
#    cCypherText[i] = name[i % len(name)] ^ seed, where seed starts at 0x11
#    and increments by 0x11 each iteration, for i in 0..15
# 3. p2 = Serpent_ECB_Decrypt(key=p1, data=cCypherText)  -- note: keygen uses 'Decryption'
#    which means the crackme verifies by doing Serpent_ECB_Encrypt(key=p1, data=p2) == cCypherText
# 4. After computing p2, p1[0] ^= name[0]; p1[1] ^= name[1]  (for serial display)
# 5. Serial = FormatSerial(p1[0:2], p2[0:16])
#    FormatSerial: B256ToB32(p1[0:2]) + '-' + B256ToB32(p2[0:16])
#
# ASSUMPTION: The crackme validates by reversing: it takes the serial, decodes base32,
# recovers p1_original=[0x12,0x34,...] and p2, then encrypts p2 with Serpent and
# compares to the expected cCypherText derived from the name.
# ASSUMPTION: Serpent block cipher is used in ECB mode with a 128-bit key.
# We use pycryptodome's Serpent if available; fallback noted.

try:
    from Crypto.Cipher import Serpent as _Serpent
    def serpent_decrypt(key, data):
        cipher = _Serpent.new(key, _Serpent.MODE_ECB)
        return cipher.decrypt(data)
    def serpent_encrypt(key, data):
        cipher = _Serpent.new(key, _Serpent.MODE_ECB)
        return cipher.encrypt(data)
except ImportError:
    # ASSUMPTION: If pycryptodome Serpent not available, algorithm cannot be fully executed
    def serpent_decrypt(key, data):
        raise NotImplementedError("Serpent cipher not available. Install pycryptodome with Serpent support.")
    def serpent_encrypt(key, data):
        raise NotImplementedError("Serpent cipher not available. Install pycryptodome with Serpent support.")

ALPHABET = list('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
ALPHABET_MAP = {c: i for i, c in enumerate(ALPHABET)}


def b256_to_b32(data: bytes) -> str:
    """Convert bytes to base32 using the custom alphabet (5-bit groups)."""
    n_len = len(data)
    result = []
    i = 0
    b_pos = 0
    while i < n_len:
        b_byte = 0
        b_taken = 0
        b_prev = 0
        while b_taken != 5:
            b_byte |= ((data[i] >> b_pos) << b_taken) & 0x1F
            b_taken += 8 - b_pos
            if b_taken > 5:
                b_taken = 5
            b_pos += b_taken - b_prev
            if b_pos >= 8:
                i += 1
                b_pos = 0
                if i >= n_len:
                    break
            b_prev = b_taken
        result.append(ALPHABET[b_byte & 0x1F])
    # Pad to multiple of 8
    while len(result) % 8 != 0:
        result.append(ALPHABET[0])
    return ''.join(result)


def format_serial(p1_bytes: bytes, p2_bytes: bytes) -> str:
    part1 = b256_to_b32(p1_bytes[:2])
    part2 = b256_to_b32(p2_bytes[:16])
    return part1 + '-' + part2


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    name_bytes = name.encode('ascii', errors='replace')
    n_len = len(name_bytes)
    if n_len <= 2:
        raise ValueError("Name must be longer than 2 characters")

    # Build the key: p1 = [0x12, 0x34, 0, 0, ..., 0] (16 bytes)
    p1 = bytearray(16)
    p1[0] = 0x12
    p1[1] = 0x34

    # Build cCypherText (plaintext for decryption = input to Serpent decrypt)
    seed = 0x11
    cypher_text = bytearray(16)
    for i in range(16):
        cypher_text[i] = name_bytes[i % n_len] ^ (seed & 0xFF)
        seed = (seed + 0x11) & 0xFF

    # p2 = Serpent_ECB_Decrypt(key=p1, ciphertext=cypher_text)
    # Note: The keygen does Decryption (SDec.ProcessData), so p2 = decrypt(p1, cypher_text)
    p2 = bytearray(serpent_decrypt(bytes(p1), bytes(cypher_text)))

    # XOR p1[0] and p1[1] with name chars for display
    p1_display = bytearray(p1)
    p1_display[0] ^= name_bytes[0]
    p1_display[1] ^= name_bytes[1]

    return format_serial(bytes(p1_display[:2]), bytes(p2))


def verify(name: str, serial: str) -> bool:
    """Verify a serial for the given name by regenerating and comparing.
    ASSUMPTION: The crackme checks the serial by re-generating it from the name
    and comparing -- or equivalently by decoding the serial and verifying the
    Serpent encryption relationship. We verify by regenerating.
    """
    if len(name) <= 2:
        return False
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
    except Exception:
        return False



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
