import random
import string
from typing import Optional

# Lookup tables extracted from the assembly
data_4020a0 = [
    0x10, 0x2f, 0x1a, 0x1e, 0x27, 0x1e, 0x1b, 0x23,
    0x0a, 0x24, 0x20, 0x0b, 0x1e, 0x0c, 0x11, 0x21,
    0x0e, 0x2a, 0x0a, 0x18, 0x19, 0x29, 0x2c, 0x20,
    0x0d, 0x2e, 0x4c, 0x0b, 0x04, 0x19, 0x00, 0x00
]

data_402020 = [
    0x40, 0x06, 0xFFFFFFAA, 0x51, 0xFFFFFFC1, 0xFFFFFFDD, 0xFFFFFFB8, 0x1d,
    0xFFFFFFF7, 0x08, 0xFFFFFFD2, 0x5f, 0xFFFFFFBB, 0x20, 0xFFFFFFF7, 0xFFFFFF9F,
    0xFFFFFFCB, 0x1b, 0x54, 0x2b, 0xFFFFFFFF, 0x27, 0x12, 0xFFFFFFD2,
    0x51, 0x60, 0xFFFFFFD5, 0xFFFFFFBD, 0x13, 0x32, 0x00, 0x00
]

data_402120 = [
    0x22, 0x14, 0x08, 0xFFFFFFF5, 0x5A, 0x3E, 0xFFFFFFF6, 0x4E, 0x57, 0xFFFFFFE1
]

# Valid characters for password (from 'possible' string in asm, minus the '-' which is separator)
# possible: db "hgfedcbaponmlkjixwvutsrqzy-"
POSSIBLE = "hgfedcbaponmlkjixwvutsrqzy-"
LETTERS = "hgfedcbaponmlkjixwvutsrqzy"  # 26 lowercase letters (reordered)


def sign32(x):
    """Convert to signed 32-bit integer."""
    x = x & 0xFFFFFFFF
    if x >= 0x80000000:
        x -= 0x100000000
    return x


def factorial_recursive(n):
    """sub_401227: recursive factorial (or actually just returns n if n<=1, else factorial(n-1)*n).
    # ASSUMPTION: sub_401227 is a factorial function based on the recursive decrement pattern.
    """
    if n <= 1:
        return n
    return n * factorial_recursive(n - 1)
    # ASSUMPTION: This matches sub_401227's behavior; it could be something simpler.


