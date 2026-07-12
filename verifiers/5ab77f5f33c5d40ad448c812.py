import struct
import sys

# Registry serial validation algorithm from ty123's Crackme #3
#
# The crackme does the following:
# 1. Gets the volume serial number of the current drive
# 2. Computes: magic_hash = BSWAP(volume_serial) + 0x44464347
#    where 0x44464347 is the ASCII string "DFCG" in little-endian
# 3. The magic_hash is stored as a hex string (8 hex chars) at address 004031C4
# 4. Registry serial is checked: for each char, serial_char XOR 0x74 == magic_hash_char
#    i.e., serial_char == magic_hash_char XOR 0x74
# 5. Serial must be exactly 8 characters
#
# Additionally the crackme checks for a keyfile (routines 2 and 3), but the
# exact keyfile algorithm is not fully described in the writeup.
#
# ASSUMPTION: The magic_hash is stored as an 8-character ASCII hex string
# (uppercase or lowercase). The writeup shows example magic_hash = "6129149B"
# and serial = "BEFME@M6", let's verify:
# ord('B')=0x42, 0x42 XOR 0x74 = 0x36 = '6' ✓
# ord('E')=0x45, 0x45 XOR 0x74 = 0x31 = '1' ✓
# ord('F')=0x46, 0x46 XOR 0x74 = 0x32 = '2' ✓
# ord('M')=0x4D, 0x4D XOR 0x74 = 0x39 = '9' ✓
# ord('E')=0x45, 0x45 XOR 0x74 = 0x31 = '1' ✓
# ord('@')=0x40, 0x40 XOR 0x74 = 0x34 = '4' ✓
# ord('M')=0x4D, 0x4D XOR 0x74 = 0x39 = '9' ✓
# ord('6')=0x36, 0x36 XOR 0x74 = 0x42 = 'B' ... hmm that gives 'B' not 'B'
# Wait: magic_hash="6129149B", serial char for '9B' last two:
# ord('M')=0x4D XOR 0x74 = 0x39 = '9' ✓
# ord('6')=0x36 XOR 0x74 = 0x42 = 'B' ... but serial ends in '6' not 'B'?
# Recheck: serial = "BEFME@M6", magic = "6129149B"
# pos7: serial='6'=0x36, 0x36 XOR 0x74 = 0x42 = 'B' -- but magic[7]='B'? No magic='6129149B', magic[7]='B'
# Wait '6','1','2','9','1','4','9','B' -> index 7 = 'B' = 0x42
# serial[7] = '6' = 0x36, 0x36 XOR 0x74 = 0x42 = 'B' ✓  
# All checks pass!

def bswap32(val):
    """Byte-swap a 32-bit integer (like x86 BSWAP instruction)"""
    return struct.unpack('<I', struct.pack('>I', val & 0xFFFFFFFF))[0]

def compute_magic_hash_from_vsn(volume_serial_number):
    """
    Given the raw volume serial number (32-bit integer),
    compute the magic hash string stored by the crackme.
    magic_hash_int = BSWAP(vsn) + 0x44464347 (mod 2^32)
    ASSUMPTION: magic hash is stored as uppercase hex string, 8 chars
    """
    bswapped = bswap32(volume_serial_number)
    magic_int = (bswapped + 0x44464347) & 0xFFFFFFFF
    # ASSUMPTION: stored as 8-char uppercase hex string
    magic_hash = "%08X" % magic_int
    return magic_hash

def keygen_from_magic(magic_hash):
    """
    Given the 8-char magic hash string, compute the registry serial.
    serial_char = magic_hash_char XOR 0x74
    """
    assert len(magic_hash) == 8, "Magic hash must be 8 characters"
    serial = "".join(chr(ord(c) ^ 0x74) for c in magic_hash)
    return serial

def keygen_from_vsn(volume_serial_number):
    """
    Given a volume serial number, compute the registry serial.
    """
    magic_hash = compute_magic_hash_from_vsn(volume_serial_number)
    return keygen_from_magic(magic_hash)

def verify_serial_against_magic(serial, magic_hash):
    """
    Verify that the registry serial matches the magic hash.
    Condition: len(serial) == 8 and for each i: serial[i] XOR 0x74 == magic_hash[i]
    """
    if len(serial) != 8 or len(magic_hash) != 8:
        return False
    for s_char, m_char in zip(serial, magic_hash):
        if (ord(s_char) ^ 0x74) != ord(m_char):
            return False
    return True

def verify(name, serial):
    """
    This crackme does NOT use the name in serial validation.
    The serial is validated against a machine-specific magic hash
    derived from the volume serial number.
    
    Since we cannot call GetVolumeInformationA from Python here,
    we demonstrate the algorithm structure.
    
    ASSUMPTION: 'name' parameter here is repurposed to pass the
    volume serial number (as an integer) for testing purposes.
    In the real crackme, name is not used in serial generation.
    """
    # ASSUMPTION: name is passed as the volume serial number (integer)
    # In the real crackme the name field is irrelevant for serial validation
    try:
        vsn = int(name) if isinstance(name, str) else name
    except (ValueError, TypeError):
        # If name is not a VSN integer, we cannot validate without machine info
        return False
    magic_hash = compute_magic_hash_from_vsn(vsn)
    return verify_serial_against_magic(serial, magic_hash)

def keygen(name):
    """
    Generate a valid registry serial.
    ASSUMPTION: 'name' is the volume serial number (integer).
    In the real crackme the name is not part of the algorithm.
    """
    try:
        vsn = int(name) if isinstance(name, str) else name
    except (ValueError, TypeError):
        raise ValueError("For this crackme, pass the volume serial number as 'name'")
    return keygen_from_vsn(vsn)


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
