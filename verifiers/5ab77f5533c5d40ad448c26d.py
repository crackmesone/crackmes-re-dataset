# Reverse-engineered from: cerebus by j
# Solution by Ank83 on crackmes.de
#
# What we know from the writeup:
# - Name must be 4 < len <= 10 (i.e., len >= 4 and len <= 10, strictly > 3 and <= 10)
# - There is a key-generation procedure at 0x00402740 that produces a serial
# - The final serial-building loop at 0x0040253C processes 0x20 (32) bytes of
#   some intermediate buffer (at [EBX+EBP-0x38]) and converts each byte into
#   two hex-like characters offset by 0x61 ('a'), giving a 64-char output.
# - The loop:
#     byte = buf[i]
#     hi   = (byte >> 4) & 0x0F   -> output char: chr(hi + 0x61)
#     lo   = byte & 0x0F          -> output char: chr(lo + 0x61)
#   This repeats for i in range(0x20), producing a 64-character serial.
# - The CONTENT of the 32-byte intermediate buffer is NOT described in the
#   writeup (the author says "one hell of a long algo" and skips it).
# - The call at 0x00403297 passes both the name and the entered serial to the
#   check function; the result (DEC AL; JE) suggests the function returns 1
#   for success.
#
# ASSUMPTION: The 32-byte intermediate buffer is some hash/digest of the name.
#   The most plausible candidate for a C/C++ crackme of this era is MD5 (which
#   produces exactly 16 bytes, repeated or padded to 32) or SHA-1 (20 bytes,
#   padded to 32) or a custom hash. Without more disassembly we cannot determine
#   the real algorithm, so we use MD5 (16 bytes) zero-padded to 32 bytes as a
#   placeholder. This is LIKELY WRONG but demonstrates the encoding layer.
#
# ASSUMPTION: The encoding layer (the only part fully described) is:
#   for each byte b in buf[0:32]:
#       serial += chr((b >> 4) + 0x61)
#       serial += chr((b & 0x0F) + 0x61)
# This produces a 64-character lowercase-ish serial (chars 'a'..'p').

import hashlib


def _encode_buffer(buf32: bytes) -> str:
    """Encode 32 bytes into a 64-char serial using the loop described in the writeup."""
    assert len(buf32) == 32
    result = []
    for b in buf32:
        hi = (b >> 4) & 0x0F
        lo = b & 0x0F
        result.append(chr(hi + 0x61))
        result.append(chr(lo + 0x61))
    return ''.join(result)


def _compute_intermediate(name: str) -> bytes:
    """Compute the 32-byte intermediate buffer from the name.

    ASSUMPTION: The actual algorithm in the crackme is unknown (skipped in writeup).
    We use MD5 of the name bytes, repeated to fill 32 bytes, as a placeholder.
    Replace this function body with the real algorithm when discovered.
    """
    # ASSUMPTION: placeholder using MD5 (16 bytes) doubled to 32 bytes.
    h = hashlib.md5(name.encode('ascii', errors='replace')).digest()  # 16 bytes
    buf32 = (h + h)  # 32 bytes
    return buf32


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair.

    Name constraints (from disassembly):
        len(name) > 3  (CMP EAX,3 / JLE -> error)
        len(name) <= 10 (CMP EAX,0A / JLE -> ok, else error)
    Serial must be the 64-char string produced by keygen(name).
    """
    if len(name) <= 3 or len(name) > 10:
        return False  # Name length out of range
    expected = keygen(name)
    return serial == expected


def keygen(name: str) -> str:
    """Generate the serial for the given name.

    ASSUMPTION: The intermediate buffer computation is a placeholder (MD5 x2).
    The encoding layer is faithfully reconstructed from the writeup.
    """
    if len(name) <= 3 or len(name) > 10:
        raise ValueError(f'Name must be 4-10 chars, got {len(name)}')
    buf32 = _compute_intermediate(name)
    return _encode_buffer(buf32)



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
