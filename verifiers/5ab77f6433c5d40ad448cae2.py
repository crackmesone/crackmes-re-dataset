#!/usr/bin/env python3
"""
Shmoocon 2011 Crypto Challenge Pack - warmup.py reconstruction

Based on the writeup, the warmup challenge uses 10 'rotor' strings.
The serial is found via the Chinese Remainder Theorem (CRT).

validation:
  - name is truncated/padded to 10 chars (pad char = 'S')
  - for each of 10 rotors, find rotation amount r_i = rotors[i].find(name[i])
  - serial S satisfies S mod len(rotors[i]) == r_i for all i
  - check: name == check and serial > 139 and serial < 421336842070675358939

NOTE: The actual rotor strings (rotor0..rotor9) are NOT given in the writeup.
We reconstruct the algorithm structure only; rotor strings are ASSUMED below.
"""

from functools import reduce
import math

# ASSUMPTION: The actual rotor strings are not provided in the writeup.
# These are placeholder stubs. Replace with the actual strings from warmup.py.
ROTORS = [
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#",  # rotor0
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#",  # rotor1
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#",  # rotor2
    "!@#0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",  # rotor3
    "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210!@#",  # rotor4
    "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210!@#",  # rotor5
    "9876543210ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba!@#",  # rotor6
    "#@!9876543210ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba",  # rotor7
    "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789!@#",  # rotor8
    "ZzYyXxWwVvUuTtSsRrQqPpOoNnMmLlKkJjIiHhGgFfEeDdCcBbAa9876543210!@#",  # rotor9
]


def normalize_name(name: str) -> str:
    """Truncate to 10 chars or pad with 'S' to length 10."""
    if len(name) > 10:
        return name[:10]
    while len(name) < 10:
        name = name + 'S'
    return name


def rol_string(s: str, amount: int) -> str:
    """Rotate string left by amount positions."""
    width = len(s)
    amount = amount % width
    for _ in range(amount):
        s = s[1:width] + s[0]
    return s


def extended_gcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x


def modinv(a: int, m: int) -> int:
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f"No modular inverse for {a} mod {m}")
    return x % m


def crt(remainders, moduli):
    """Chinese Remainder Theorem."""
    L = 1
    for m in moduli:
        L *= m
    S = 0
    for r_i, l_i in zip(remainders, moduli):
        L_i = L // l_i
        v_i = modinv(L_i, l_i)
        S += r_i * v_i * L_i
    return S % L


def keygen(name: str) -> int:
    """Generate a valid serial for the given name using CRT."""
    norm = normalize_name(name)
    rotors = ROTORS
    rot = []
    for i in range(10):
        idx = rotors[i].find(norm[i])
        if idx == -1:
            raise ValueError(
                f"Character '{norm[i]}' not found in rotor {i}. "
                "Actual rotor strings needed."
            )
        rot.append(idx)
    moduli = [len(rotors[i]) for i in range(10)]
    serial = crt(rot, moduli)
    # The check requires serial > 139; if the base CRT solution is too small,
    # add the LCM until it's in range.
    L = 1
    for m in moduli:
        L = L * m // math.gcd(L, m)  # LCM
    SERIAL_MAX = 421336842070675358939
    while serial <= 139:
        serial += L
    if serial >= SERIAL_MAX:
        raise ValueError("No valid serial found in required range")
    return serial


def verify(name: str, serial) -> bool:
    """Verify name/serial pair."""
    norm = normalize_name(name)
    rotors = ROTORS

    # Check bounds
    serial = int(serial)
    if not (serial > 139 and serial < 421336842070675358939):
        return False

    # For each rotor, rotate by serial mod len(rotor) and check first char == name[i]
    check_chars = []
    for i in range(10):
        amount = serial % len(rotors[i])
        rotated = rol_string(rotors[i], amount)
        check_chars.append(rotated[0])

    check = ''.join(check_chars)
    return norm == check



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
