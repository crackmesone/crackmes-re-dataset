#!/usr/bin/env python3

"""Keygen/verifier for DBP 1.0 Keygenme by wt0vremr (solution by juza)"""

import hashlib


def _mmx_to_words(value):
    """Split 64-bit value into 4 x 16-bit words [hi ... lo]"""
    return [((value >> b) & 0xFFFF) for b in [48, 32, 16, 0]]


def _words_to_mmx(words):
    """Pack 4 x 16-bit words into a 64-bit integer"""
    mm0 = 0
    for w, shift in zip(words, [48, 32, 16, 0]):
        mm0 |= ((w << shift) & 0xFFFFFFFFFFFFFFFF)
    return mm0 & 0xFFFFFFFFFFFFFFFF


def _mmx_to_bytes(value):
    """Split 64-bit value into 8 bytes [hi ... lo]"""
    return [((value >> b) & 0xFF) for b in [56, 48, 40, 32, 24, 16, 8, 0]]


def _bytes_to_mmx(dbs):
    """Pack 8 bytes into a 64-bit integer"""
    mm0 = 0
    for b, shift in zip(dbs, [56, 48, 40, 32, 24, 16, 8, 0]):
        mm0 |= ((b << shift) & 0xFFFFFFFFFFFFFFFF)
    return mm0 & 0xFFFFFFFFFFFFFFFF


def _psubb(mm0, mm1):
    """PSUBB: packed subtract byte (8 x byte, wrapping)"""
    b0 = _mmx_to_bytes(mm0)
    b1 = _mmx_to_bytes(mm1)
    result = [((a - b) & 0xFF) for a, b in zip(b0, b1)]
    return _bytes_to_mmx(result)


def _compute_serial_hex(username):
    """Return the uppercase hex string that gets SHA-1'd."""
    if not username:
        return None

    # Step 1: partial serial from username
    # serial = ord(username[0])
    # for i in 2 .. len(username)+1:
    #     serial += i
    #     serial *= ord(username[0])
    serial = ord(username[0])
    i = 2
    while i < (len(username) + 1):
        serial += i
        serial *= ord(username[0])
        i += 1

    serial = serial & 0xFFFFFFFFFFFFFFFF
    backup = serial  # saved as mm1 later

    # Step 2: PSRLW mm0, 8  (packed shift right logical word by 8)
    words = _mmx_to_words(serial)
    words = [(w >> 8) & 0xFFFF for w in words]
    mm0 = _words_to_mmx(words)

    # Step 3: PSLLQ mm0, 0x0C  (packed shift left logical quadword by 12)
    # Note: the keygen source does this as a per-word shift, but the PDF
    # says PSLLQ (shift the whole 64-bit value left by 0x0C).
    # The keygen source applies per-word << 0x0C which matches the author's
    # own keygen, so we follow that exactly.
    words2 = _mmx_to_words(mm0)
    words2 = [(w << 0x0C) & 0xFFFF for w in words2]
    mm0 = _words_to_mmx(words2)

    # Step 4: PSUBB mm0, mm1  (packed subtract byte)
    mm1 = backup
    mm2 = _psubb(mm0, mm1)

    # Convert to uppercase hex string (no leading zeros forced by %X)
    serial_str = "%X" % mm2
    return serial_str


def keygen(username):
    """Generate the valid serial for the given username."""
    serial_str = _compute_serial_hex(username)
    if serial_str is None:
        return None
    # SHA-1 of the hex string, take last 9 chars (indices 31..39)
    digest = hashlib.sha1(serial_str.encode('ascii')).hexdigest()
    return digest[31:]


def verify(name, serial):
    """Return True if serial is valid for name."""
    expected = keygen(name)
    if expected is None:
        return False
    return serial.lower() == expected.lower()



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
