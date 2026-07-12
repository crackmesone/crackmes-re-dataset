# Reconstructed from VM disassembly of racal_crackme_n3_with_vm
# The writeup is a raw VM disassembly trace, truncated, and many details are unclear.
# This is a partial reconstruction based on what can be inferred.

import ctypes
import struct


def rol32(val, n):
    """Rotate left 32-bit integer by n bits."""
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF


def compute_name_sum(name: str) -> int:
    """Sum of character values of name string."""
    total = 0
    for ch in name:
        total += ord(ch)
    return total & 0xFFFFFFFF


def compute_computer_name_hash(computer_name: str) -> int:
    """
    From the disassembly:
    Loop over each character of computer_name:
      acc = (acc | char_val) | acc  -- actually: acc = acc | char_val, then rol32(acc, 3)
    # ASSUMPTION: The 'or' and rol32 logic from 0x40776C-0x4077DF
    # EAX = movsx byte[computer_name[i]]
    # EAX = EAX | *VM_mem[9]  (which is ebp-0x58, running hash acc)
    # acc = EAX | acc  -> effectively acc = acc | char_val
    # then rol32(acc, 3)
    """
    acc = 0
    for ch in computer_name:
        char_val = ord(ch)
        # ASSUMPTION: first OR uses EAX (char) ORed with current acc stored at ebp-0x58
        # The two 'or [EAX], *VM_Mem[0x9]' instructions are confusing;
        # interpreting as: acc = acc | char_val, then rol32(acc, 3)
        acc = (acc | char_val) & 0xFFFFFFFF
        acc = rol32(acc, 3)
    return acc


def atoi_hex(s: str) -> int:
    """
    ASSUMPTION: The [00] opcode calls some string-to-integer function (possibly strtol/atoi).
    We assume it converts a substring of the serial to an integer.
    """
    try:
        return int(s, 16)
    except ValueError:
        try:
            return int(s)
        except ValueError:
            return 0


def verify(name: str, serial: str) -> bool:
    """
    Based on the VM disassembly:

    1. If name is empty -> fail (show message box)
    2. Compute name_sum = sum of char values of name
    3. Get computer name, compute computer_name_hash (OR + ROL3 loop)
    4. Serial must contain '-' characters as separators
    5. Extract substrings from serial around '-' separators:
       - Part A: serial[serial_index .. serial_index + group_len]  (before first '-' at position i)
       - Part B: serial[i+1 .. i+1+8]  (8 chars after '-')
       - Part C: serial[i+17 .. i+17+8]  (8 chars after second group)
       - Part D: serial[i+9 .. i+9+8]  (another 8-char group)
    6. Convert parts to integers (hex or decimal -- ASSUMPTION: hex)
    7. Check part A value == name_sum
    8. Check part B value != 0xFF
    9. Check part C value != 0xFF
    10. (Further checks truncated in writeup)

    NOTE: The writeup is truncated and many details are assumptions.
    This implementation is PARTIAL and likely incomplete.
    """
    if not name:
        return False

    name_len = len(name)
    serial_len = len(serial)

    if serial_len == 0:
        return False

    # Compute name sum (ebp-0x54 accumulator)
    name_sum = compute_name_sum(name)

    # ASSUMPTION: computer name is obtained at runtime; for keygen purposes
    # we cannot know it, so we use a placeholder.
    # In verify(), we'd need the actual computer name.
    # For testing we use a dummy.
    import socket
    try:
        computer_name = socket.gethostname().upper()
    except Exception:
        computer_name = "WORKSTATION"

    computer_hash = compute_computer_name_hash(computer_name)

    # Find '-' in serial
    # From disassembly: iterates serial positions, checks for '-' (0x2D)
    # ASSUMPTION: serial format is XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    # where each group is 8 hex digits

    parts = serial.split('-')
    if len(parts) < 4:
        return False

    # ASSUMPTION: each part is a hex number
    try:
        part_a = int(parts[0], 16)  # should equal name_sum
        part_b = int(parts[1], 16)  # != 0xFF
        part_c = int(parts[2], 16)  # != 0xFF
        part_d = int(parts[3], 16)  # further checks (truncated)
    except ValueError:
        return False

    if part_a != name_sum:
        return False

    if part_b == 0xFF:
        return False

    if part_c == 0xFF:
        return False

    # ASSUMPTION: Further parts involve computer_hash and other transforms
    # The writeup is truncated so we cannot determine the full check.
    # We return True here provisionally if the basic checks pass.
    # ASSUMPTION: part_d should relate to computer_hash somehow
    # (cannot determine exact relation from truncated disassembly)

    return True


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: serial format = XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
    Part A = name_sum in hex
    Parts B, C, D = arbitrary non-0xFF values
    (full algorithm not recoverable from truncated writeup)
    """
    if not name:
        raise ValueError("Name must not be empty")

    name_sum = compute_name_sum(name)

    # ASSUMPTION: parts B, C, D must not be 0xFF and satisfy unknown conditions
    part_a = name_sum & 0xFFFFFFFF
    part_b = 0x00000001  # ASSUMPTION: arbitrary non-0xFF value
    part_c = 0x00000001  # ASSUMPTION: arbitrary non-0xFF value
    part_d = 0x00000001  # ASSUMPTION: arbitrary value

    return "{:08X}-{:08X}-{:08X}-{:08X}".format(part_a, part_b, part_c, part_d)



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
