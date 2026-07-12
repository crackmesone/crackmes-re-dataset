#!/usr/bin/env python3
"""
Keygen for Nass CM#1 based on kao's writeup.

The crackme reads a key file and uses a 'subMagic' function to decrypt
two things from the same key file buffer:
  1. A greeting message (32 bytes, magic byte = 0x0F)
  2. A code patch (32 bytes, magic byte = 0x0A)

The subMagic function reads 4 bytes from the key file to produce 1 output BIT.
The 4-byte -> 1-bit mapping depends on the magic byte, but kao found by brute
force that the following 4-byte sequences produce the given bit combinations
for magic bytes 0x0F and 0x0A:

  4-byte sequence  | bit for 0x0F | bit for 0x0A
  -------------------------------------------------
  00 00 00 FC      |      0       |      0
  00 00 FC 00      |      0       |      1
  00 00 04 00      |      1       |      0
  00 00 00 04      |      1       |      1

So to produce a desired byte in the greeting AND a desired byte in the code
patch simultaneously, we process each bit-pair (bit from greeting byte,
bit from code byte) and write 4 bytes per bit-pair.

Each byte of output requires 8 * 4 = 32 bytes in the key file.
Total key file size = 400h = 1024 bytes (kao uses 400h buffer).

Greeting is 32 bytes -> 32 * 32 = 1024 bytes total key file.
Code patch is also 32 bytes, processed in parallel.

Bit order: highest order bit first (rol al,1 in the asm -> MSB first).
"""

# 4-byte sequences indexed by (bit_for_0F, bit_for_0A)
BIT_SEQ = {
    (0, 0): bytes([0x00, 0x00, 0x00, 0xFC]),
    (0, 1): bytes([0x00, 0x00, 0xFC, 0x00]),
    (1, 0): bytes([0x00, 0x00, 0x04, 0x00]),
    (1, 1): bytes([0x00, 0x00, 0x00, 0x04]),
}

# The patched code that goes at 4010D0 (jump replaced with NOPs)
PATCHED_PROC = bytes([
    0x6A, 0x00, 0x68, 0x08, 0x30, 0x40, 0x00, 0x68,
    0x22, 0x30, 0x40, 0x00, 0x6A, 0x00, 0xE8, 0xC3,
    0x00, 0x00, 0x00, 0x90, 0x90, 0x64, 0x8F, 0x05,
    0x00, 0x00, 0x00, 0x00, 0x83, 0xC4, 0x04, 0xC3,
])


def build_keyfile(greeting: bytes) -> bytes:
    """
    Build the 1024-byte key file.
    greeting: exactly 32 bytes (padded with zeros if shorter).
    code_patch: the 32-byte code fragment to be patched in.
    """
    if len(greeting) > 32:
        raise ValueError("Greeting must be <= 32 bytes")
    # Pad greeting to 32 bytes
    greeting = greeting.ljust(32, b'\x00')
    code_patch = PATCHED_PROC  # always the same patched code

    key = bytearray()
    for i in range(32):
        g_byte = greeting[i]
        c_byte = code_patch[i]
        # Process MSB first
        for bit_pos in range(7, -1, -1):
            g_bit = (g_byte >> bit_pos) & 1
            c_bit = (c_byte >> bit_pos) & 1
            key += BIT_SEQ[(g_bit, c_bit)]

    # Should be 32 * 8 * 4 = 1024 = 0x400 bytes
    assert len(key) == 0x400, f"Key length error: {len(key)}"
    return bytes(key)


def keygen(name: str) -> bytes:
    """
    Generate a key file bytes for the given name/greeting.
    name is used as the greeting string (max 32 chars).
    Returns the raw bytes to write to key.dat.
    """
    greeting = name.encode('ascii', errors='replace')[:32]
    return build_keyfile(greeting)


def verify(name: str, serial: bytes) -> bool:
    """
    Verify that the given serial (key file bytes) is valid for the name
    by checking that decoding it with magic bytes 0x0F and 0x0A reproduces
    the greeting and the patched code respectively.

    ASSUMPTION: The verify logic here re-implements the bit extraction:
    for each group of 4 bytes, we check which sequence it matches and
    extract the two bits, then reconstruct the greeting and code bytes.
    """
    if len(serial) < 0x400:
        return False

    # Build reverse lookup
    reverse_map = {v: k for k, v in BIT_SEQ.items()}

    greeting_bits = []
    code_bits = []
    
    for i in range(256):  # 256 groups of 4 bytes
        chunk = bytes(serial[i*4:(i+4)*4 - (i*4 - i*4)])  # careful indexing
        chunk = bytes(serial[i*4:i*4+4])
        if chunk not in reverse_map:
            return False
        g_bit, c_bit = reverse_map[chunk]
        greeting_bits.append(g_bit)
        code_bits.append(c_bit)

    # Reconstruct bytes from bits (MSB first, 8 bits per byte)
    greeting = bytearray()
    code_out = bytearray()
    for byte_idx in range(32):
        g_byte = 0
        c_byte = 0
        for bit_pos in range(8):
            overall_bit = byte_idx * 8 + bit_pos
            g_byte = (g_byte << 1) | greeting_bits[overall_bit]
            c_byte = (c_byte << 1) | code_bits[overall_bit]
        greeting.append(g_byte)
        code_out.append(c_byte)

    # Check greeting matches name
    expected_greeting = name.encode('ascii', errors='replace')[:32].ljust(32, b'\x00')
    if bytes(greeting) != expected_greeting:
        return False

    # Check code patch matches expected
    # ASSUMPTION: only the patched (NOPs) version is accepted
    if bytes(code_out) != PATCHED_PROC:
        return False

    return True

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
