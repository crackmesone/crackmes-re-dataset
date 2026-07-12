import hashlib
import struct

# MD5 with modified init constants as described in the tutorial
# Standard MD5 init: 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
# Crackme uses: 0x41424344, 0x65666768, 0x494A4B4C, 0x6D6E6F70
# However, the keygen source uses standard MD5 then overwrites digest[1..5] with name[0..4]
# We follow the keygen source (C++ keygen) as it is the authoritative algorithm shown.

# ASSUMPTION: We use Python's standard hashlib MD5 because the keygen C++ source
# uses MD5Init/MD5Update/MD5Final with the name (not xored name), then patches digest[1..5].
# The tutorial mentions a modified MD5 init in the crackme's *verification* code,
# but the keygen source (what we need to replicate) uses standard MD5.

ALFA = "ACBDFEGIHKJMLONP"

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Name must be at least 5 characters long.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")

    name_bytes = name.encode('latin-1')
    length = len(name_bytes)

    # Step 1: Build the first part: each char XOR 1
    sn_part1 = bytes([b ^ 1 for b in name_bytes]).decode('latin-1')

    # Step 2: Append ";-------"
    sn = sn_part1 + ";-------"

    # Step 3: Compute MD5 of name (standard MD5)
    md5 = hashlib.md5()
    md5.update(name_bytes)
    digest = bytearray(md5.digest())  # 16 bytes

    # Step 4: Overwrite digest[1..5] with name[0..4]
    for j in range(1, 6):
        digest[j] = name_bytes[j - 1]

    # Step 5: Encode all 16 digest bytes using ALFA alphabet (2 hex-like chars per byte)
    serial_suffix = ""
    for i in range(16):
        high = (digest[i] >> 4) & 0x0F
        low = digest[i] & 0x0F
        serial_suffix += ALFA[high]
        serial_suffix += ALFA[low]
    # serial_suffix is 32 chars

    # Append the 32-char suffix
    sn += serial_suffix

    # Total length: len(name) + 8 + 32 = len(name) + 40
    # The tutorial says last serial part must be 39 chars long after the ";"
    # The keygen produces: name_xored + ";-------" + 32 md5 chars
    # After ";" we have: "-------" + 32 chars = 39 chars  -> matches!
    return sn


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given name.
    Based on the keygen source and tutorial description.
    """
    if len(name) < 5:
        return False

    # Check that serial contains ";"
    if ";" not in serial:
        return False

    # Split at ";": before is name XOR 1, after is the rest
    semicolon_pos = serial.index(";")
    part_before = serial[:semicolon_pos]
    part_after = serial[semicolon_pos + 1:]  # should be "-------" + 32 encoded chars

    name_bytes = name.encode('latin-1')
    length = len(name_bytes)

    # Check part before ";" == name XOR 1
    expected_before = bytes([b ^ 1 for b in name_bytes]).decode('latin-1')
    if part_before != expected_before:
        return False

    # Remove "-" dashes from part_after (the crackme strips dashes)
    part_after_no_dash = part_after.replace("-", "")

    # Check charset: only ALFA chars allowed
    for c in part_after_no_dash:
        if c not in ALFA:
            return False

    # Check length of last serial part (after removing dashes) == 32
    # (The tutorial says 39 chars after ";", which includes 7 dashes + 32 encoded = 39)
    # After removing 7 dashes: 32 chars
    if len(part_after_no_dash) != 32:
        return False

    # Compute expected MD5 suffix
    md5 = hashlib.md5()
    md5.update(name_bytes)
    digest = bytearray(md5.digest())

    # Overwrite digest[1..5] with name[0..4]
    for j in range(1, 6):
        digest[j] = name_bytes[j - 1]

    expected_suffix = ""
    for i in range(16):
        high = (digest[i] >> 4) & 0x0F
        low = digest[i] & 0x0F
        expected_suffix += ALFA[high]
        expected_suffix += ALFA[low]

    return part_after_no_dash == expected_suffix



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
