# Reconstruction of the serial validation algorithm from serial.com by OPX
# Based on 3 independent writeups all agreeing on the same logic.
#
# The crackme reads a serial of up to 7 bytes (6 meaningful chars + Enter).
# It is stored at offset 0x163: [max_len, actual_len, char0, char1, char2, char3, char4, char5, ...]
# So serial[0] = char at offset +2 from the buffer base.
#
# The validation (using 0-indexed into the user-typed chars):
#   BX = word at serial[0..1]  (little-endian: serial[0] | serial[1]<<8)
#   CX = word at serial[2..3]  (little-endian: serial[2] | serial[3]<<8)
#   AX = word at serial[4..5]  (little-endian: serial[4] | serial[5]<<8)
#   BX = BX - AX               (not used further)
#   CX = CX - AX
#   AX = 0, BX = 0
#   AL = serial[0]             (lodsb reloads from same position)
#   CX = CX xor AX             (AX = 0x00 | serial[0])
#   check: CX == 0x0463
#
# In other words, the check reduces to:
#   (word(serial[2], serial[3]) - word(serial[4], serial[5])) XOR serial[0] == 0x0463
#
# Note: serial[1] is completely unused in the check.
# The name is NOT used in validation at all (this is a serial-only crackme).

def _word(lo, hi):
    """Form a little-endian 16-bit word from two byte values."""
    return (lo & 0xFF) | ((hi & 0xFF) << 8)

def verify(name: str, serial: str) -> bool:
    """Verify the serial (name is ignored by the crackme)."""
    s = [ord(c) for c in serial]
    if len(s) < 6:
        return False
    # CX = word(serial[2], serial[3])
    cx = _word(s[2], s[3])
    # AX = word(serial[4], serial[5])
    ax = _word(s[4], s[5])
    # CX -= AX  (16-bit, unsigned, mod 2^16)
    cx = (cx - ax) & 0xFFFF
    # AL = serial[0]
    al = s[0] & 0xFF
    # CX ^= AX (where AX = 0x0000 | AL)
    cx = cx ^ al
    return cx == 0x0463

def keygen(name: str) -> str:
    """Generate a valid serial. Name is ignored.
    
    Algorithm (from writeup 1 / keygen in C):
      serial[5] = serial[3] - 4
      serial[4] = serial[2] - (serial[0] ^ 0x63)
      serial[1] can be anything (unused).
    
    We pick printable ASCII characters for serial[0], serial[2], serial[3]
    and derive the rest.
    """
    # ASSUMPTION: we pick fixed base chars that yield printable results
    # Use the example from writeup 2: serial[0]='C'(0x43), serial[2]='D'(0x44),
    # serial[3]='e'(0x65), derive serial[4] and serial[5].
    # serial[5] = serial[3] - 4
    # serial[4] = serial[2] - (serial[0] ^ 0x63)

    s0 = ord('C')  # 0x43
    s1 = ord(' ')  # unused, space
    s2 = ord('D')  # 0x44
    s3 = ord('e')  # 0x65
    s4 = (s2 - (s0 ^ 0x63)) & 0xFF
    s5 = (s3 - 4) & 0xFF

    serial = chr(s0) + chr(s1) + chr(s2) + chr(s3) + chr(s4) + chr(s5)
    return serial

def keygen_custom(char0, char2, char3) -> str:
    """Generate a serial for arbitrary base characters.
    
    Rules:
      serial[5] = serial[3] - 4
      serial[4] = serial[2] - (serial[0] ^ 0x63)
      serial[1] = anything (use space)
    """
    s0 = ord(char0) if isinstance(char0, str) else char0
    s1 = ord(' ')
    s2 = ord(char2) if isinstance(char2, str) else char2
    s3 = ord(char3) if isinstance(char3, str) else char3
    s4 = (s2 - (s0 ^ 0x63)) & 0xFF
    s5 = (s3 - 4) & 0xFF
    return chr(s0) + chr(s1) + chr(s2) + chr(s3) + chr(s4) + chr(s5)


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
