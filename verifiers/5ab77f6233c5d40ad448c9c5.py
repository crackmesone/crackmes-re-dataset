import string

def verify(name: str, serial: str) -> bool:
    """
    Validates name/serial pair according to the disassembly.

    Steps:
    1. Name length must be >= 2 and <= 16.
    2. Serial must consist only of A-Z or a-z (letters only, no digits/symbols).
    3. Serial must be the same length as the name.
    4. For each character at position i (1-indexed, ECX counts down from len):
         a. Take the name char value.
         b. Compute: val = char - (char >> 2) - ecx_counter
            where ecx_counter starts at len(name) and decrements by 1 each iteration (LOOPD).
         c. name_mod = val % 7  (unsigned, but we handle sign carefully)
         d. Take the uppercased serial char value (already forced uppercase via AND 0xDF).
         e. serial_mod = serial_char_value % 9
         f. name_mod must equal serial_mod.
    5. After all chars processed, [EDI] (next serial char) must be 0 (same length check).
    6. Sum of all original serial bytes (mod 256) must equal 0.
    """
    # Step 1: name length check
    if len(name) < 2 or len(name) > 16:
        return False

    # Step 2 & 3: serial must be all letters and same length as name
    serial_up = serial.upper()
    if len(serial_up) != len(name):
        return False
    for c in serial_up:
        if not ('A' <= c <= 'Z'):
            return False

    # Step 4: per-character check
    n = len(name)
    for i, (nc, sc) in enumerate(zip(name, serial_up)):
        ecx = n - i  # ECX counts down: starts at n, decrements via LOOPD
        char_val = ord(nc) & 0xFF
        val = char_val - (char_val >> 2) - ecx
        # DIV EBX (7) is unsigned 32-bit division; handle negative by masking
        val = val & 0xFFFFFFFF
        name_mod = val % 7

        serial_char_val = ord(sc) & 0xFF
        # Serial char is already uppercased; EDX=0, EAX=serial_char_val, DIV 9
        serial_mod = serial_char_val % 9

        if name_mod != serial_mod:
            return False

    # Step 6: sum of original serial bytes mod 256 must be 0
    total = sum(ord(c) for c in serial) & 0xFF
    if total != 0:
        return False

    return True


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name.

    Strategy:
    - For each position, find an uppercase letter whose value % 9 == required_mod.
    - Then adjust the last character so that the sum of all serial bytes mod 256 == 0.
    """
    if len(name) < 2 or len(name) > 16:
        raise ValueError(f"Name must be 2-16 characters long, got {len(name)}")

    n = len(name)
    # Collect the required modulo for each position
    required_mods = []
    for i, nc in enumerate(name):
        ecx = n - i
        char_val = ord(nc) & 0xFF
        val = (char_val - (char_val >> 2) - ecx) & 0xFFFFFFFF
        required_mods.append(val % 7)

    # For each position (except last), pick the smallest uppercase letter matching the required mod
    # Letters A-Z: ord 65-90
    # We'll pick candidates for each position
    candidates = []
    for mod in required_mods:
        # Find all uppercase letters whose ord % 9 == mod
        letters = [chr(c) for c in range(65, 91) if c % 9 == mod]
        if not letters:
            raise ValueError(f"No uppercase letter found for mod {mod}")
        candidates.append(letters)

    # Build serial using first candidate for all positions, then fix last to satisfy checksum
    serial_chars = [cands[0] for cands in candidates]

    # Try to fix the last character to make sum % 256 == 0
    current_sum = sum(ord(c) for c in serial_chars) & 0xFF
    needed = (256 - current_sum) % 256  # We need to add `needed` to last char

    # Try all candidates for last position and see if any adjusted value works
    last_idx = n - 1
    last_mod = required_mods[last_idx]

    found = False
    # Try all uppercase letters for the last position that have the right mod
    for c in candidates[last_idx]:
        # Can we adjust: we need ord(c) + delta such that new_sum % 256 == 0
        # and the new char is still A-Z with same % 9
        # Easiest: try all valid chars for last position
        pass

    # Smarter: iterate all valid last-position chars and pick one that fixes checksum
    partial_sum = sum(ord(c) for c in serial_chars[:-1]) & 0xFF
    for c in range(65, 91):
        if c % 9 == last_mod:
            if (partial_sum + c) & 0xFF == 0:
                serial_chars[-1] = chr(c)
                found = True
                break

    if not found:
        # Try extending search: maybe use a different letter at position n-2 to free up last position
        # Exhaustive search over all positions for last two
        for alt_last in range(65, 91):
            if alt_last % 9 != last_mod:
                continue
            for alt_prev in candidates[last_idx - 1] if last_idx > 0 else [serial_chars[last_idx - 1]]:
                test_sum = (sum(ord(c) for c in serial_chars[:-2]) + ord(alt_prev) + alt_last) & 0xFF
                if test_sum == 0:
                    serial_chars[-2] = alt_prev
                    serial_chars[-1] = chr(alt_last)
                    found = True
                    break
            if found:
                break

    if not found:
        # Full brute-force: try all combinations for positions that have multiple candidates
        # This is a fallback; for short names brute-force is feasible
        from itertools import product
        for combo in product(*candidates):
            if sum(ord(c) for c in combo) & 0xFF == 0:
                serial_chars = list(combo)
                found = True
                break

    if not found:
        raise ValueError(f"Could not find valid serial for name '{name}'")

    serial = ''.join(serial_chars)
    assert verify(name, serial), f"Generated serial {serial} failed verification for name {name}"
    return serial



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
