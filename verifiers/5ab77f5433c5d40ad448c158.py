import hashlib
import struct
import re

# Algorithm recovered from NTS Crackme 9 by Cyclops / REAL
# Solution writeups by Prof. DrAcULA and the ASM keygen author
#
# Summary:
# 1. The serial is read via sscanf("%8s"), taking up to 8 chars.
# 2. The string "Cyclops / REAL" is appended to the 8-char serial prefix.
# 3. MD5 is computed on (serial_prefix + "Cyclops / REAL").
# 4. The MD5 digest bytes are formatted as uppercase hex pairs.
# 5. The valid/registered serial displayed is: serial_prefix (8 chars) + first 8 hex pairs (16 hex chars) of MD5
#    = 24 chars total.
# 6. Comparison: the entered serial is compared byte-by-byte against this computed value.
#
# NOTE: The 'name' field appears in the UI but the core check only uses the serial.
# The name must be non-empty (length > 0) to proceed past the first check.
# ASSUMPTION: The serial prefix used in the hash is exactly the first 8 characters of the entered serial
#             (padded or truncated via sscanf "%8s").
# ASSUMPTION: Only the first 8 bytes of the MD5 digest (16 hex chars) are used in the comparison,
#             based on the keygen loop: .WHILE eax < 8 (eax incremented each iteration, ebp += 2 bytes).
#             So 8 iterations * 2 bytes of MD5 = first 8 bytes of MD5 = 16 hex chars appended.
# ASSUMPTION: The name field is not incorporated into the hash - only the serial prefix + constant string.

CYCLOPS_STR = 'Cyclops / REAL'

def _compute_serial_hash(serial_prefix: str) -> str:
    """Compute the expected serial given a serial prefix (up to 8 chars)."""
    # Truncate/pad to 8 chars as sscanf("%8s") would do
    prefix = serial_prefix[:8]
    # Append the constant string
    data = prefix + CYCLOPS_STR
    # Compute MD5
    md5 = hashlib.md5(data.encode('ascii', errors='replace')).digest()
    # Format first 8 bytes as uppercase hex pairs
    # ASSUMPTION: uses uppercase %X format without leading zeros for single-digit hex
    # The keygen uses '%X' (not '%02X'), but the crackme itself uses '%02X'.
    # The solution writeup (solution.txt) shows format "%02X" in the crackme.
    # The keygen ASM uses '%X' without zero-padding.
    # We use the crackme's format (%02X / zero-padded) for the verify function.
    hash_part = ''.join('{:02X}'.format(b) for b in md5[:8])
    return prefix + hash_part

def verify(name: str, serial: str) -> bool:
    """Verify a serial for a given name.
    Name must be non-empty. Serial must be exactly 24 chars.
    """
    if not name or len(name) == 0:
        return False
    if len(serial) < 8:
        return False
    # Extract the 8-char prefix from the entered serial
    # ASSUMPTION: sscanf("%8s") reads the serial directly, not derived from name
    prefix = serial[:8]
    expected = _compute_serial_hash(prefix)
    # Compare entered serial with expected (24 chars)
    return serial[:24] == expected

def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    Name must be non-empty.
    Since the hash uses a random serial prefix (not the name),
    we generate a deterministic prefix from the name for reproducibility.
    ASSUMPTION: Any 8-char serial prefix is valid as long as the full 24-char
    serial matches. We derive a prefix from the name for convenience.
    """
    if not name:
        raise ValueError('Name must be non-empty')
    # Create a deterministic prefix from the name (up to 8 hex chars)
    # ASSUMPTION: any prefix works; we use a hash of the name to pick one
    import hashlib as _hl
    name_hash = _hl.md5(name.encode()).hexdigest()[:8].upper()
    prefix = name_hash  # 8 chars
    full_serial = _compute_serial_hash(prefix)
    return full_serial


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
