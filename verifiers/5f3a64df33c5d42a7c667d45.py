#!/usr/bin/env python3
"""
Keygen for virtual.1 by bagolymadar (Linux)

Serial format: LLPP-HHHHHHHHHHHHHHHH
  LL   = 2 hex digits: length of username
  PP   = 2 hex digits: sum of popcount of all username bytes
  -    = literal dash
  HHHH = 16 hex digits: transformed magic number

Algorithm (from multiple solutions in the writeup):
  magic = 0xb7e151628aed2a6a
  for each character c in username:
      pc = popcount(ord(c))  # number of set bits
      magic = rol64(magic, pc)
      if pc is odd:
          c_byte = (~ord(c)) & 0xff
      else:
          c_byte = ord(c)
      magic ^= c_byte
      magic &= 0xffffffffffffffff
  serial = f"{len(username):02X}{pop_sum:02X}-{magic:016X}"
"""


def popcount(n: int) -> int:
    """Count number of set bits in integer n."""
    return bin(n).count('1')


def rol64(value: int, count: int) -> int:
    """Rotate left 64-bit integer value by count bits."""
    count = count % 64
    value = value & 0xffffffffffffffff
    return ((value << count) | (value >> (64 - count))) & 0xffffffffffffffff


def compute_hash(name: str) -> int:
    """
    Compute the transformed magic number for the given username.
    Seed: 0xb7e151628aed2a6a (related to e's continued fraction / Euler's number)
    """
    h = 0xb7e151628aed2a6a
    for c in name:
        b = ord(c)
        pc = popcount(b)
        h = rol64(h, pc)
        if pc & 1:  # odd popcount -> NOT the byte
            b = (~b) & 0xff
        h ^= b
        h &= 0xffffffffffffffff
    return h


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.
    Returns serial string in format: LLPP-HHHHHHHHHHHHHHHH
    """
    if len(name) == 0 or len(name) > 255:
        raise ValueError("Username length must be between 1 and 255")

    length = len(name)
    pop_sum = sum(popcount(ord(c)) for c in name) & 0xff
    hash_val = compute_hash(name)
    return f"{length:02X}{pop_sum:02X}-{hash_val:016X}"


def verify(name: str, serial: str) -> bool:
    """
    Verify that the given serial is valid for the given username.

    Serial constraints (from the writeup):
      1. Serial must be exactly 21 characters long.
      2. First two chars (hex): length of username.
      3. Next two chars (hex): sum of popcount of all username bytes (mod 256).
      4. Fifth char: must be '-' (0x2d).
      5. Last 16 chars (hex): transformed magic number.
    """
    # Constraint 1: serial must be 21 characters
    if len(serial) != 21:
        return False

    # Constraint 4: fifth char must be '-'
    if serial[4] != '-':
        return False

    # Constraint 2: first two chars = hex length of username
    try:
        serial_len = int(serial[0:2], 16)
    except ValueError:
        return False
    if serial_len != len(name):
        return False

    # Constraint 3: next two chars = hex sum of popcount of all username bytes
    try:
        serial_popsum = int(serial[2:4], 16)
    except ValueError:
        return False
    expected_popsum = sum(popcount(ord(c)) for c in name) & 0xff
    if serial_popsum != expected_popsum:
        return False

    # Constraint 5: last 16 chars = hex transformed magic
    try:
        serial_hash = int(serial[5:21], 16)
    except ValueError:
        return False
    expected_hash = compute_hash(name)
    if serial_hash != expected_hash:
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
