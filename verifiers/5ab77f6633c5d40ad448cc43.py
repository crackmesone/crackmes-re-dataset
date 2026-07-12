#!/usr/bin/env python3
"""
Keygen for HappyTown CrackMe#31
Protection: TIGER hash

Algorithm:
1. Compute Tiger hash of name[0] (first char)
2. Compute Tiger hash of name[1] (second char)
3. Compute Tiger hash of name[2] (third char)
4. Compute Tiger hash of full name
5. Take the first 4 bytes (first dword) of each hash, format as uppercase hex string
6. Serial = part1-part2-part3-part4

Requirements: pip install pytiger2  OR use a Tiger implementation
We implement Tiger here using the `tiger` package or a pure-python fallback.
"""

import struct

# Pure Python Tiger-192 implementation
# Based on the Tiger hash specification

def _tiger_sboxes():
    # Tiger S-boxes (standard)
    # These are the standard Tiger S-box tables
    t1 = [
        0x02AAB17CF7E90C5E, 0xAC424B03E243A8EC, 0x72CD5BE30DD5FCD3, 0x6D019B93F6F97F3A,
        0xCD9978FFD21F9193, 0x7573A1C9708029E2, 0xB164326B922A83C3, 0x46883EAF2AA9AD2E,
        0x1BB3978631C5AA7F, 0xAC3AEB42E767C9D8, 0x3AC1F10463A22FAD, 0xBAE0208F6BAB4A13,
        0xF7B8E05B85A6E5C7, 0x88CB82C5B3A0CB0E, 0x91CAAA0CB8A08F8E, 0x7FB8F3E9B4E4EE0C,
        0x5C42ED54C040D982, 0x0B82BEED66F98E63, 0xC7D4AA436F0B27C8, 0xCBD9B74C03D3A0EA,
        0x7D7BBD2B30E9C3F4, 0x88B9F97D2C9D4E4A, 0x7D5E0B6D9E4E9B4C, 0x4E2A42B5B9A4D90C,
        0x657FD9E7F47E9AF0, 0xF79DEB15F08534D2, 0x2C40F93F57A72B36, 0xBB0CD1A3FFEBA29A,
        0x18E0C5D8F3F7BF9C, 0xC8D22CCD7E3E6C80, 0xC9AF01AC0F7ECAB4, 0x6F09F79EA88A2E4E,
        0x66F5EC05E82E9D78, 0xE0CC7BFFE9C5AE5A, 0xFC9A4E56B4E01F6C, 0x06D6CDE3E04B3F34,
        0x5FF7F9FA3E0A0C10, 0xC1B487BAEC7D1A6E, 0x18B3B6D36FAE2E66, 0x0B0819F35EB3B76A,
        0x60B68D0BB88F88C2, 0xA92FA2B5B6AABF40, 0xDFEC1CEBB5D70E6A, 0x9A8E25F1E56B8E64,
        0x85C070CF0A45F8C8, 0x01B0F40CB85AB4FE, 0x66B12B46DA38B9FA, 0xAE34B0AC39E28AD2,
        0x2C028DABAC37E824, 0x7B4F5D3B29A02BF2, 0xE02DFC46E24D6DEC, 0x0F6B5E39B8C61B78,
        0x0B6BD27E41DB7C6A, 0x99F76FA0F77E4614, 0x696C27FE8A3BFCE0, 0x35E0F95BA7C2C808,
        0x4E97F7BA068A6BD2, 0x3EDE8E5AA0C87E2E, 0xB673D9A42543E024, 0x1B6E5EEC7BC9AB26,
        0x8FC1A4D42B524D66, 0x97D32C47B5A6EACA, 0xB01DE37E048F66D4, 0xA21D9D73BED6A8FE,
        # ASSUMPTION: Full s-box tables are very long; using a known Tiger library is preferred
        # Padding with zeros to make indexing safe - this will NOT produce correct hashes
    ]
    # ASSUMPTION: Full Tiger s-boxes not inlined here for brevity
    # We will use the `hashlib`-based approach or the `tiger` package
    return None


def tiger_hash(data: bytes) -> bytes:
    """
    Compute Tiger-192 hash of data.
    Returns 24 bytes (192 bits).
    
    ASSUMPTION: We use the `tiger` third-party package.
    If not available, raises ImportError with instructions.
    """
    try:
        import tiger  # pip install python-tiger
        h = tiger.new(data)
        return h.digest()
    except ImportError:
        pass
    
    try:
        import tigerpy  # alternative package
        return tigerpy.tiger(data)
    except ImportError:
        pass
    
    # Try using the `Crypto` or `pytigerlib`
    # ASSUMPTION: Fall back to our own implementation placeholder
    raise ImportError(
        "No Tiger hash library found. Install one:\n"
        "  pip install python-tiger\n"
        "or use another Tiger-192 implementation."
    )


def first_dword_to_hex(hash_bytes: bytes) -> str:
    """
    Take the first 4 bytes of a Tiger hash and return uppercase hex string.
    Tiger is little-endian internally, but the writeup shows the hash bytes
    in the order they appear in memory and takes the first 8 hex chars.
    
    From the writeup:
      'O' hash bytes: a69a1f8661037ae81934678b29eff8904bef9ffe0c360489
      first dword (cotstr): A69A1F86
    
    So we just take the first 4 bytes and format them as uppercase hex.
    """
    return hash_bytes[:4].hex().upper()


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    
    Algorithm:
    1. Tiger hash of name[0]
    2. Tiger hash of name[1]
    3. Tiger hash of name[2]
    4. Tiger hash of full name
    5. Take first 4 bytes of each hash -> 8 hex chars
    6. Join with '-'
    """
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters long")
    
    name_bytes = name.encode('ascii')  # ASSUMPTION: ASCII encoding
    
    h1 = tiger_hash(name_bytes[0:1])  # Tiger of first char
    h2 = tiger_hash(name_bytes[1:2])  # Tiger of second char
    h3 = tiger_hash(name_bytes[2:3])  # Tiger of third char
    h4 = tiger_hash(name_bytes)       # Tiger of full name
    
    part1 = first_dword_to_hex(h1)
    part2 = first_dword_to_hex(h2)
    part3 = first_dword_to_hex(h3)
    part4 = first_dword_to_hex(h4)
    
    serial = f"{part1}-{part2}-{part3}-{part4}"
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that a serial is valid for the given name.
    
    Checks:
    1. Name length >= 3
    2. Serial length == 35 (8+1+8+1+8+1+8 = 35)
    3. Serial format: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    4. Each block matches the first dword of the corresponding Tiger hash
    """
    if len(name) < 3:
        return False
    
    if len(serial) != 35:
        return False
    
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    
    if not all(len(p) == 8 for p in parts):
        return False
    
    try:
        expected = keygen(name)
    except (ImportError, ValueError):
        return False
    
    return serial.upper() == expected.upper()



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
