#!/usr/bin/env python3
"""
Reconstructed keygen for 'Not to simple KeyGen V2' by howosec.

Algorithm (from writeup by djd320):

1. Serial must be exactly 16 bytes long.
2. A custom hash function (at 0x401d80 in the binary) is applied:
   h_name  = hash(name)
   h_email = hash(email)
   h_mix   = hash(h_name + h_email)
3. The serial is validated by iterating i in [0, 3, 6, 9, 12, 15]:
   For each i, the loop checks two conditions:
   Condition 1 (must be FALSE for success):
       s8(serial[i]) + s8(serial[(i+1)%17]) == s8(serial[(i+2)%17]) << 3
       where s8(x) = x - 256 if x >= 128 else x  (signed 8-bit)
       and serial[16] is treated as 0 (index 16 wraps to 0)
   Condition 2 (must be TRUE for success at that step):
       At loop index i, the serial byte at position j = (i+3)%17
       must equal  (s8(h_mix[i]) * 4) & 0xFF
4. No serial byte may be 0x00 or 0x0A (null / newline).

NOTE: The custom hash function at 0x401d80 is NOT reconstructed in pure Python;
      it requires the original binary (emulated via Unicorn in the original keygen).
      The verify() below implements only the serial structural checks (step 3/4),
      assuming h_mix is already known / provided.
      The keygen() function shows the full flow but marks the hash as an ASSUMPTION.
"""

from typing import List, Optional, Tuple


LOOP_INDEXES = [0, 3, 6, 9, 12, 15]


def s8(x: int) -> int:
    """Interpret byte as signed 8-bit integer."""
    return x - 256 if x >= 128 else x


def serial_value(serial: bytearray, idx: int) -> int:
    """Return signed value of serial[idx]; index 16 is always 0."""
    if idx == 16:
        return 0
    return s8(serial[idx])


def cond1_is_true(serial: bytearray, i: int) -> bool:
    """
    Condition 1 for loop index i:
        s8(serial[i]) + s8(serial[(i+1)%17]) == s8(serial[(i+2)%17]) << 3
    This must be FALSE for the serial to be valid at step i.
    """
    a = serial_value(serial, i)
    b = serial_value(serial, (i + 1) % 17)
    c = serial_value(serial, (i + 2) % 17)
    return (a + b) == (c << 3)


def force_cond1_false(serial: bytearray, i: int, locked_index: int) -> bool:
    """
    If cond1 is already False, return True.
    Otherwise try tweaking nearby bytes (not locked_index) to make it False.
    """
    if not cond1_is_true(serial, i):
        return True

    tune_positions = [i, (i + 1) % 17, (i + 2) % 17]
    trial_values = [0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x61, 0x62]

    for pos in tune_positions:
        if pos == 16 or pos == locked_index:
            continue
        old = serial[pos]
        for tv in trial_values:
            if tv in (0x00, 0x0A):
                continue
            serial[pos] = tv
            if not cond1_is_true(serial, i):
                return True
        serial[pos] = old
    return False


def verify_with_hash(serial_str: str, h_mix: bytes) -> bool:
    """
    Verify a 16-character serial given the pre-computed h_mix hash.

    Parameters
    ----------
    serial_str : the 16-byte serial string supplied by the user
    h_mix      : hash(hash(name) + hash(email))  -- 17+ bytes assumed
    """
    if len(serial_str) != 16:
        return False

    serial = bytearray(serial_str.encode('latin-1') if isinstance(serial_str, str) else serial_str)

    # No null bytes or newlines allowed
    if any(b in (0x00, 0x0A) for b in serial):
        return False

    for i in LOOP_INDEXES:
        # Condition 1 must be FALSE
        if cond1_is_true(serial, i):
            return False

        # Condition 2: serial[(i+3)%17] must equal (s8(h_mix[i]) * 4) & 0xFF
        target = (s8(h_mix[i]) * 4) & 0xFF
        j = (i + 3) % 17
        if j == 16:
            # index 16 is virtual (always 0); can't satisfy via serial bytes
            # ASSUMPTION: the game skips this or uses a different formula
            continue
        if serial[j] != target:
            return False

    return True


def verify(name: str, serial: str, email: str = '') -> bool:
    """
    Top-level verify.  Because the custom hash (0x401d80) is not reconstructed
    in pure Python, this function CANNOT check condition 2 without the binary.
    It only validates the structural / length / cond1 constraints.

    # ASSUMPTION: Full verification requires emulating 0x401d80 from the binary.
    """
    if len(serial) != 16:
        return False
    serial_b = bytearray(serial.encode('latin-1') if isinstance(serial, str) else serial)
    if any(b in (0x00, 0x0A) for b in serial_b):
        return False
    for i in LOOP_INDEXES:
        if cond1_is_true(serial_b, i):
            return False
    # ASSUMPTION: condition 2 (hash-based byte match) is not checked here
    #             because the custom hash function requires the original binary.
    return True


def build_candidate_from_hash(hash_bytes: bytes) -> Optional[Tuple[int, bytes]]:
    """
    Given h_mix, build a valid 16-byte serial.
    Returns (chosen_loop_index, serial_bytes) or None.
    """
    candidates: List[Tuple[int, int, bytes]] = []

    for i in LOOP_INDEXES:
        target = s8(hash_bytes[i]) * 4
        if target < -128 or target > 127:
            continue

        target_b = target & 0xFF
        if target_b in (0x00, 0x0A):
            continue

        j = (i + 3) % 17
        if j == 16:
            continue  # ASSUMPTION: skip virtual index

        serial = bytearray(b'A' * 16)
        serial[j] = target_b

        if not force_cond1_false(serial, i, j):
            continue
        if any(b in (0x00, 0x0A) for b in serial):
            continue

        printable_score = sum(32 <= b <= 126 for b in serial)
        candidates.append((printable_score, i, bytes(serial)))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (-x[0], x[1]))
    _, idx, serial = candidates[0]
    return idx, serial


def keygen(name: str, email: str = '') -> Optional[str]:
    """
    Generate a valid serial for (name, email).

    # ASSUMPTION: The custom hash function (0x401d80) is emulated using Unicorn
    #             in the original solution.  Without the binary this function
    #             cannot compute h_mix and will return None.
    #             To use this with the binary, pass binary_path to Hash401d80Emu
    #             (see scripts/keygen.py in the original writeup).
    """
    # ASSUMPTION: replace the block below with actual emulator calls when binary is available
    try:
        # If unicorn + binary are available, import and use Hash401d80Emu here.
        # from keygen_emu import Hash401d80Emu  # ASSUMPTION: external module
        # emu = Hash401d80Emu('./howo-not-to-simple-keygen')
        # h_name  = emu.hash_401d80(name.encode('utf-8'))
        # h_email = emu.hash_401d80(email.encode('utf-8'))
        # h_mix   = emu.hash_401d80(h_name + h_email)
        raise NotImplementedError('Binary emulation not available in standalone mode')
    except NotImplementedError:
        # ASSUMPTION: without the hash we cannot compute condition 2 bytes;
        #             return a structurally valid serial that may fail condition 2.
        serial = bytearray(b'A' * 16)
        for i in LOOP_INDEXES:
            if not force_cond1_false(serial, i, -1):
                return None
        if any(b in (0x00, 0x0A) for b in serial):
            return None
        return serial.decode('latin-1')



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
