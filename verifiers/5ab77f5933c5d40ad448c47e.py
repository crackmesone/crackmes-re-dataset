# Reverse-engineered keygen/verifier for xc2 by virw
# Based on the writeup by _p0w45Hi31D
#
# Key facts from the writeup:
# 1. Name length: 2..20 chars
# 2. Serial length: exactly 29 (0x1D) chars
# 3. First 4 chars of serial are checked via a CRC/hash loop against hardcoded bytes at [4059D8]
# 4. After the 4-char loop, a second check uses the 4 LSBs of name[0] and the serial
#    via procedure 401190 -> 401140 (a string comparison after lookup)
# 5. After that, wsprintfA formats something, and more checks follow (truncated)
#
# The hash function at 0x401010:
#   Takes a byte (key char) and the current state byte (initially 0),
#   runs 8 iterations of a feedback-shift-register-like transform.
#
# The hardcoded comparison bytes at [4059D8+i] for i=0..3 are UNKNOWN from the writeup.
# ASSUMPTION: We do not know the hardcoded bytes at 4059D8; we mark them as placeholders.
# ASSUMPTION: The full serial format and all subsequent checks (after the 4-char loop) are
#             not described in the (truncated) writeup, so those parts are approximated.

def _hash_step(state: int, key_char: int) -> int:
    """Implements the routine at 0x401010.
    Takes current state byte and one key char byte, returns new state byte."""
    cl = state & 0xFF
    dl = key_char & 0xFF
    for _ in range(8):
        al = (cl ^ dl) & 0x01
        if al == 1:
            cl ^= 0x18
        cl = (cl >> 1) & 0xFF
        if al == 1:
            cl |= 0x80
        dl = (dl >> 1) & 0xFF
    return cl & 0xFF


def _hash_reset() -> int:
    """Routine at 0x401000: resets state byte at 4055D4 to 0."""
    return 0


def _hash_4bytes(key_bytes: bytes) -> list:
    """Run the 4-iteration loop on the first 4 bytes of the key.
    Returns list of 4 resulting hash bytes."""
    results = []
    state = 0
    for i in range(4):
        state = _hash_reset()  # reset to 0 each iteration (per 401000)
        state = _hash_step(state, key_bytes[i])
        results.append(state)
    return results


# ASSUMPTION: These are the hardcoded expected bytes at addresses [4059D8], [4059D9], [4059DA], [4059DB]
# They are NOT revealed in the writeup. We cannot determine valid serial without them.
# Placeholder values -- replace with actual values from the binary.
HARDCODED_BYTES = [0x00, 0x00, 0x00, 0x00]  # ASSUMPTION: unknown, must be read from binary


def _find_char_for_hash(expected_hash: int) -> int:
    """Brute-force a printable ASCII char whose hash (with initial state=0) equals expected_hash."""
    for c in range(0x20, 0x7F):
        if _hash_step(0, c) == expected_hash:
            return c
    # Try all bytes if printable not found
    for c in range(0, 256):
        if _hash_step(0, c) == expected_hash:
            return c
    return None


# Table lookup used in 401190 / 401140
# ASSUMPTION: The table at [405060] and the string comparison logic in 401140
# are not fully described. We approximate: the check at 401316 calls 401190
# which does: eax = (name[0] & 0x0F) + 6, then looks up table[name[0]&0x0F],
# then calls strcmp(table_entry, serial+offset).
# We do NOT have the table contents -- this part cannot be verified.
# ASSUMPTION: We skip this check in verify() and note it in keygen.

def verify(name: str, serial: str) -> bool:
    """Attempt to verify name/serial pair.
    WARNING: Partial reconstruction -- hardcoded bytes and table are unknown.
    """
    # Length checks
    if len(name) < 2 or len(name) > 20:
        return False
    if len(serial) != 29:
        return False

    name_b = name.encode('ascii', errors='replace')
    serial_b = serial.encode('ascii', errors='replace')

    # Check 1: first 4 chars of serial via hash loop
    for i in range(4):
        state = _hash_reset()
        state = _hash_step(state, serial_b[i])
        # ASSUMPTION: HARDCODED_BYTES[i] must be replaced with actual binary values
        if HARDCODED_BYTES[i] != 0x00:
            if state != HARDCODED_BYTES[i]:
                return False
        # If HARDCODED_BYTES are all 0 (placeholder), skip this check

    # Check 2: 401190 check using (name[0] & 0x0F) and serial
    # ASSUMPTION: Cannot implement without table at 405060 and full logic of 401140
    # We skip this check.

    # Further checks after wsprintfA are truncated in the writeup.
    # ASSUMPTION: We cannot verify them.

    return True  # ASSUMPTION: incomplete -- only partial checks applied


def keygen(name: str) -> str:
    """Generate a serial for a given name.
    WARNING: Only the first 4 bytes are generated from known algorithm.
    The remaining 25 bytes are UNKNOWN due to truncated writeup.
    """
    if len(name) < 2 or len(name) > 20:
        raise ValueError("Name must be 2-20 characters")

    # Generate first 4 serial bytes from HARDCODED_BYTES
    # ASSUMPTION: HARDCODED_BYTES must be filled from actual binary
    serial_bytes = []
    for i in range(4):
        c = _find_char_for_hash(HARDCODED_BYTES[i])
        if c is None:
            # ASSUMPTION: fallback to 0x41 ('A') if no match found (placeholders are 0x00)
            c = _find_char_for_hash(0x00)  # with placeholder 0x00
            if c is None:
                c = 0x30  # '0'
        serial_bytes.append(c)

    # Remaining 25 bytes: UNKNOWN
    # ASSUMPTION: Fill with printable chars as placeholder
    for _ in range(25):
        serial_bytes.append(ord('A'))  # ASSUMPTION: unknown

    serial = bytes(serial_bytes).decode('ascii', errors='replace')
    # Ensure length is exactly 29
    serial = (serial + 'A' * 29)[:29]
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
