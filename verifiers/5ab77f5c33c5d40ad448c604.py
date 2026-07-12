#!/usr/bin/env python3
"""
D_KeygenMe by DaXXoR_101 - keygen/verifier

Algorithm (from multiple writeups):
  1. Username must be > 4 chars (at least 5); truncated to 6 chars.
  2. Initialize a 64-bit accumulator: sto0 = 0x23E (574), sto1 = 0
  3. For each character c in username[:6]:
       a. eax = ord(c) // 5  (integer division, quotient)
       b. ebx = eax
       c. ecx = ebx >> 0x1F  (arithmetic shift right 31, sign extension -> 0 for positive)
       d. eax_old = sto0
       e. edx_old = sto1
       f. ecx = ecx * sto0
       g. edx_old = edx_old * ebx
       h. ecx = ecx + edx_old
       i. [edx:eax] = sto0 * ebx  (mul ebx, unsigned 64-bit result)
       j. edx = edx + ecx
       k. sto0 = eax  (low 32 bits of product)
       l. sto1 = edx
       m. edi = ord(c)
       n. edx2 = edi >> 0x1F  (0 for printable chars)
       o. sto0 = (sto0 + edi) & 0xFFFFFFFF
       p. sto1 = (sto1 + edx2) & 0xFFFFFFFF
  4. Serial = str(sto0)  (decimal representation of low 32-bit value)

Note: Solution 4 (Kreet/dkeygen.c) uses a simpler model that ignores the 64-bit
      high word (sto1) and just uses int overflow, but the more complete
      analysis from solutions 1 and 2 shows the 64-bit pair. The final serial
      is always sto0 (the low 32-bit word), so both approaches agree for
      the serial output.
"""

import ctypes


def _compute(name: str):
    """Core serial computation. Returns (sto0, sto1) as 32-bit unsigned ints."""
    # Truncate to 6 characters
    name = name[:6]

    sto0 = 0x23E  # 574
    sto1 = 0

    for ch in name:
        c = ord(ch)

        # eax = c // 5 (integer division)
        eax = c // 5
        ebx = eax

        # ecx = ebx >> 31 (arithmetic, sign extension; 0 for positive quotients)
        ecx = ebx >> 31  # Python ints are arbitrary precision, so this is fine
        # For positive ebx, ecx = 0; for negative, ecx = -1 (all 1s in 32-bit)
        # Mask to 32-bit signed interpretation
        ecx = ecx & 0xFFFFFFFF

        # imul ecx, sto0  (signed 32-bit multiply, keep low 32 bits)
        ecx = (ecx * sto0) & 0xFFFFFFFF

        # imul edx, ebx  where edx = sto1
        edx = (sto1 * ebx) & 0xFFFFFFFF

        # add ecx, edx
        ecx = (ecx + edx) & 0xFFFFFFFF

        # mul ebx: unsigned multiply eax=sto0 by ebx, 64-bit result
        product = sto0 * ebx  # sto0 is already low 32-bit
        new_eax = product & 0xFFFFFFFF
        new_edx = (product >> 32) & 0xFFFFFFFF

        # add edx, ecx
        new_edx = (new_edx + ecx) & 0xFFFFFFFF

        sto0 = new_eax
        sto1 = new_edx

        # add sto0, ord(c)
        edi = c
        edx2 = (edi >> 31) & 0xFFFFFFFF  # 0 for printable ASCII

        sto0 = (sto0 + edi) & 0xFFFFFFFF
        sto1 = (sto1 + edx2) & 0xFFFFFFFF

    return sto0, sto1


def keygen(name: str) -> str:
    """Generate a valid serial for the given username."""
    if len(name) < 5:
        raise ValueError("Username must be at least 5 characters long.")
    # Truncation warning
    if len(name) > 6:
        name = name[:6]
    sto0, sto1 = _compute(name)
    return str(sto0)


def verify(name: str, serial: str) -> bool:
    """Verify that serial matches the expected serial for name."""
    if len(name) < 5:
        return False
    expected = keygen(name)
    return serial.strip() == expected



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
