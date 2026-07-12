# calypso keygen/verifier
# Based on the writeup by josh. The algorithm is:
#   1. Hash the name twice (hash1 and hash2) - proprietary algos, NOT reversible from the writeup
#   2. Concatenate: complete_name_hash = hash1_result + '-' + hash2_result
#   3. Key part1 = base64(DMC_compress(complete_name_hash))
#   4. Key part2 = CRC32(complete_name_hash + key_part1) as decimal or hex string
#   5. Serial = key_part1 + '-' + key_part2
#
# ASSUMPTION: hash1 and hash2 are proprietary algorithms extracted from the binary.
#             We do NOT have their source, so we cannot implement them here.
#             The DMC (Dynamic Markov Compression) variant used deviates from standard DMC
#             in predictor state reset - exact parameters unknown from writeup alone.
# This is a PARTIAL skeleton only.

import base64
import struct
import zlib

# ---------------------------------------------------------------------------
# ASSUMPTION: hash1 produces a string of the form XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
#             (four 8-char hex groups). Algorithm unknown from writeup.
def hash1(name: str) -> str:
    raise NotImplementedError('hash1: proprietary algorithm not described in writeup')

# ASSUMPTION: hash2 produces a 64-character uppercase hex string.
#             Algorithm unknown from writeup.
def hash2(name: str) -> str:
    raise NotImplementedError('hash2: proprietary algorithm not described in writeup')

# ---------------------------------------------------------------------------
# CRC32 - standard, using magic number 0xEDB88320 (confirmed in writeup)
def crc32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF

# ---------------------------------------------------------------------------
# ASSUMPTION: DMC compressor - the writeup describes a non-standard variant where
#             the predictor state is reset after each character's expansion.
#             The exact implementation is not given; this is a placeholder.
#             The standard DMC reference is http://plg1.cs.uwaterloo.ca/~ftp/dmc/dmc.c
def dmc_compress(data: bytes) -> bytes:
    # ASSUMPTION: This is a placeholder. The actual DMC variant used by calypso
    #             resets predictor state after each character, deviating from standard DMC.
    raise NotImplementedError('DMC compression: non-standard variant not fully described in writeup')

def dmc_expand(data: bytes) -> bytes:
    # ASSUMPTION: Placeholder for the DMC expander as used in calypso.
    raise NotImplementedError('DMC expansion: non-standard variant not fully described in writeup')

# ---------------------------------------------------------------------------
# Base64 encode/decode - standard base64 (writeup confirms standard base64)
def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')

def b64_decode(s: str) -> bytes:
    return base64.b64decode(s)

# ---------------------------------------------------------------------------
def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Steps:
      1. Compute complete_name_hash = hash1(name) + '-' + hash2(name)
      2. DMC-compress the complete_name_hash bytes
      3. Base64-encode the compressed bytes -> key_part1
      4. CRC32(complete_name_hash_bytes + key_part1_bytes) -> key_part2
      5. serial = key_part1 + '-' + str(key_part2)
    """
    h1 = hash1(name)  # e.g. 'F1AD203B-D038866A-D17A5E15-CAFFD8A7'
    h2 = hash2(name)  # e.g. '92CC85F9E05F3572CF24D814CA485B334F17165B76781F0F3CD7FCF9F0289D24'
    complete_name_hash = h1 + '-' + h2

    # Compress the complete name hash (as ASCII bytes)
    cnh_bytes = complete_name_hash.encode('ascii')
    compressed = dmc_compress(cnh_bytes)

    # Base64 encode
    key_part1 = b64_encode(compressed)

    # CRC32 of complete_name_hash + key_part1
    crc_input = cnh_bytes + key_part1.encode('ascii')
    key_part2 = crc32(crc_input)

    # ASSUMPTION: key_part2 is represented as an unsigned 32-bit decimal or hex string.
    #             Using hex uppercase to match the crackme style.
    serial = key_part1 + '-' + format(key_part2, '08X')
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    """
    # Split serial at last '-'
    dash_idx = serial.rfind('-')
    if dash_idx == -1:
        return False
    key_part1 = serial[:dash_idx]
    key_part2_str = serial[dash_idx+1:]

    # Parse key_part2 as a number (try hex first, then decimal)
    try:
        key_part2_given = int(key_part2_str, 16)
    except ValueError:
        try:
            key_part2_given = int(key_part2_str, 10)
        except ValueError:
            return False

    # Compute hashes
    h1 = hash1(name)
    h2 = hash2(name)
    complete_name_hash = h1 + '-' + h2
    cnh_bytes = complete_name_hash.encode('ascii')

    # CRC32 check
    crc_input = cnh_bytes + key_part1.encode('ascii')
    expected_crc = crc32(crc_input)
    if expected_crc != key_part2_given:
        return False

    # DMC expansion check: decode key_part1 from base64, expand, compare to complete_name_hash
    try:
        compressed_bytes = b64_decode(key_part1)
        expanded = dmc_expand(compressed_bytes)
    except Exception:
        return False

    return expanded == cnh_bytes



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
