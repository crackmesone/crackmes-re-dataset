#!/usr/bin/env python3
"""
Reverse-engineered keygen/verifier for lagalopex' cm3 crackme.

The keyfile is a binary file located at ~/.key_<username>
It contains 20 pairs of 32-bit little-endian integers (x_i, y_i), 160 bytes total.

For each pair i (0..19):
  Let x = x_i, y = y_i, s = x + y
  Constraints (all must hold):
    1. x > 0
    2. y > x  (gs check: x > 0 and y > x)
    3. gcd(x, y) == 1  (gcd1)
    4. gcd(x, s) == 1  (gcd2)
    5. gcd(y, s) == 1  (gcd3)
    6. rad(x * y * s) < s  (rad check)
    7. x // 19 + y // 94 == hashcode[i]  (calc check, where hashcode = RIPEMD-160(homedir + '/.key_' + username + '_0'))

Note: The keyfile path used for hashing includes '_0' suffix:
  hash_input = homedir + '/.key_' + username + '_0'
  hashcode = RIPEMD160(hash_input)  -> 20 bytes, one per pair

The keyfile itself is written to: homedir + '/.key_' + username
"""

import struct
import os
import math
from hashlib import new as hashlib_new


def ripemd160(data: bytes) -> bytes:
    """Compute RIPEMD-160 hash."""
    try:
        h = hashlib_new('ripemd160')
        h.update(data)
        return h.digest()
    except ValueError:
        # ASSUMPTION: If ripemd160 not available, fall back - this should not happen on standard OpenSSL builds
        raise RuntimeError("RIPEMD-160 not available in this Python/OpenSSL build")


def gcd(a: int, b: int) -> int:
    """Standard GCD."""
    while b:
        a, b = b, a % b
    return a


def rad(n: int) -> int:
    """
    Radical of n: product of distinct prime factors of n.
    Matches the rad_() function from the disassembly:
      result = 1
      for x4 = 2 to n:
        if n % x4 == 0:
          result *= x4
          while n % x4 == 0: n //= x4
      return result
    """
    if n <= 1:
        return n
    result = 1
    temp = n
    x4 = 2
    while x4 <= temp:
        if temp % x4 == 0:
            result *= x4
            while temp % x4 == 0:
                temp //= x4
        x4 += 1
    return result


def rad_fast(n: int) -> int:
    """Faster version of rad using trial division."""
    if n <= 1:
        return n
    result = 1
    temp = n
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            result *= d
            while temp % d == 0:
                temp //= d
        d += 1
    if temp > 1:
        result *= temp
    return result


def verify_pair(x: int, y: int, target_byte: int) -> bool:
    """
    Verify a single (x, y) pair against its target hash byte.
    """
    if x <= 0:
        return False
    s = x + y
    # gs: x > 0 and y > x
    if not (y > x):
        return False
    # gcd1: gcd(x, y) == 1
    if gcd(x, y) != 1:
        return False
    # gcd2: gcd(x, s) == 1
    if gcd(x, s) != 1:
        return False
    # gcd3: gcd(y, s) == 1
    if gcd(y, s) != 1:
        return False
    # rad check: rad(x*y*s) < s
    if rad_fast(x * y * s) >= s:
        return False
    # calc check: x//19 + y//94 == target_byte
    if (x // 19 + y // 94) != target_byte:
        return False
    return True


def get_hash_input(username: str, homedir: str = None) -> bytes:
    """
    Build the hash input string: homedir/.key_username_0
    """
    if homedir is None:
        homedir = os.path.expanduser('~')
    hash_str = f"{homedir}/.key_{username}_0"
    return hash_str.encode('ascii')


def get_hashcode(username: str, homedir: str = None) -> bytes:
    """
    Compute the 20-byte RIPEMD-160 hash used for key validation.
    """
    data = get_hash_input(username, homedir)
    return ripemd160(data)


def verify(username: str, keyfile_bytes: bytes, homedir: str = None) -> bool:
    """
    Verify the keyfile contents for the given username.
    keyfile_bytes: raw bytes read from ~/.key_<username> (must be >= 160 bytes)
    """
    if len(keyfile_bytes) < 160:
        return False
    hashcode = get_hashcode(username, homedir)
    for i in range(20):
        offset = i * 8
        x = struct.unpack_from('<I', keyfile_bytes, offset)[0]
        y = struct.unpack_from('<I', keyfile_bytes, offset + 4)[0]
        if not verify_pair(x, y, hashcode[i]):
            return False
    return True


def solve_pair(target_byte: int):
    """
    Find (x, y) satisfying all constraints for one pair with given target_byte.
    Strategy from keygen.c:
      For x stepping by 19:
        d = target_byte - x//19
        y_base = d * 94
        if y_base > 0 and y_base > x:
          try y in [y_base, y_base+94) stepped by 1,
          with multiplier k stepping by 256.
    """
    for x_base in range(1, 0x7fffffff, 19):
        d = target_byte - x_base // 19
        if d <= 0:
            continue
        y_base_calc = d * 94
        if y_base_calc <= 0 or y_base_calc <= x_base:
            continue
        # Try different x values near x_base
        for x in range(x_base, x_base + 19):
            if x == 0:
                continue
            # Try k multipliers
            for k in range(1, 0x7FFFFF, 256):
                y_start = k * y_base_calc
                for y in range(y_start, y_start + 94):
                    # skip if both even
                    if (x % 2 == 0) and (y % 2 == 0):
                        continue
                    if y <= x:
                        continue
                    s = x + y
                    if gcd(x, y) != 1:
                        continue
                    if gcd(x, s) != 1:
                        continue
                    if gcd(y, s) != 1:
                        continue
                    if rad_fast(x * y * s) >= s:
                        continue
                    # Check calc constraint
                    if (x // 19 + y // 94) != target_byte:
                        continue
                    return (x, y)
    return None


def keygen(username: str, homedir: str = None) -> bytes:
    """
    Generate keyfile bytes for the given username.
    Returns 160 bytes to be written to ~/.key_<username>
    """
    hashcode = get_hashcode(username, homedir)
    result = b''
    for i in range(20):
        target = hashcode[i]
        pair = solve_pair(target)
        if pair is None:
            raise RuntimeError(f"Could not find valid pair for index {i}, target={target}")
        x, y = pair
        result += struct.pack('<II', x, y)
    return result

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
