# Reverse-engineered from sv_keygenme (sv_reverser)
# Based on the writeup by red477
#
# Algorithm summary (from writeup):
#
# INPUTS:
#   name  -> read from control 0x3EB (GetDlgItemTextA)
#   serial -> read from control 0x3EC (GetDlgItemTextA), must be exactly 16 chars (0x10)
#
# STEP 1 (call at 0x401038):
#   - ESI = serial string (0x403068)
#   - EBX = name string   (0x403468)
#   - EDI = output buffer (0x403268)
#
#   Loop over serial two characters at a time:
#     chunk = serial[i:i+2]          # take 2 chars
#     val   = str2int(chunk)         # convert 2-hex-digit string to integer (byte value)
#     result_byte = val XOR name[name_pos]
#     store result_byte -> output_buffer
#     name_pos advances by 1, wraps around if past end of name
#     serial index advances by 2
#   => produces 8 result bytes in output_buffer (16 hex chars / 2 = 8 bytes)
#
# STEP 2 (exception-handler path / check at 0x401282):
#   The code intentionally triggers an exception (CALL EDI where EDI points to
#   the output buffer which is NOT valid code).  The SEH handler at 0x401282
#   then runs and checks:
#
#     output_buffer[4..7]  (DWORD at offset 4 in output_buffer)
#     vs DWORD PTR DS:[403690]  which is initialised to 0x0FFFFFF
#     (written as 0x0FFFFFF at 0x401218, then overwritten by the exception
#      handler with the exception-record's first DWORD -- the exception code).
#
#   From the writeup the exception code for executing an invalid instruction /
#   access violation is compared.  The solver says the bytes at output[4..7]
#   must equal 0x0FFFFFF (the initial value) -- the writeup is truncated here
#   but 0x0FFFFFF = 0x00FFFFFF.
#
#   ASSUMPTION: The comparison at 0x40128D checks that
#       DWORD(output_buffer[4:8]) == 0x0FFFFFF  (little-endian)
#   i.e. the 5th-8th result bytes must form the value 0x00FFFFFF.
#
# STEP 3 (call at 0x4012FA -- only reached when step-2 passes):
#   Likely displays the 'success' dialog.  The button is disabled on success.
#   ASSUMPTION: no additional serial check in that call (writeup truncated).
#
# str2int: converts a 2-char hex string to an integer (e.g. "4F" -> 79)
# ASSUMPTION: str2int is a simple hex-string to int conversion.

def str2int(two_chars):
    """Convert a 2-character hex string to an integer.
    ASSUMPTION: this is standard hex conversion."""
    return int(two_chars, 16)


def _compute_xor_bytes(name: str, serial: str) -> bytes:
    """Run the XOR loop from 0x401038.
    serial must be exactly 16 hex characters (8 bytes when parsed).
    name is used cyclically."""
    if len(serial) != 16:
        return b''
    result = []
    name_pos = 0
    name_len = len(name)
    if name_len == 0:
        return b''
    for i in range(0, 16, 2):
        chunk = serial[i:i+2]
        try:
            val = str2int(chunk)
        except ValueError:
            return b''
        name_byte = ord(name[name_pos % name_len])
        result.append(val ^ name_byte)
        name_pos += 1
        # ASSUMPTION: name pointer wraps when it hits the null terminator
    return bytes(result)


def verify(name: str, serial: str) -> bool:
    """Verify a (name, serial) pair.
    Serial must be exactly 16 hex digits."""
    if len(serial) != 16:
        return False
    xor_bytes = _compute_xor_bytes(name, serial)
    if len(xor_bytes) != 8:
        return False
    # Check: DWORD at offset 4 (bytes 4..7) must equal 0x0FFFFFF == 0x00FFFFFF
    # ASSUMPTION: little-endian DWORD comparison
    import struct
    dword_at_4 = struct.unpack_from('<I', xor_bytes, 4)[0]
    target = 0x00FFFFFF
    return dword_at_4 == target


def keygen(name: str) -> str:
    """Generate a valid serial for the given name.

    The serial is 16 hex chars (8 bytes).
    Bytes 0-3 can be arbitrary (ASSUMPTION: not checked beyond the exception path).
    Bytes 4-7 must XOR with name bytes (cyclic) to produce 0x00FFFFFF (little-endian).

    little-endian 0x00FFFFFF = bytes [0xFF, 0xFF, 0xFF, 0x00]
    """
    if not name:
        raise ValueError('Name must not be empty')

    name_len = len(name)

    # ASSUMPTION: bytes 0-3 of the result can be anything; we choose 0x00 each.
    # So serial bytes 0-3 = 0x00 XOR name[0..3 mod len]
    result_bytes_0_3 = [0x00, 0x00, 0x00, 0x00]  # desired output bytes 0-3
    # ASSUMPTION: desired output bytes 4-7 = little-endian 0x00FFFFFF
    result_bytes_4_7 = [0xFF, 0xFF, 0xFF, 0x00]

    serial_bytes = []
    for i, desired in enumerate(result_bytes_0_3 + result_bytes_4_7):
        name_byte = ord(name[i % name_len])
        serial_bytes.append(desired ^ name_byte)

    # Format each byte as two uppercase hex digits
    serial = ''.join('{:02X}'.format(b) for b in serial_bytes)
    return serial



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
