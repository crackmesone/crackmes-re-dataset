#!/usr/bin/env python3
"""
Reverse-engineered keygen for 'simple_kgm_2_by_v3sa' by vesa.

Algorithm summary (from writeup):
1. ID field: GetDlgItemInt -> subtract 0xD4 -> store as dwID
2. Name: length must be >= 4 and <= 0x20
3. Checksum of name is computed; result must equal dwID  (i.e. ID == checksum + 0xD4)
4. Serial is treated as a big-number hex string; RSA verification is done:
     BigPowMod(serial_bignum, 0x10001, 0xF1CB476270EA27E9) == expected_value
   The expected_value is compared against szHexId (the 8-char ASCII-hex of the checksum)
   interpreted as a bignum.  The writeup is truncated so the exact final comparison
   is inferred but not fully confirmed.

NOTE: The modulus 0xF1CB476270EA27E9 is 64-bit, public exponent e=0x10001.
This looks like textbook RSA (no padding).  To sign (keygen), we need the private key d.
The modulus factors: we attempt to factor it to find d.
"""

import math

# RSA parameters from WM_INITDIALOG
MOD = 0xF1CB476270EA27E9   # n
PUB_EXP = 0x10001           # e

def checksum(name: str) -> int:
    """
    Reproduce the assembly checksum loop.

    Assembly logic (szName is 1-indexed via [edx+szName-1], edx starts at 1):
      esi = 0
      edx = 0
      ecx = 1
      edi = len(name)
      loop 31 times (ecx goes 1..31, increments BEFORE body use -> actually loop body runs while ecx != 0x20):
        edx++
        eax = name[edx-1]  (0-based)
        if edx == edi: edx = 0  (wrap-around)
        eax = eax + esi
        eax = eax << 4
        eax = eax + 0x10001
        eax = chk1(eax)   # ASSUMPTION: chk1 is a modular reduction or hash step
        esi = esi + eax
        ecx++
      result is eax (last value) and also compared to dwID

    ASSUMPTION: chk1(x) = x % MOD  (unknown - writeup does not fully describe chk1)
    The loop runs until ecx == 0x20 (32 iterations from ecx=1..0x1F, so 31 iterations).
    The name bytes are accessed cyclically.
    """
    name_bytes = [ord(c) for c in name]
    n = len(name_bytes)
    esi = 0
    edx = 0
    ecx = 1
    eax = 0
    while ecx != 0x20:
        edx += 1
        # [edx + szName - 1] with edx starting at 1 means name[edx-1] zero-based
        eax = name_bytes[(edx - 1) % n]
        if edx == n:
            edx = 0
        eax = (eax + esi) & 0xFFFFFFFF
        eax = (eax << 4) & 0xFFFFFFFF
        eax = (eax + 0x10001) & 0xFFFFFFFF
        # ASSUMPTION: chk1(x) = x (identity; the real chk1 function is not described)
        eax = chk1(eax)
        esi = (esi + eax) & 0xFFFFFFFF
        ecx += 1
    return eax

def chk1(x: int) -> int:
    # ASSUMPTION: chk1 is unknown. The writeup mentions it but does not describe it.
    # Possible candidates: identity, x & 0xFFFF, x % something.
    # Using identity as placeholder.
    return x & 0xFFFFFFFF

def compute_id(name: str) -> int:
    """Compute the ID that should be entered for a given name."""
    cs = checksum(name)
    return (cs + 0xD4) & 0xFFFFFFFF

def factor_modulus(n: int):
    """Try to factor n = p*q for the 64-bit RSA modulus."""
    # Try small factors first
    for p in range(2, 1000000):
        if n % p == 0:
            return p, n // p
    # ASSUMPTION: if not found by trial division, we cannot factor here
    return None, None

# Attempt to factor the modulus at import time
_p, _q = factor_modulus(MOD)
if _p is not None:
    _phi = (_p - 1) * (_q - 1)
    _d = pow(PUB_EXP, -1, _phi)   # modular inverse; Python 3.8+
else:
    _d = None  # ASSUMPTION: cannot compute private key without factoring

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    The serial S satisfies: pow(S, e, n) == M
    where M is the big-number representation of szHexId = '%08X' % checksum(name)

    To sign: S = pow(M, d, n)  (RSA private key operation)
    """
    if len(name) < 4 or len(name) > 0x20:
        raise ValueError('Name length must be 4..32')
    cs = checksum(name)
    hex_id = '%08X' % cs
    # The message M is szHexId interpreted as a hex big integer
    M = int(hex_id, 16)
    if _d is None:
        raise RuntimeError('Could not factor modulus; private key unknown. ASSUMPTION: factoring required.')
    S = pow(M, _d, MOD)
    return '%X' % S

def verify(name: str, serial: str) -> bool:
    """
    Verify name+serial pair.

    1. Name length: 4 <= len(name) <= 32
    2. Compute checksum of name
    3. Convert serial hex string -> bignum, compute pow(serial, 0x10001, MOD)
    4. Compare result to int(szHexId, 16) where szHexId = '%08X' % checksum

    ASSUMPTION: The final comparison target is int(szHexId, 16).
    The writeup is truncated and does not fully confirm this, but it is
    the most logical RSA verify conclusion.
    """
    if not name or not serial:
        return False
    if len(name) < 4 or len(name) > 0x20:
        return False
    cs = checksum(name)
    hex_id = '%08X' % cs
    M_expected = int(hex_id, 16)
    try:
        S = int(serial, 16)
    except ValueError:
        return False
    result = pow(S, PUB_EXP, MOD)
    return result == M_expected


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
