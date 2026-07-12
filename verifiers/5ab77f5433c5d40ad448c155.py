# Reverse-engineered algorithm for OZiRiS by Cyclops
# Based on the writeup which shows:
# 1. Username must be >= 7 chars, serial must be >= 5 chars
# 2. Call 401450 processes the input serial
# 3. Call 401A09 takes username and processed serial, produces a 16-byte value
# 4. That 16-byte value is compared against s2 (derived from serial via call 401A09)
# 5. The 16-byte block at [EBP-70] after call 401A09 is compared with memcmp against [EBP-38]
#
# Key observations from the writeup data:
# - For 'abcdefgh', S1 becomes 'ijklmnopqrstuvwx' => each byte incremented by 1 from username chars
#   Wait: 'a'=0x61 -> 'i'=0x69 => +8, 'b'=0x62 -> 'j'=0x6A => +8 ... so +8 to each char
# - For 'AAAbbbCCC', S1 = 41+0A=4B 41+0A=4B 41+0A=4B 62+0A=6C ... +10 (0x0A) ?
#   Wait: 'A'=0x41 -> 'J'=0x4A => +9, no... 'A'=0x41, result shows 4B = +0xA=10
# - For spaces (0x20): result 0x28 = +8, 0x30 = +0x10 for positions 8-15
# - For 'AA  bb  CC': 0x41->0x4B (+0xA), 0x20->0x2A (+0xA)
# - For 20x 'a' (0x61): result 0x61 stays 0x61 ... no that can't be right
#   Wait 20x 'a': 0012F610 = 61616161 same as input, so no change? But name len=20
#
# ASSUMPTION: The transformation in call 401A09 on the username adds some value
# derived from the serial to each username byte (or XORs), producing S1.
# The serial must be chosen so that S2 == S1.
# Since the writeup is truncated and the crypto is described as 'Custom Crypto',
# the full algorithm cannot be determined from this text.
#
# From the data:
# abcdefgh (len=8) -> each char +8 (which equals len)
# AAAbbbCCC (len=9) -> each char +0xA (10)... not len
# 8 spaces (len=8) -> chars 0-7: +8, chars 8-15: +0x10 (16)
# AA  bb  CC (len=9) -> +0xA
# 20x 'a' (len=20) -> no change (0)? or wraps mod 256?
#
# ASSUMPTION: increment per char = (name_length + 1) mod 256? No...
# abcdefgh len=8: +8 matches
# AAAbbbCCC len=9: +10... doesn't match
# AA  bb  CC len=9 (with spaces, total=9): +10... still doesn't match
# Let's count 'AA  bb  CC' = 'AA' + 2spaces + 'bb' + 2spaces + 'CC' = 9 chars but +0xA=10
# ASSUMPTION: sum of ASCII values of name mod something?
#
# The algorithm cannot be fully reconstructed from the truncated writeup.
# Below is a partial skeleton:

def _transform_name(name):
    """ASSUMPTION: Each byte of name is incremented by some value derived from the name.
    From observations: for len=8 name 'abcdefgh', increment=8.
    For len=9 'AAAbbbCCC', increment=10.
    Pattern unclear - writeup truncated."""
    # ASSUMPTION: increment = len(name) + (some function of serial or name sum)
    # Cannot determine full algorithm from available text
    result = bytearray()
    inc = len(name)  # ASSUMPTION: might just be len(name)
    for c in name[:16]:
        result.append((ord(c) + inc) & 0xFF)
    # Pad to 16 bytes
    while len(result) < 16:
        result.append(0)
    return bytes(result)

def _process_serial(serial):
    """Call 401450 processes the input serial. Output fed to 401A09.
    ASSUMPTION: unknown transformation"""
    # ASSUMPTION: identity or some encoding
    return serial.encode('ascii') if isinstance(serial, str) else serial

def _generate_s2(processed_serial):
    """Call 401A09 with processed serial produces S2 (16 bytes at [EBP-38]).
    ASSUMPTION: unknown transformation of serial -> 16 byte value"""
    # ASSUMPTION: unknown
    return b'\x00' * 16

def verify(name, serial):
    """
    Verifies name/serial pair for OZiRiS by Cyclops.
    PARTIAL: core structure present but inner crypto unknown.
    """
    if len(name) < 7:
        return False
    if len(serial) < 5:
        return False

    # Call 401450: process input serial
    processed_serial = _process_serial(serial)

    # Call 401A09: transform username using processed_serial, store in [EBP-70] (s1)
    # and also compute s2 in [EBP-38]
    # ASSUMPTION: s1 = transform of name, s2 = transform of serial
    s1 = _transform_name(name)

    # ASSUMPTION: s2 is computed from serial via same or related transform
    s2 = _generate_s2(processed_serial)

    # memcmp(s1, s2, 16) == 0
    return s1 == s2

def keygen(name):
    """
    Generates a serial for given name.
    ASSUMPTION: Cannot implement without knowing the full crypto algorithm.
    The serial must be chosen such that _generate_s2(serial) == _transform_name(name).
    """
    # ASSUMPTION: placeholder - real algorithm unknown from truncated writeup
    raise NotImplementedError(
        "Cannot generate serial: crypto algorithm (sub_401450, sub_401A09) "
        "not fully described in the available writeup text."
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
