#!/usr/bin/env python3
"""
Keygen/verify for demeter_keygenme by _J_

Algorithm (from writeup):
1. Hash the username buffer three times with func_0040B6B0 (a custom hash,
   ripped from the crackme; see ASSUMPTION below).
   - hash0 -> used to find prime p (increment until prime)
   - hash1 -> used to find prime q (increment until prime)
   - hash2 -> the message to encrypt
2. e = byte-reversed volume serial number, incremented until prime
   (machine-specific; ASSUMPTION: we cannot reproduce this without the actual
    volume serial, so we use a placeholder or require it as input)
3. m = p * q
4. phi = (p-1)*(q-1)
5. d = modular inverse of e mod phi
6. serial = hash2 ^ e (mod m)   [RSA encryption]

Verification (what the crackme does):
   serial ^ d (mod m) == hash2
   which is equivalent to:
   serial ^ e (mod m) should equal hash2, so we verify:
   serial_int ^ d (mod m) == hash2_int

NOTE: func_0040B6B0 is a custom hash function ripped from the binary.
      From the rips.cpp we can see it uses 64-byte internal state and
      hashdata1 (which starts 0x80, 0x00, ...).  This looks like a
      SHA-256 (or similar) padding block appended, suggesting it may be
      a custom Haval/MD5/SHA variant.  Without the full assembly we
      ASSUME it is SHA-256 applied iteratively, updating a 64-byte buffer
      each call.
"""

import hashlib
from sympy import isprime, nextprime
from sympy import mod_inverse


# ASSUMPTION: func_0040B6B0 is a custom hash that transforms a 64-byte
# buffer in-place and the first 32 bytes of the result are used as a
# 256-bit big-endian integer.  We model it as SHA-256 of the current
# buffer content (first meaningful bytes), writing result back into
# buffer[0:32].  This is a GUESS; the real function is a ripped asm routine.

def func_0040B6B0_approx(buf: bytearray) -> None:
    """
    ASSUMPTION: approximation of the custom hash function.
    Takes a 64-byte bytearray, hashes its content with SHA-256,
    writes the 32-byte digest back into buf[0:32].
    """
    digest = hashlib.sha256(bytes(buf)).digest()
    buf[0:32] = digest
    # upper 32 bytes zeroed as per the hashdata1 pattern seen in rips.cpp
    buf[32:64] = b'\x00' * 32


def compute_hashes(name: str):
    """
    Compute hash0, hash1, hash2 from the username.
    Returns (hash0_int, hash1_int, hash2_int) as Python integers.
    """
    buf = bytearray(64)
    name_bytes = name.encode('ascii', errors='replace')[:64]
    buf[:len(name_bytes)] = name_bytes

    func_0040B6B0_approx(buf)
    hash0 = int.from_bytes(buf[:32], 'big')

    func_0040B6B0_approx(buf)
    hash1 = int.from_bytes(buf[:32], 'big')

    func_0040B6B0_approx(buf)
    hash2 = int.from_bytes(buf[:32], 'big')

    return hash0, hash1, hash2


def compute_rsa_params(name: str, volume_serial: int):
    """
    Compute RSA parameters from name and volume serial.
    volume_serial: 32-bit integer (byte-reversed DWORD from GetVolumeInformation)
    Returns (p, q, e, m, phi, d, hash2)
    """
    hash0, hash1, hash2_int = compute_hashes(name)

    # Find primes p, q by incrementing from hash values
    p = nextprime(hash0 - 1)  # nextprime finds smallest prime >= hash0
    q = nextprime(hash1 - 1)

    # e from volume serial (already byte-reversed in the C code)
    # byte-reverse the 4-byte volume serial
    vs_bytes = volume_serial.to_bytes(4, 'big')
    vs_reversed = bytes([vs_bytes[3], vs_bytes[2], vs_bytes[1], vs_bytes[0]])
    e_start = int.from_bytes(vs_reversed, 'big')
    e = nextprime(e_start - 1)

    m = p * q
    phi = (p - 1) * (q - 1)

    # d = modular inverse of e mod phi
    d = mod_inverse(e, phi)

    return p, q, e, m, phi, d, hash2_int


def keygen(name: str, volume_serial: int = 0x12345678) -> str:
    """
    Generate serial for given name and volume serial.
    volume_serial: the raw DWORD from GetVolumeInformation (before byte-swap).
    ASSUMPTION: volume serial defaults to a placeholder; real keygen needs
    the actual volume serial of the target machine.
    """
    p, q, e, m, phi, d, hash2_int = compute_rsa_params(name, volume_serial)

    # serial = hash2 ^ e (mod m)
    serial_int = pow(hash2_int, e, m)
    return format(serial_int, 'X').upper()


def verify(name: str, serial: str, volume_serial: int = 0x12345678) -> bool:
    """
    Verify that serial is valid for name.
    The crackme checks: serial ^ d (mod m) == hash2
    ASSUMPTION: volume serial must match the machine's value.
    """
    try:
        serial_int = int(serial.strip(), 16)
    except ValueError:
        return False

    p, q, e, m, phi, d, hash2_int = compute_rsa_params(name, volume_serial)

    # Decrypt serial: serial ^ d (mod m)
    decrypted = pow(serial_int, d, m)
    return decrypted == hash2_int



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
