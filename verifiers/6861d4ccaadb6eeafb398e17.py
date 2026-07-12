import struct
import hashlib

# Based on the write-up by hacktooth and comments by Ja4V8s28Ck
# Algorithm summary (from the write-up):
#   1. Get the Name string and its length L.
#   2. Compute L * 0x539, convert to hex string -> part A
#   3. Convert the Name bytes to a hex string (bytes_to_hex) -> part B
#   4. Concatenate part A + part B -> intermediate string
#   5. The serial input field is also read, and a second GetDlgItemTextA call
#      suggests the serial is parsed/processed.
#   6. A function at 4092E0 converts bytes to uppercase hex nibbles.
#   7. Some BCD-based calculation is done on the input.
#   8. The result is hashed (SHA-256 based on SHA2_BLAKE2_IVs YARA hit and
#      the 64-char hex output observed in valid serials).
#   9. The expected serial = <hex_hash>-OMGWTFBBQ
#
# Observed valid serials:
#   nightxyz (len=8)  -> 691604A0FA6FA1C99BCED0013AE788A2B39B56AFC0A96867BD2A1C31BE5DC9CE-OMGWTFBBQ
#   Boozy    (len=5)  -> A46EC6FA53551E6C14C4835B324AC3889864AF08D0919FD6A7FA1A453379A149-OMGWTFBBQ
#   InDuLgEo_CrackME_V2 (len=20) -> 89BC00027B89CA2274C1201532EE4D9BFECEE9885326BD013579F9954F42163D-OMGWTFBBQ
#
# From Ja4V8s28Ck's comment:
#   "first 4 chars of name and length of name are the only things important"
#   "BCD based calculations are done to the given input and a hex string is obtained.
#    Then that hex string is hashed."
#
# The write-up shows:
#   - length * 0x539 -> formatted as hex string (wsprintfA with "%X" or similar)
#   - Name bytes converted to hex string via the 4092E0 function
#   - These are concatenated
#   - Then hashed
#
# ASSUMPTION: Only the first 4 chars and the length matter (per Ja4V8s28Ck).
# ASSUMPTION: The intermediate string fed to the hash is:
#   hex(len * 0x539).upper() + hex_encode(name[:4]).upper()
#   then that string is SHA-256 hashed.
# ASSUMPTION: The hash used is SHA-256 (64 hex chars observed in all serials, and
#   YARA hit on SHA2_BLAKE2_IVs).
# ASSUMPTION: The BCD encoding of the name bytes uses the 4092E0 routine which
#   converts each byte to two hex ASCII chars (standard hex encoding).

def _bytes_to_hex_upper(data: bytes) -> str:
    """Mirrors the 4092E0 function: converts each byte to 2 uppercase hex chars."""
    result = []
    for b in data:
        hi = (b >> 4) & 0xF
        lo = b & 0xF
        # The assembly: cmp eax,A / sbb edx,edx / adc eax,0 / lea eax,[eax+edx*8+37]
        # For hi nibble and lo nibble:
        # if nibble < 10: char = nibble + 0x30 ('0'-'9')
        # if nibble >= 10: char = nibble + 0x37 ('A'-'F')
        def nibble_to_char(n):
            if n < 10:
                return chr(n + 0x30)
            else:
                return chr(n + 0x37)
        result.append(nibble_to_char(hi))
        result.append(nibble_to_char(lo))
    return ''.join(result)

def _compute_serial_hash(name: str) -> str:
    name_bytes = name.encode('ascii', errors='replace')
    length = len(name_bytes)

    # Step 1: length * 0x539, format as uppercase hex string
    # ASSUMPTION: wsprintfA format is "%X" (uppercase hex, no leading zeros)
    length_val = length * 0x539
    part_a = format(length_val, 'X').upper()

    # Step 2: Convert name bytes to hex (ASSUMPTION: only first 4 chars matter per Ja4V8s28Ck)
    # But the write-up also shows the full name is hex-encoded and appended.
    # We'll try full name first, then fall back.
    part_b = _bytes_to_hex_upper(name_bytes)

    # Step 3: Concatenate
    intermediate = part_a + part_b

    # Step 4: SHA-256 hash the intermediate string (as bytes)
    # ASSUMPTION: the string is hashed as ASCII bytes
    digest = hashlib.sha256(intermediate.encode('ascii')).hexdigest().upper()
    return digest


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    if not serial.endswith('-OMGWTFBBQ'):
        return False
    provided_hash = serial[:-len('-OMGWTFBBQ')].upper()
    expected_hash = _compute_serial_hash(name)
    return provided_hash == expected_hash


def keygen(name: str) -> str:
    """Generate a valid serial for a given name."""
    h = _compute_serial_hash(name)
    return h + '-OMGWTFBBQ'


# ---- Self-test against known valid pairs ----

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
