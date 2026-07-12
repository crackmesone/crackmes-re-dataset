# Reverse-engineered keygen for bug_crypto_crackme by black_eye
# Based on the partial source code provided in the writeup.
# The keygen uses:
#   - MD5 of the name
#   - RC4 stream cipher
#   - Continued fractions (convergents)
#   - MIRACL big-number library (for RSA/crypto operations)
# The main.cpp was truncated, so the exact serial format and validation
# steps are PARTIALLY recovered.

import hashlib
import struct

# ---------------------------------------------------------------------------
# RC4 implementation (rc4.cpp referenced in project)
# ---------------------------------------------------------------------------

def rc4(key: bytes, data: bytes) -> bytes:
    """Standard RC4 stream cipher."""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(byte ^ S[(S[i] + S[j]) % 256])
    return bytes(out)

# ---------------------------------------------------------------------------
# MD5 helper
# ---------------------------------------------------------------------------

def md5_of_name(name: str) -> bytes:
    return hashlib.md5(name.encode('ascii')).digest()  # 16 bytes

# ---------------------------------------------------------------------------
# Continued fraction convergents (from Fraction.h)
# ---------------------------------------------------------------------------

def continued_fraction(numer: int, denom: int):
    """
    Returns lists: quotients, convergent numerators, convergent denominators.
    Directly translated from ContinuedFraction<Integer>::ContinuedFraction.
    """
    N, D = numer, denom
    a = N // D

    p = [a, 1]   # p[0]=a, p[1]=1  (index 0 = current, 1 = previous)
    q = [1, 0]   # q[0]=1, q[1]=0

    quotients = [a]
    conv_numer = [p[0]]
    conv_denom = [q[0]]

    while True:
        temp = N % D
        N = D
        D = temp
        if D == 0:
            break
        a = N // D

        temp = a * p[0] + p[1]
        p[1] = p[0]
        p[0] = temp

        temp = a * q[0] + q[1]
        q[1] = q[0]
        q[0] = temp

        quotients.append(a)
        conv_numer.append(p[0])
        conv_denom.append(q[0])

    return quotients, conv_numer, conv_denom

# ---------------------------------------------------------------------------
# ASSUMPTION: The crackme derives a 32-bit or 64-bit 'key number' from the
# name's MD5 hash, then uses continued fractions on that number (perhaps
# ratio of two halves of the MD5) to produce convergents, and RC4-encrypts
# a value derived from the convergents to produce the serial.
# The exact serial format (length, encoding, separators) is unknown because
# main.cpp was truncated.
# ---------------------------------------------------------------------------

def derive_key_number(name: str):
    """Derive two integers from the MD5 of name."""
    digest = md5_of_name(name)
    # ASSUMPTION: split MD5 into two 8-byte (64-bit) halves
    hi = int.from_bytes(digest[:8], 'little')
    lo = int.from_bytes(digest[8:], 'little')
    if lo == 0:
        lo = 1  # avoid division by zero
    return hi, lo

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: Algorithm is partially reconstructed. May not match the
    actual crackme's expected serial format.
    """
    hi, lo = derive_key_number(name)

    # Ensure numer >= denom for a meaningful continued fraction
    numer, denom = (hi, lo) if hi >= lo else (lo, hi)
    if denom == 0:
        denom = 1

    quotients, conv_numer, conv_denom = continued_fraction(numer, denom)

    # ASSUMPTION: use the last convergent numerator/denominator as the serial basis
    last_p = conv_numer[-1]
    last_q = conv_denom[-1]

    # ASSUMPTION: RC4-encrypt the convergent value using the MD5 as key
    key = md5_of_name(name)
    plain = struct.pack('<QQ', last_p % (2**64), last_q % (2**64))
    cipher = rc4(key, plain)

    # ASSUMPTION: serial is the hex encoding of the RC4 output, uppercased
    serial = cipher.hex().upper()
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: Compare generated serial against provided serial (case-insensitive).
    This is a placeholder; the real check logic from main.cpp is unknown.
    """
    expected = keygen(name)
    return serial.strip().upper() == expected.upper()

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


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
