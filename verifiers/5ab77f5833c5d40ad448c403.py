import hashlib
import struct

# Based on the writeup by Zaphod for deroko's pemem crackme.
#
# The serial is 27 characters split into three 8-char groups separated by a
# delimiter (any character, zeroed out at positions 8 and 17 in the buffer):
#   serial = XXXXXXXX_YYYYYYYY_ZZZZZZZZ
#
# Each 8-char group is interpreted as a hex number (e.g. "EE4D79A4" -> 0xEE4D79A4).
#
# From the name, 16 bytes are computed (the writeup says a function at 3B14AE
# generates them; the author says it was very lengthy code that he translated
# to C++).  The 16 bytes are then used as indices into a table of DWORDs at
# address 3B216D.  The writeup by lord_Phoenix (solution 2) suggests that MD5
# is used internally (md5.pas is included in solution 3).  So the 16 bytes are
# ASSUMPTION: the MD5 digest of the name (lowercase or as-typed).
#
# Let bytes = name_hash[0..15]
# table[b] = a DWORD looked up from the mysterious table at 3B216D.
#
# The check computes three values from the table and XORs them with the three
# serial parts (after rotating the second ROL 7, and the third ROR 9):
#
#   val1 = table[bytes[0]] XOR table[bytes[3]]
#   val2 = table[bytes[4]] XOR table[bytes[8]]
#   val3 = table[bytes[9]] XOR table[bytes[10]]
#
#   sum = (serial_part1 XOR val1)
#       + (rol32(serial_part2, 7) XOR val2)
#       + (ror32(serial_part3, 9) XOR val3)
#
# Valid serial: sum == 0  (eax shifted right 32 times with no carry => eax==0)
#
# To make each contribution zero independently:
#   serial_part1 = val1
#   serial_part2 = ror32(val2, 7)   (so that ROL(serial_part2,7)==val2)
#   serial_part3 = rol32(val3, 9)   (so that ROR(serial_part3,9)==val3)
#
# ASSUMPTION: The mysterious DWORD table at 3B216D is not given in the writeup.
# We cannot reconstruct it without the binary.  The md5.pas source suggests MD5
# is used for the 16-byte name hash.  The table itself is unknown.
#
# Therefore verify() implements the structural check (assuming we have the table),
# and keygen() is also provided structurally.
#
# The writeup gives a known pair:
#   name="Zaphod", serial="EE4D79A4_A172542A_4227DF7A"
# We can use this to partially validate the logic.

def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def ror32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

def parse_serial(serial):
    """Parse a serial of the form XXXXXXXX_YYYYYYYY_ZZZZZZZZ.
    Returns (part1, part2, part3) as integers, or None on error."""
    # Strip any separator at positions 8 and 17
    if len(serial) != 27:
        return None
    try:
        p1 = int(serial[0:8], 16)
        p2 = int(serial[9:17], 16)
        p3 = int(serial[18:26], 16)
        return p1, p2, p3
    except ValueError:
        return None

# ASSUMPTION: The 16-byte name hash is the MD5 of the name string (encoded as latin-1).
def get_name_hash(name):
    return list(hashlib.md5(name.encode('latin-1')).digest())

# ASSUMPTION: The DWORD table at 3B216D is unknown; we cannot reconstruct it
# from the writeup alone.  The keygen example (Zaphod -> EE4D79A4_A172542A_4227DF7A)
# is used to reverse-engineer the three expected XOR values for validation below.
# Without the table we mark the table lookup as ASSUMPTION.

# Known values from the writeup for reverse-engineering:
# name = "Zaphod"
# serial = "EE4D79A4_A172542A_4227DF7A"
# p1 = 0xEE4D79A4, p2 = 0xA172542A, p3 = 0x4227DF7A
# val1 = p1 (since p1 XOR val1 must contribute 0 to the sum, and the sum must be 0)
# val2 = rol32(p2, 7)
# val3 = ror32(p3, 9)

# ASSUMPTION: stub table - all zeros; real table is unknown.
_TABLE = [0] * 256

def _table_lookup(b):
    # ASSUMPTION: returns DWORD from the mysterious table at 3B216D indexed by byte b
    return _TABLE[b & 0xFF]

def _compute_vals(name):
    """Compute the three XOR masks derived from the name."""
    h = get_name_hash(name)  # ASSUMPTION: MD5 gives the 16 bytes
    val1 = _table_lookup(h[0]) ^ _table_lookup(h[3])
    val2 = _table_lookup(h[4]) ^ _table_lookup(h[8])
    val3 = _table_lookup(h[9]) ^ _table_lookup(h[10])
    return val1, val2, val3

def verify(name, serial):
    """Return True if serial is valid for name."""
    parts = parse_serial(serial)
    if parts is None:
        return False
    p1, p2, p3 = parts
    val1, val2, val3 = _compute_vals(name)
    # Each XOR should produce 0 contribution to the sum:
    # (p1 XOR val1) + (ROL(p2,7) XOR val2) + (ROR(p3,9) XOR val3) == 0 (mod 2^32... actually == 0 exactly)
    contrib1 = (p1 ^ val1) & 0xFFFFFFFF
    contrib2 = (rol32(p2, 7) ^ val2) & 0xFFFFFFFF
    contrib3 = (ror32(p3, 9) ^ val3) & 0xFFFFFFFF
    total = (contrib1 + contrib2 + contrib3) & 0xFFFFFFFF
    return total == 0

def keygen(name):
    """Generate a valid serial for the given name.
    ASSUMPTION: Requires the real DWORD table to produce correct serials.
    Without the table, this will produce serials valid only when table=all-zeros.
    """
    val1, val2, val3 = _compute_vals(name)
    # To make sum == 0, we want contrib1 + contrib2 + contrib3 == 0
    # Simplest: make contrib1 = val1, contrib2 = 0, contrib3 = (2^32 - val1) & mask
    # But the writeup says make each part individually zero:
    p1 = val1  # p1 XOR val1 = 0
    p2 = ror32(val2, 7)  # ROL(p2,7) XOR val2 = 0
    p3 = rol32(val3, 9)  # ROR(p3,9) XOR val3 = 0
    serial = '{:08X}_{:08X}_{:08X}'.format(p1, p2, p3)
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
