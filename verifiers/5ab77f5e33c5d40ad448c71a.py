#!/usr/bin/env python3
"""
freesoul's SerialMe #2 - Key Verification & Keygen

Algorithm reconstructed from writeups by El_PuPaZzArO, gibz, and hound.

Serial format (27+ chars):
  [0-3]   = "NaRF"  (fixed prefix)
  [4-8]   = 5 chars derived from name_sum and lookup table
  [9]     = 1 char from (strlen(name) % 4) -> lookup into "XYPO"
  [10]    = 1 char from last letter of name (toupper; if > 'M': -1, else +2)
  [11-26] = remaining chars (not fully described in writeups)

Constraints on name:
  - length > 3 (at least 4 chars)
  - length <= 50
  - all chars alphanumeric
  - first and last chars cannot be digits (side effect of verification)

Serial length must be > 26 (0x1A), i.e. at least 27 chars.
The program only reads up to 0x1C (28) chars for the serial.
"""

LOOKUP = "Z00YWABKKD28LHMFNOP05Q4SI37TWRUE8VVUGUL9AB9AZHGZZC0"
XYPO = "XYPO"

# ASSUMPTION: The lookup table used for serial[4..8] is 0-indexed into LOOKUP
# The first of the 5 chars uses index (53 - len(name)) = (0x35 - len(name))
# The remaining 4 use: idx = ((digit_of_sum[len-i] - '0') * i) + 1
#   where i in 1..4, digit_of_sum is the decimal string of name_sum
#   if idx <= 50 (0x32): use LOOKUP[idx - 1]  (adjusted by -0x40 from EBP-8 base)
#   if idx > 50: use LOOKUP based on name_len offset
# NOTE: The exact indexing arithmetic involves EBP-relative offsets.
# We reconstruct as faithfully as possible from the assembly comments.

def compute_name_sum(name: str) -> int:
    """Sum of ASCII values of all name chars, then multiply by 96."""
    s = sum(ord(c) for c in name)
    return s * 96

def get_serial_char_from_lookup(idx: int, name_len: int) -> str:
    """
    Given a 1-based index into the lookup table:
    - if idx <= 50: return LOOKUP[idx - 1]
    - if idx > 50: use LOOKUP[name_len - 1] (ASSUMPTION for the >50 branch)
    """
    # ASSUMPTION: For idx > 50, the code does ADD EAX, [name_len]; SUB EAX, 0x40
    # and indexes into LOOKUP. The exact offset is unclear; we approximate.
    if idx <= 50 and idx >= 1:
        return LOOKUP[idx - 1]
    else:
        # ASSUMPTION: fallback uses name_len-based index into LOOKUP
        fallback_idx = (name_len - 1) % len(LOOKUP)
        return LOOKUP[fallback_idx]

def get_char_at_9(name: str) -> str:
    """
    char at position 9: (strlen(name) % 4) gives index into 'XYPO'
    The assembly loops strlen(name) times, incrementing a counter 0..3 cyclically.
    Final value = (strlen(name) % 4) if we count from 0 each reset,
    but the loop increments first then checks >3 to reset to 0.
    So after len(name) iterations starting from 0:
      result = len(name) % 4  (since it increments before check)
    Actually from assembly: starts at 0, increments, if >3 reset to 0.
    After n iterations: result = n % 4
    """
    # ASSUMPTION: The loop counter ends at len(name) % 4
    # Assembly: counter starts 0, increments to 1 first iteration, resets when >3
    # So after n steps: value = n % 4 (1-indexed within 0..3)
    # Let's trace: n=4 -> 1,2,3,0 -> ends at 0. n%4=0. XYPO[0]='X'
    # But careful: increments first, so seq is 1,2,3,0,1,2,3,0,...
    # After n steps: if n%4==0 -> 0, else n%4
    # ASSUMPTION: index = len(name) % 4
    idx = len(name) % 4
    return XYPO[idx]