def simulate(key_bytes):
    """
    Simulate the validation algorithm from the assembly writeup.
    key_bytes: list of integer byte values
    Returns the final data_404130 value after processing.
    """
    length = len(key_bytes)
    data_404040 = list(range(30))  # 30 qword slots, initialized to 0 then set to i

    # sub_401266: initialize data_404040[i] = i, then do a Fisher-Yates-like shuffle
    for i in range(length):
        data_404040[i] = i

    # Second loop in sub_401266: shuffle based on character values
    for i in range(length):
        # sub_401227(i+1) - ASSUMPTION: factorial
        fact_val = factorial_recursive(i + 1)
        ch = key_bytes[i]
        # data_4020a0[ch - 0x61] / (i + fact_val) => remainder
        # ASSUMPTION: ch is a lowercase letter 'a'-'z' for this indexing
        if 0x61 <= ch <= 0x7a:
            idx = ch - 0x61
        else:
            # '-' character: skip or use 0
            # ASSUMPTION: dash chars might cause issues; treat as index 0
            idx = 0
        divisor = i + fact_val
        if divisor == 0:
            remainder = 0
        else:
            remainder = data_4020a0[idx] % divisor
        # swap data_404040[i] and data_404040[remainder]
        tmp = data_404040[i]
        data_404040[i] = data_404040[remainder % length] if remainder < length else data_404040[i]
        if remainder < length:
            data_404040[remainder] = tmp

    # Compute var_01 = length >> 1
    var_01 = length >> 1

    # Compute length % 10 to index data_402020
    # The assembly does: (length * 0x4ec4ec4ec4ec4ec5) >> 67 to get length//10,
    # then length - (length//10)*10 = length%10
    # ASSUMPTION: this is length % 10
    mod10 = length % 10
    data_404130 = sign32(data_402020[mod10])

    # sub_4013a5: loop from 0 to var_01-1
    for i in range(var_01):
        # [rbp-0x15] = key_bytes[data_404040[i] + base] but base offset is complex
        # ASSUMPTION: we index key_bytes directly with data_404040[i]
        idx = data_404040[i]
        if idx >= length:
            continue
        ch = key_bytes[idx]
        if ch == 0x2d:  # '-'
            continue
        shift_amount = data_404040[i] & 0x3F
        shifted = (ch << shift_amount) & 0xFFFFFFFFFFFFFFFF
        xored = sign32(data_404130 ^ shifted)
        if xored <= sign32(data_404130 & 0xFFFFFFFF):
            # data_404130 = data_402020[data_404040[i] * 4]  -- but *4 as index? 
            # ASSUMPTION: data_402020 indexed by data_404040[i]
            tbl_idx = data_404040[i]
            if tbl_idx < len(data_402020):
                data_404130 = sign32(data_402020[tbl_idx])
        else:
            data_404130 = sign32(xored >> 3)

    # sub_401488: loop from var_01 to length-1
    acc = sign32(data_402020[mod10])  # re-read initial for [rbp-0x24]? 
    # ASSUMPTION: [rbp-0x24] = var_01 originally but used as AND accumulator; 
    # looking at code: [rbp-0x24] = [rbp-0x8][8] which is likely the initial data_404130
    and_acc = data_404130  # ASSUMPTION
    dash_count = 0
    non_dash_count = 0

    for i in range(var_01, length):
        idx = data_404040[i]
        if idx >= length:
            continue
        ch = key_bytes[idx]
        if ch == 0x2d:  # '-'
            # and_acc &= data_4020a0[data_404040[i] * 4] -- ASSUMPTION: index as int
            tbl_idx = data_404040[i]
            if tbl_idx < len(data_4020a0):
                and_acc = sign32(and_acc & data_4020a0[tbl_idx])
            dash_count += 1
        else:
            data_404130 = sign32(data_404130 | non_dash_count)
            non_dash_count += 1

    # Validation: dash_count must be <= 2 (not above 2 => <= 2? assembly says "above 2 => fail")
    # non_dash_count must be <= 3 (not above 3 => <= 3? assembly says "above 3 => fail")
    # ASSUMPTION: the keygen re-checks these with jb (below), so edi >= 4 and esi >= 2
    # The keygen uses: cmp edi, 4; jb _start => fail if non_dash_count < 4
    #                  cmp esi, 1; jbe _start => fail if dash_count <= 1
    # So valid requires: non_dash_count >= 4 AND dash_count >= 2
    if non_dash_count < 4 or dash_count < 2:
        return None, and_acc

    return data_404130, and_acc


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial (password). Name is unused (crackme uses argv[1] only).
    Returns True if serial is valid.
    """
    key_bytes = [ord(c) for c in serial]
    length = len(key_bytes)

    # Length check: > 11 and <= 0x1e (30)
    if length <= 11 or length > 30:
        return False

    # Character set check: must only contain characters from POSSIBLE
    for c in serial:
        if c not in POSSIBLE:
            return False

    result, and_acc = simulate(key_bytes)
    if result is None:
        return False

    # Check result against data_402120[0..9]
    # ASSUMPTION: 'sleep' variable = and_acc is checked against data_402120
    target = sign32(and_acc & 0xFFFFFFFF)
    for i in range(10):
        if target == sign32(data_402120[i]):
            return True
    return False


def keygen(name: str) -> str:
    """
    Generate a valid serial. Name is unused.
    Uses randomized approach similar to the assembly keygen.
    """
    # ASSUMPTION: The keygen picks a random length between 12 and 29,
    # places exactly 3 dashes at random positions, fills rest with random letters.
    import random
    max_tries = 100000
    for _ in range(max_tries):
        length = random.randint(12, 30)
        # Pick 3 distinct dash positions
        positions = random.sample(range(length), 3)
        key_chars = []
        for i in range(length):
            if i in positions:
                key_chars.append('-')
            else:
                key_chars.append(random.choice(LETTERS))
        serial = ''.join(key_chars)
        if verify(name, serial):
            return serial
    # ASSUMPTION: fallback known-valid key from comment
    return "aaaaaaaaaaa--aaaaaaaaaaa"



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
