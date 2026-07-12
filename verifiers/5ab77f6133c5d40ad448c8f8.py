# Keygen for scarabee's KeygenMe #2
# Based on Kao's writeup
#
# Algorithm summary:
#   1. Username must be >= 10 chars.
#   2. The first 6 chars of username must have ASCII sum == 0x242 (578).
#   3. Serial is computed from chars at positions 7..end (up to 9 chars, i.e. indices 6..14)
#      checksum = sum( ord(name[6+i]) * strange[i] ) for i in 0..len(suffix)-1
#      where strange = [2, 7, 0xC, 3, 0xB, 5, 0x12, 9, 1, 0xA]
#   4. checksum *= len(name)
#   5. Convert checksum to decimal string, then REVERSE it -> that is the serial.
#   6. Validity check: first char of username == first char of serial.
#      AND entered serial == calculated serial.
#
# ASSUMPTION: The loop over name bytes uses indices 6..min(len(name)-1, 14),
#             i.e. up to 9 characters (strange array has 10 entries, but
#             the writeup says "starting from 7th till end but no more than 9").
# ASSUMPTION: The strange number array is exactly [2, 7, 12, 3, 11, 5, 18, 9, 1, 10].
# ASSUMPTION: The comparison is on the full decimal-reversed string.
# ASSUMPTION: The 'multiply by len(name)' uses the full name length.

STRANGE = [2, 7, 0xC, 3, 0xB, 5, 0x12, 9, 1, 0xA]


def _compute_serial(name: str) -> str:
    """Compute the expected serial for the given (full) name."""
    # Use characters from position 6 onward, up to 9 chars
    suffix = name[6:15]  # positions 7..15 (0-indexed: 6..14), max 9 chars
    checksum = 0
    for i, ch in enumerate(suffix):
        checksum += ord(ch) * STRANGE[i]
    checksum *= len(name)
    # Convert to decimal string, then reverse
    serial = str(checksum)[::-1]
    return serial


def verify(name: str, serial: str) -> bool:
    """Return True if (name, serial) is a valid pair."""
    # Condition 1: name must be at least 10 chars
    if len(name) < 10:
        return False
    # Condition 2: sum of first 6 chars must be 0x242
    prefix_sum = sum(ord(c) for c in name[:6])
    if prefix_sum != 0x242:
        return False
    # Condition 3 & 4: compute serial
    expected = _compute_serial(name)
    if not expected:
        return False
    # Condition 5: first char of name == first char of serial
    if name[0] != expected[0]:
        return False
    # Condition 6: entered serial == computed serial
    return serial == expected


def keygen(wanted_name: str) -> str:
    """
    Generate a valid (full_name, serial) pair for a desired username.
    Strategy from Kao's writeup:
      - Prepend 'X' + 5 asterisks + wanted_name, where X is chosen so that
        sum of first 6 chars == 0x242.
      - Wanted name should be 4..9 chars (positions 7..15 = the suffix used).
    The first char of the full name must equal the first char of the computed serial.
    We brute-force the first char to satisfy that.
    """
    # wanted_name goes into positions 7..end (indices 6..)
    # prefix is 6 chars total: [first_char] + 5 * '*'
    # sum of 5 asterisks = 5 * ord('*') = 5 * 42 = 210
    TARGET_SUM = 0x242  # 578
    FILLER_SUM = 5 * ord('*')  # 210
    needed_first = TARGET_SUM - FILLER_SUM  # 368 -- won't fit in single ASCII char!
    # ASSUMPTION: We need to pick 6 chars whose sum is 578.
    # Kao used approach: choose first char X and 5 filler chars.
    # Since single char can't be 368, we use all 6 prefix chars as filler.
    # We pick prefix chars such that sum == 578.
    # Strategy: use 5 chars of value 'z' (122) = 610, leaves room.
    # 578 - 5*ord('z') = 578 - 610 = -32, negative. Use lower values.
    # Try: 5 * ord('Z') = 5*90=450, first = 578-450 = 128 -- non-ASCII
    # Use mixed: e.g., prefix = find 6 printable chars summing to 578
    # 578 / 6 ~ 96.3, so chars around 96 = '`'
    # Let's do: 5 chars of ord 96 = 480, first = 578-480 = 98 = 'b'
    # But first char of name must == first char of serial (constraint 5)
    # So we must iterate.

    filler_val = 96  # '`'
    filler_sum = 5 * filler_val
    needed_fc = TARGET_SUM - filler_sum  # 578 - 480 = 98

    # Try first_char_ord from printable range, find one that satisfies constraint 5
    for offset in range(0, 200):
        for sign in (1, -1):
            fc_ord = needed_fc + sign * offset
            if not (32 <= fc_ord <= 126):
                continue
            fc = chr(fc_ord)
            # remaining 5 chars must sum to TARGET_SUM - fc_ord
            rem = TARGET_SUM - fc_ord
            # distribute rem over 5 chars
            avg = rem // 5
            leftover = rem % 5
            if not (32 <= avg <= 126):
                continue
            if not (32 <= avg + (1 if leftover > 0 else 0) <= 126):
                continue
            # build prefix chars
            prefix_chars = [fc]
            for j in range(5):
                val = avg + (1 if j < leftover else 0)
                if not (32 <= val <= 126):
                    break
                prefix_chars.append(chr(val))
            else:
                full_name = ''.join(prefix_chars) + wanted_name
                # verify sum
                if sum(ord(c) for c in full_name[:6]) != TARGET_SUM:
                    continue
                if len(full_name) < 10:
                    continue
                serial = _compute_serial(full_name)
                if not serial:
                    continue
                if full_name[0] == serial[0]:
                    return full_name, serial
    # ASSUMPTION: fallback brute force with varying filler
    for fv in range(32, 127):
        for fv2 in range(32, 127):
            fc_ord = TARGET_SUM - 4 * fv - fv2
            if not (32 <= fc_ord <= 126):
                continue
            fc = chr(fc_ord)
            prefix_chars = [fc, chr(fv), chr(fv), chr(fv), chr(fv), chr(fv2)]
            full_name = ''.join(prefix_chars) + wanted_name
            if sum(ord(c) for c in full_name[:6]) != TARGET_SUM:
                continue
            if len(full_name) < 10:
                continue
            serial = _compute_serial(full_name)
            if not serial:
                continue
            if full_name[0] == serial[0]:
                return full_name, serial
    raise ValueError(f"Could not find valid prefix for name '{wanted_name}'")



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
