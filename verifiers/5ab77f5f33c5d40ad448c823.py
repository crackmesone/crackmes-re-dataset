# Reconstructed from writeup analysis of no_reason crackme by raven_
# Solution writeup by alex_ls
#
# The serial generation algorithm:
# 1. Build a 16-byte name buffer: name_buf[i] = name[i % len(name)] for i in 0..15
# 2. Compute nlen_mod = len(name) % 0xFF  (NAMELENGTH MOD 0xFF)
# 3. For each of 16 positions, compute an index into a character table:
#    - BYTE1 = name_buf[i]  (the rewritten name byte)
#    - BYTE1_xor = BYTE1 ^ len(name) ^ nlen_mod
#    - BYTE2 = name[(BYTE1_xor) % len(name)]  (lookup in original name)
#    - BYTE4 = name[i % len(name)]
#    - BYTE3 = BUF_N[i]  (buffer of 0x55 bytes: 'UUUU...')
#    - BYTE5 = BYTE3 ^ BYTE2 ^ BYTE4
#    - INDEX = BYTE5 % 0x3E
#    - serial_char[i] = BUF_C[INDEX]  (char table starting at 0x402198)
# 4. Format as "%c%c%c%c-%c%c%c%c-%c%c%c%c-%c%c%c%c"
#
# ASSUMPTION: BUF_N is 16 bytes all equal to 0x55 (buffer of '5' or 0x55 filler)
# ASSUMPTION: BUF_C is the character table at 0x402198; writeup mentions ABCDEF...
#             We assume it's a printable ASCII sequence starting at 'A' (0x41) going
#             through common alphanumeric chars. Exact table unknown - using a
#             reasonable 62-char alphanumeric table as approximation.
# ASSUMPTION: The writeup is truncated so the exact BUF_C content is unknown.
# ASSUMPTION: NAMELENGTH MOD 0xFF means floor-div style: nlen % 255
# ASSUMPTION: xor with NAMELENGTH uses the raw integer length value

# ASSUMPTION: BUF_C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz' (62 chars = 0x3E)
BUF_C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
assert len(BUF_C) == 0x3E, f"BUF_C length must be 62 (0x3E), got {len(BUF_C)}"

# ASSUMPTION: BUF_N is 16 bytes of 0x55
BUF_N = bytes([0x55] * 16)


def generate_serial(name: str) -> str:
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    nlen = len(name_bytes)
    if nlen == 0:
        # ASSUMPTION: empty name is invalid; return empty
        return ''

    # Step 1: Build 16-byte name buffer
    name_buf = bytearray(16)
    for i in range(16):
        name_buf[i] = name_bytes[i % nlen]

    # Step 2: Compute nlen_mod = nlen % 0xFF
    nlen_mod = nlen % 0xFF

    # Step 3: Generate 16 serial characters
    serial_chars = []
    for i in range(16):
        byte1 = name_buf[i]  # NAME[i] (rewritten buffer)
        byte1_xor = (byte1 ^ nlen ^ nlen_mod) & 0xFF
        # BYTE2 = NAME[byte1_xor % nlen]
        byte2 = name_bytes[byte1_xor % nlen]
        # BYTE4 = NAME[i % nlen]
        byte4 = name_bytes[i % nlen]
        # BYTE3 = BUF_N[i]
        byte3 = BUF_N[i]
        # BYTE5 = BYTE3 ^ BYTE2 ^ BYTE4
        byte5 = (byte3 ^ byte2 ^ byte4) & 0xFF
        # INDEX = BYTE5 % 0x3E
        index = byte5 % 0x3E
        serial_chars.append(BUF_C[index])

    # Step 4: Format as XXXX-XXXX-XXXX-XXXX
    s = serial_chars
    serial = f"{s[0]}{s[1]}{s[2]}{s[3]}-{s[4]}{s[5]}{s[6]}{s[7]}-{s[8]}{s[9]}{s[10]}{s[11]}-{s[12]}{s[13]}{s[14]}{s[15]}"
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    expected = generate_serial(name)
    if not expected:
        return False
    # The crackme compares the generated serial string with the input serial
    return serial.strip() == expected


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    return generate_serial(name)



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
