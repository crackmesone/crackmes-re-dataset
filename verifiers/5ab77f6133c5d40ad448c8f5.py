def _keygen_serial(name: str) -> str:
    """
    Reproduce the serial generation algorithm described in the solution writeups.

    Pass 1: for each byte b at index i in name:
        b1 = (b ^ 0xFA) + i - 0x52
        b1 &= 0xFF
        intermediate[i] = b1

    Pass 2: for each byte b1 at index i in intermediate (len = n):
        b2 = (b1 ^ 0x133) - 0x22
        b2 &= 0xFF
        buf[n + i] = b2          # stored at offset EBX (=n) in the shared buffer

    Pass 3 (casing fixup on buf, indices 0..2n-1):
        For each byte dl in buf:
            if 'A'(0x41) <= dl <= 'Z'(0x5A): dl = dl - 0x0A  (shift upper to lower-ish range)
            elif dl < 0x41:                  dl = dl + 0x10  (bump low bytes up)
            store back

    The serial is the second half of buf (indices n..2n-1) converted to chars.
    """
    name_bytes = [ord(c) & 0xFF for c in name]
    n = len(name_bytes)
    if n == 0:
        return ""

    # Pass 1: transform name -> intermediate  (stored in buf[0..n-1])
    intermediate = []
    for i, b in enumerate(name_bytes):
        b1 = ((b ^ 0xFA) + i - 0x52) & 0xFF
        intermediate.append(b1)

    # Pass 2: transform intermediate -> second_half  (stored in buf[n..2n-1])
    second_half = []
    for b1 in intermediate:
        # ASSUMPTION: XOR with 0x133 on a single byte is effectively XOR with 0x33
        # because 0x133 & 0xFF == 0x33. The assembly uses 81F2 (XOR EDX, imm32)
        # but DL is only the low byte, so the high bits of 0x133 cancel out.
        b2 = ((b1 ^ 0x33) - 0x22) & 0xFF
        second_half.append(b2)

    # Pass 3: casing / range fixup on the entire buffer (both halves)
    # From the disasm: CMP EDX,5A / JG upper / CMP EDX,41 / JL lower
    #   upper: SUB DL, 0x0A  (> 'Z')
    #   between 0x41 and 0x5A inclusive: no change (letters A-Z stay)
    #   lower: ADD DL, 0x10  (< 'A')
    # ASSUMPTION: the fixup is applied to the SECOND half (serial chars)
    # based on the writeup description of the keygen output.
    def fixup(b):
        if b > 0x5A:
            return (b - 0x0A) & 0xFF
        elif b < 0x41:
            return (b + 0x10) & 0xFF
        else:
            return b  # 0x41-0x5A stays

    serial_bytes = [fixup(b) for b in second_half]
    return ''.join(chr(b) for b in serial_bytes)


def verify(name: str, serial: str) -> bool:
    """
    Verification mirrors what the crackme checks:

    The crackme generates a serial from the name (keygen), then:
      Step A: for each index i, compute: name_byte[i] + serial_byte[i]
              apply the same operations and store result_A
      Step B: for each index i, compute: name_byte[i] + provided_serial_byte[i]
              apply the same operations and store result_B
      If result_A == result_B then success.

    Because both paths apply identical transformations, result_A == result_B
    iff the generated serial == provided serial (byte-by-byte).

    ASSUMPTION: The comparison is a simple equality of the two transformed
    buffers, which reduces to comparing serial == keygen(name).
    """
    if len(name) == 0:
        return False
    expected = _keygen_serial(name)
    # Lengths must match
    if len(serial) != len(expected):
        return False
    return serial == expected


def keygen(name: str) -> str:
    """Return the valid serial for the given name."""
    return _keygen_serial(name)


# ---- quick self-test ----

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
