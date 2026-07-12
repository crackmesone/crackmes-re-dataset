# roticv's crackme 1 - keyfile-based protection
# The crackme reads 'keyfile.dat', searches for '**' marker,
# hashes the data BEFORE '**' using an unknown hash algorithm (producing 5 dwords),
# and compares them with 5 dwords stored AFTER '**' in the keyfile.
# A 6th byte is also computed from the hash.
#
# The hash algorithm is explicitly described as 'unknown' in both writeups.
# We can reconstruct the keyfile FORMAT but not the hash function itself.

# ASSUMPTION: The hash algorithm is some rolling/accumulation hash over the
# pre-marker bytes producing 5x 32-bit values. The actual algorithm is NOT
# described in any writeup - both authors admit they don't know it.
# We implement the keyfile structure but mark the hash as a stub.

import struct

def _hash_data(data: bytes):
    """
    ASSUMPTION: This is a placeholder for the actual (unknown) hash algorithm.
    The writeup states it produces 5 dwords stored at address 0x401310.
    The actual algorithm was never reverse-engineered by either solution author.
    """
    # ASSUMPTION: unknown hash - cannot implement without the actual assembly
    raise NotImplementedError(
        "The hash algorithm used by this crackme was not documented in any writeup. "
        "Both authors acknowledged it is unknown."
    )

def _compute_sixth_byte(hash_dwords, pre_marker_data):
    """
    ASSUMPTION: The 6th byte is computed via 'sub ecx, eax' where eax comes
    from the hash buffer at offset +0x14 (5th dword's high part or similar).
    The exact computation is not described.
    """
    # ASSUMPTION: placeholder
    raise NotImplementedError("Sixth byte computation algorithm unknown.")

def make_keyfile(pre_marker_text: bytes) -> bytes:
    """
    Constructs a valid keyfile.dat content.
    Format:
      <arbitrary text (pre_marker_text)> + '**' + <5 hash dwords LE> + <1 byte>
    """
    # ASSUMPTION: padding may be needed so that '**' starts on a 0x200-byte boundary
    # The writeup mentions: if (offs + 0x1FF) & 0xFFFFFE00 != offs,
    # bytes 0x0A are padded and 0x99 is placed at end before the hash.
    # We ignore this alignment padding here for simplicity.
    hash_dwords = _hash_data(pre_marker_text)  # raises NotImplementedError
    sixth = _compute_sixth_byte(hash_dwords, pre_marker_text)
    payload = b''
    for dw in hash_dwords:
        payload += struct.pack('<I', dw)
    payload += bytes([sixth])
    return pre_marker_text + b'**' + payload

def verify(name: str, serial: str) -> bool:
    """
    This crackme does NOT use a name+serial pair.
    It validates a keyfile named 'keyfile.dat'.
    
    'name' is ignored.
    'serial' is treated as the keyfile content (as a hex string or raw bytes).
    
    ASSUMPTION: We attempt to parse the keyfile structure and check consistency,
    but since the hash algorithm is unknown we cannot actually verify.
    """
    # ASSUMPTION: serial is the keyfile content as a hex string
    try:
        keyfile_bytes = bytes.fromhex(serial)
    except Exception:
        keyfile_bytes = serial.encode('latin-1')

    # Find '**' marker (search starts from offset 1 per writeup)
    marker_pos = keyfile_bytes.find(b'**', 1)
    if marker_pos == -1:
        return False

    pre_marker = keyfile_bytes[:marker_pos]
    post_marker = keyfile_bytes[marker_pos + 2:]

    # Need at least 5 dwords (20 bytes) + 1 byte = 21 bytes after marker
    if len(post_marker) < 21:
        return False

    stored_dwords = struct.unpack_from('<5I', post_marker, 0)
    stored_sixth = post_marker[20]

    # ASSUMPTION: compute hash and compare - but algorithm is unknown
    try:
        computed_dwords = _hash_data(pre_marker)
        computed_sixth = _compute_sixth_byte(computed_dwords, pre_marker)
        return (tuple(computed_dwords) == stored_dwords and
                computed_sixth == stored_sixth)
    except NotImplementedError:
        # Cannot verify without the hash algorithm
        return False

def keygen(name: str) -> str:
    """
    Cannot generate a valid keyfile without knowing the hash algorithm.
    ASSUMPTION: If hash algorithm were known, we would:
      1. Take arbitrary pre_marker_text
      2. Compute hash -> 5 dwords
      3. Compute 6th byte
      4. Assemble keyfile as: pre_marker_text + '**' + hash_bytes + sixth_byte
    """
    raise NotImplementedError(
        "Keygen impossible: the internal hash algorithm was not recovered from the writeups."
    )


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
