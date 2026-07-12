#!/usr/bin/python3
"""
Timotei Crackme #9 - Serial Verification and Keygen

Algorithm (from writeup):
1. Read serial string (max 50 chars, including null => max 49 usable)
2. serial length must be > 0
3. atoi(serial) must be >= 2023 (0x7E7)
4. Scan serial for 'CM' at a WORD (2-byte) boundary (even index): serial[0], serial[2], serial[4], ...
5. Compute checksum:
     sum = atoi(serial)
     for each char in serial:
         sum += (ord(char) + 123456)
   Equivalently: sum = atoi(serial) + 123456 * len(serial) + sum_of_ascii_values
6. sum % atoi(serial) == 0  =>  valid

Note on 'CM' position: repne scasw scans word-by-word starting at edi (start of serial),
so 'CM' must start at an even index: 0, 2, 4, 6, ...
But atoi(serial) >= 2023 means at least 4 leading digits, so 'CM' at index 0 or 2 would
not allow 4 leading digits unless digits appear after CM. Since atoi stops at first non-digit,
'CM' must come AFTER the leading digits. With 4 leading digits (indices 0-3), 'CM' can start
at index 4 (even). With more digits, it can be at index 4, 6, 8, etc.
"""

import ctypes
import itertools
import string


def _atoi(s):
    """Mimics C atoi: skip leading whitespace, read optional sign, read digits."""
    i = 0
    n = len(s)
    # skip leading whitespace
    while i < n and s[i] in ' \t\n\r\x0b\x0c':
        i += 1
    if i == n:
        return 0
    sign = 1
    if s[i] == '-':
        sign = -1
        i += 1
    elif s[i] == '+':
        i += 1
    result = 0
    while i < n and s[i].isdigit():
        result = result * 10 + int(s[i])
        i += 1
    # C int overflow (32-bit)
    result = sign * result
    result = ctypes.c_int32(result).value
    return result


def _checksum(serial):
    """
    Compute the checksum as described:
      ecx starts as atoi(serial)
      for each char: ecx += (char + 0x1E240)   [0x1E240 = 123456 decimal]
      => sum = atoi(serial) + sum_over_chars(ord(c) + 123456)
      => sum = atoi(serial) + 123456 * len(serial) + sum(ord(c) for c in serial)
    Uses 32-bit unsigned arithmetic for the accumulator (ecx is 32-bit register).
    """
    ecx = ctypes.c_uint32(_atoi(serial)).value
    for c in serial:
        ebx = ctypes.c_int32(ord(c) + 0x1E240).value
        ecx = ctypes.c_uint32(ecx + ebx).value
    return ecx


def _find_cm_even(serial):
    """
    Mimics 'repne scasw' scanning for word 0x4D43 ('CM' in little-endian, i.e., 'C'=0x43, 'M'=0x4D)
    repne scasw compares ax (0x4D43) with word at [edi], edi advances by 2 each time.
    So it checks serial[0:2], serial[2:4], serial[4:6], ...
    ecx starts as strlen(serial) and counts down; repne scasw decrements ecx by 1 per iteration
    but moves edi by 2. Actually repne scasw uses ecx as the count and scans cx words max.
    
    Correction: repne scasw uses ecx as count of WORDS to scan, and edi advances 2 bytes per step.
    ecx was set to strlen(serial) before the scan.
    So it scans at most strlen(serial) words? Actually ecx = strlen gives us strlen iterations,
    scanning bytes 0..1, 2..3, 4..5, ... up to 2*(strlen-1) bytes in.
    
    The key point: 'CM' must appear at an even byte offset in the serial.
    """
    for i in range(0, len(serial) - 1, 2):
        if serial[i] == 'C' and serial[i+1] == 'M':
            return True
    return False


def verify(name, serial):
    """
    Verify a serial. Note: this crackme does NOT use a name, only a serial.
    The 'name' parameter is included for API consistency but is unused.
    """
    # Length check
    if len(serial) == 0:
        return False
    if len(serial) > 49:  # max 49 usable chars (50 buffer - null terminator)
        return False

    # atoi must be >= 2023
    val = _atoi(serial)
    if val < 2023:
        return False

    # 'CM' must appear at an even index
    if not _find_cm_even(serial):
        return False

    # Checksum must be divisible by atoi(serial)
    chk = _checksum(serial)
    if chk % ctypes.c_uint32(val).value != 0:
        return False

    return True


def keygen(name=None):
    """
    Generate valid serials.
    Strategy:
      - Pick a number of leading digit count (4, 5, 6, ...)
      - Serial format: NNNN + 'CM' + extra_chars
      - 'CM' at even position: with 4 leading digits (indices 0-3), CM starts at index 4 (even). Good.
        With 5 leading digits (indices 0-4), CM starts at index 5 (odd). Bad unless we add padding.
        So we use even numbers of leading digits: 4, 6, 8, ...
        OR odd digit counts with an adjustment character before CM to make CM land on even index.
      - Simplest: 4-digit prefix + 'CM' (CM at index 4, even). Then find extra chars to make checksum divisible.
    
    For format 'DDDDCM' (6 chars, 4 digits + CM):
      sum = N + 123456*6 + sum_of_ascii('D','D','D','D','C','M')
      where N = atoi(serial) = the 4-digit number
      ascii sum of 'CM' = 67 + 77 = 144
      ascii sum of digits = sum of digit chars
      sum = N + 740736 + digit_ascii_sum + 144
      We need sum % N == 0, i.e., sum = k*N for some integer k.
      sum = N + 740880 + digit_ascii_sum
      digit_ascii_sum = sum of ascii codes of the 4 digit characters
      For number N with digits d1 d2 d3 d4: digit_ascii_sum = (d1+d2+d3+d4) + 4*48
      = digit_sum(N) + 192
      sum = N + 740880 + digit_sum(N) + 192
            = N + 741072 + digit_sum(N)
      Need: (N + 741072 + digit_sum(N)) % N == 0
      => (741072 + digit_sum(N)) % N == 0
    """
    # Try 4-digit prefix + 'CM' format
    for N in range(2023, 10000):
        s = str(N) + 'CM'
        if len(str(N)) != 4:
            continue
        if verify(None, s):
            yield s

    # Try format: DDDDCM + extra printable chars (to satisfy divisibility)
    printable = [c for c in string.printable if c not in string.whitespace and c != '\x00']
    
    for N in range(2023, 10000):
        prefix = str(N)
        if len(prefix) != 4:
            continue
        # Try adding 1 printable char after CM
        base = prefix + 'CM'
        base_sum = _checksum(base)  # sum without extra char contribution factored in
        # We want (checksum(base + c)) % N == 0
        # checksum(base+c) = checksum(base) + ord(c) + 123456
        target_mod = (ctypes.c_uint32(N).value)  # already >= 2023, fits in 32-bit
        for c in printable:
            s = base + c
            if verify(None, s):
                yield s
                break  # one per N is enough for demonstration



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
            print(_sv)
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
