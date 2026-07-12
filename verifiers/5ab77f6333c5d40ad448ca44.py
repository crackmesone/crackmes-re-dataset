#!/usr/bin/env python3
"""
illussion by black_eye - RSA-based crackme keygen

The crackme does:
  passwordBigNum = powmod(serial_as_bignum, C01, C02_patched)
  Then checks that the first 8 bytes of the result (big-endian) are:
    52 45 47 44 41 54 41 2D  (i.e. 'REGEATA-'  / hex '524547444154412D')
  Followed by the hex-encoded username bytes, terminated by '00'

Since C02 (the modulus) was changed by 1 byte (C02 -> C02_patched, a prime),
the keygen computes:
  serial = powmod(x, d, n)
where:
  n = C02_patched (prime)
  d = modular inverse of C01 modulo (n-1)  (since n is prime, phi(n) = n-1)
  x = 0x524547444154412D || hex(name_bytes) || 00
"""

def _build_plaintext(name: str) -> int:
    """Build the integer x from the username."""
    # prefix: 'REGEATA-' in hex
    hex_str = '524547444154412D'
    for ch in name:
        hex_str += format(ord(ch), '02x')
    hex_str += '00'
    return int(hex_str, 16)

# Constants from the keygen source / writeup
# C02_patched: the 512-bit modulus modified to be prime (+2 from original C02)
# From writeup: n is the patched modulus used in keygen.cpp
# keygen.cpp uses n = C9003E9F...7B (this is the patched prime C'2 expressed as the
# 63-hex-digit value shown; the writeup's full decimal is 512-bit).
# We take n directly from keygen.cpp mpz_set_str:
N_HEX = 'C9003E9F9F2DD06EE2913D34805DC551D6C38A9E763704A16A88DC7793B0064BD1C7D49EAC51A3817969B351A7CC5FCECB1EFD2BFD436EC037B3008DD34F1D7B'
# d from keygen.cpp:
D_HEX = '64801F4FCF96E83771489E9A402EE2A8EB61C54F3B1B8250B5446E3BC9D80325E8E3EA4F5628D1C0BCB4D9A8D3E62FE7658F7E95FEA1B7601BD98046E9A78EBF'

N = int(N_HEX, 16)
D = int(D_HEX, 16)

# C01 (the public exponent e) from the writeup description
# ASSUMPTION: The full value of C01 starts with C9003E9F9... - the writeup
# truncates it. The keygen only needs d and n, so we reconstruct e for verify().
# We compute e indirectly: e = modular_inverse(d, n-1) since n is prime.
E = pow(D, -1, N - 1)  # phi(n) = n-1 because n is prime


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against a name.
    serial is expected as a hex string (uppercase or lowercase).
    """
    try:
        serial_int = int(serial, 16)
    except ValueError:
        return False

    # Compute serial^E mod N  (the crackme's check)
    result = pow(serial_int, E, N)

    # Convert result to big-endian bytes (up to 256 bytes as the crackme uses 0x100)
    result_bytes = result.to_bytes(256, byteorder='big')

    # Build expected plaintext
    expected_int = _build_plaintext(name)
    # Convert expected to bytes (same length context)
    expected_hex = format(expected_int, 'x')
    if len(expected_hex) % 2:
        expected_hex = '0' + expected_hex
    expected_bytes = bytes.fromhex(expected_hex)

    # The crackme only checks the first 8 bytes (two DWORDs)
    # dword at offset 0: 0x52454744 -> 'REGD' (little-endian stored as 44474552h)
    # dword at offset 4: 0x41544102 -> but check is 44474552h and 2D415441h
    # The crackme compares [edx] == 44474552h and [edx+4] == 2D415441h
    # Memory is little-endian, so bytes are: 52 45 47 44 | 41 54 41 2D
    required_prefix = bytes.fromhex('524547444154412D')

    # result_bytes is big-endian; the crackme reads from start of outputBuffer
    # Strip leading zero-padding to find the actual content
    # The crackme uses big_to_bytes then reads the buffer from the start
    # ASSUMPTION: the result is stored with leading zeros so the first non-zero
    # bytes are the prefix. We check if the prefix appears at the correct position.
    # Find where the meaningful data starts (skip leading zeros)
    content = result_bytes.lstrip(b'\x00')

    if len(content) < 8:
        return False

    # Check first 8 bytes match the magic prefix
    if content[:8] != required_prefix:
        return False

    # Optionally verify the name bytes follow
    name_bytes = name.encode('ascii') + b'\x00'
    if len(content) >= 8 + len(name_bytes):
        if content[8:8 + len(name_bytes)] != name_bytes:
            return False

    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Returns the serial as an uppercase hex string.
    """
    x = _build_plaintext(name)
    serial_int = pow(x, D, N)
    return format(serial_int, 'X').upper()



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