def get_char_at_10(name: str) -> str:
    """
    char at position 10: based on last char of name.
    toupper(last_char); if > 'M' (0x4D): decrement by 1; else: increment by 2
    """
    last = name[-1].upper()
    val = ord(last)
    if val > ord('M'):  # > 0x4D
        val -= 1
    else:
        val += 2
    return chr(val)

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")
    if len(name) > 50:
        raise ValueError("Name must be at most 50 characters")
    if not name.isalnum():
        raise ValueError("Name must be alphanumeric")
    if name[0].isdigit() or name[-1].isdigit():
        raise ValueError("First and last chars of name cannot be digits")

    serial = "NaRF"

    name_sum = compute_name_sum(name)
    name_sum_str = str(name_sum)
    name_len = len(name)

    # Serial[4]: index = (0x35 - name_len) = (53 - name_len)
    # This is the i==0 branch in the loop (CMP DWORD PTR, 0 -> JE)
    idx0 = 53 - name_len
    # ASSUMPTION: index into local copy of LOOKUP string at EBP-48
    # The assembly does: EAX = 0x35 - name_len; then MOVZX from [EAX + EBP - 0x48]
    # LOOKUP was copied to EBP-48, so this is LOOKUP[0x35 - name_len]
    # 0x35 = 53, LOOKUP has 50 chars (indices 0..49)
    # ASSUMPTION: we clamp to valid range
    idx0 = max(0, min(idx0, len(LOOKUP) - 1))
    serial += LOOKUP[idx0]

    # Serial[5..8]: i = 1..4
    # idx = ((name_sum_str[len(name_sum_str) - i] - '0') * i) + 1
    for i in range(1, 5):
        digit_pos = len(name_sum_str) - i
        if digit_pos < 0:
            digit = 0
        else:
            digit = int(name_sum_str[digit_pos])
        idx = (digit * i) + 1
        # if idx <= 0x32 (50): lookup LOOKUP[idx-1]
        # if idx >  0x32:      lookup LOOKUP based on name_len
        if idx <= 50:
            # ASSUMPTION: 1-based index, so LOOKUP[idx-1]
            char = LOOKUP[idx - 1]
        else:
            # ASSUMPTION: uses name_len-based index
            fallback = (name_len - 1) % len(LOOKUP)
            char = LOOKUP[fallback]
        serial += char

    # Serial[9]: XYPO lookup
    serial += get_char_at_9(name)

    # Serial[10]: last-char-of-name transform
    serial += get_char_at_10(name)

    # Serial[11..26]: ASSUMPTION: remaining chars not fully described in writeups
    # The writeup was truncated. We pad with 'A' to reach length 27.
    # ASSUMPTION: The remaining 16 chars are not verified or are all some fixed pattern.
    remaining = 27 - len(serial)
    serial += 'A' * remaining

    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    This reimplements the checks described in the writeups.
    """
    # Length checks
    if len(name) <= 3:
        return False
    if len(serial) <= 26:  # must be > 0x1A
        return False
    if len(name) > 50:
        return False

    # All name chars must be alphanumeric
    if not name.isalnum():
        return False

    # First and last name chars cannot be digits
    if name[0].isdigit() or name[-1].isdigit():
        return False

    # Check serial prefix "NaRF"
    if serial[:4] != 'NaRF':
        return False

    name_sum = compute_name_sum(name)
    name_sum_str = str(name_sum)
    name_len = len(name)

    # Check serial[4]: LOOKUP[53 - name_len]
    idx0 = 53 - name_len
    idx0 = max(0, min(idx0, len(LOOKUP) - 1))
    if serial[4] != LOOKUP[idx0]:
        return False

    # Check serial[5..8]
    for i in range(1, 5):
        digit_pos = len(name_sum_str) - i
        if digit_pos < 0:
            digit = 0
        else:
            digit = int(name_sum_str[digit_pos])
        idx = (digit * i) + 1
        if idx <= 50:
            expected = LOOKUP[idx - 1]
        else:
            fallback = (name_len - 1) % len(LOOKUP)
            expected = LOOKUP[fallback]
        if serial[4 + i] != expected:
            return False

    # Check serial[9]: XYPO
    if serial[9] != get_char_at_9(name):
        return False

    # Check serial[10]: last-char transform
    if serial[10] != get_char_at_10(name):
        return False

    # ASSUMPTION: chars 11..26 are not checked (writeup truncated, unknown)
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
