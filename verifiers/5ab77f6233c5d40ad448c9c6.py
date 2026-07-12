import struct
import math

def eval_name(name: str) -> int:
    # The crackme uses 8 bytes of the name buffer regardless of actual length.
    # Pad / truncate to 8 bytes (with null bytes, mimicking uninitialized buffer zeroed)
    raw = (name.encode('latin-1') + b'\x00' * 8)[:8]
    n = raw

    # Compute initial e as a 32-bit unsigned int
    e = ((n[0] << 24) + (n[1] << 16) + (n[2] << 8) + n[3] +
         n[4] + (n[5] << 8) + (n[6] << 16) + (n[7] << 24))
    e &= 0xFFFFFFFF

    # The park multiplication formula
    # e = (e % 0x01F31D) * 0x41A7 - (e / 0x01F31D) * 0x0B14
    mod = e % 0x01F31D
    div = e // 0x01F31D
    e = mod * 0x41A7 - div * 0x0B14
    e &= 0xFFFFFFFF

    # Interpret e as 4 signed bytes (little-endian)
    packed = struct.pack('<I', e)
    p = list(struct.unpack('4b', packed))  # signed bytes

    # Modify bytes 0, 1, 2
    for i in range(3):
        if p[i] < 0:
            p[i] = p[i] | (-8)  # p[i] |= 0xF8 in signed byte arithmetic
            # 0xF8 in signed byte is -8, so |= -8 on a negative signed byte:
            # if p[i] is already negative (bit7 set), p[i] |= 0xF8 keeps upper bits set
            # Re-do correctly:
            pass
        else:
            pass

    # Redo the byte manipulation correctly using unsigned byte arithmetic then convert back
    pu = list(struct.unpack('4B', packed))  # unsigned bytes

    for i in range(3):
        if pu[i] & 0x80:  # negative in signed sense
            pu[i] = pu[i] | 0xF8
            pu[i] &= 0xFF
        else:
            pu[i] = pu[i] & 0x07
            if pu[i] == 0:
                pu[i] = 1

    # Convert bytes back to signed for the next check
    def to_signed(b):
        return b if b < 128 else b - 256

    sp = [to_signed(pu[i]) for i in range(4)]

    # if !((p[2] ^ p[0]) & 0x80): p[0] = -p[0]
    if not ((pu[2] ^ pu[0]) & 0x80):
        sp[0] = -sp[0]
        pu[0] = sp[0] & 0xFF

    # Repack as little-endian uint
    result = struct.unpack('<I', struct.pack('4B', pu[0] & 0xFF, pu[1] & 0xFF, pu[2] & 0xFF, pu[3] & 0xFF))[0]
    return result


def keygen(name: str):
    """Generate a valid serial for the given name, or None if no solution."""
    if not (3 <= len(name) <= 0x16):
        return None

    name_val = eval_name(name)
    packed = struct.pack('<I', name_val)
    pu = list(struct.unpack('4B', packed))

    def to_signed(b):
        return b if b < 128 else b - 256

    p0 = to_signed(pu[0])
    p1 = to_signed(pu[1])
    p2 = to_signed(pu[2])

    # ASSUMPTION: bytes are interpreted as signed for float arithmetic
    if p0 == 0:
        return None

    a = float(p1) / float(p0)
    b = float(p2) / float(p0)  # always < 0 per writeup

    # Condition: b*b >= 4.0*a  (note: original says b*b >= 4.0*a, not 4*b)
    # x[0] = (-a + sqrt(a*a - 4.0*b)) / 2.0
    # x[1] = (-a - sqrt(a*a - 4.0*b)) / 2.0
    discriminant = a * a - 4.0 * b
    if b * b < 4.0 * a:
        return None  # No solution per writeup
    if discriminant < 0:
        return None

    x0 = (-a + math.sqrt(discriminant)) / 2.0
    x1 = (-a - math.sqrt(discriminant)) / 2.0

    # Pack the two floats as their IEEE 754 hex representations
    b0 = struct.pack('<f', x0)
    b1 = struct.pack('<f', x1)
    key_bytes = b0 + b1
    key_ints = struct.unpack('<II', key_bytes)
    # Serial is the hex string of the two 4-byte values
    serial = '{:08X}{:08X}'.format(key_ints[0], key_ints[1])
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    Serial must be a 16-char hex string (digits and A-F only).
    The crackme converts serial to two 4-byte floats and checks them against expected values.
    """
    if not (3 <= len(name) <= 0x16):
        return False

    # Serial must be exactly 16 hex chars (A-F and digits)
    serial = serial.upper()
    if len(serial) != 16:
        return False
    import re
    if not re.fullmatch(r'[0-9A-F]{16}', serial):
        return False

    # Parse serial as two floats
    try:
        key_int0 = int(serial[0:8], 16)
        key_int1 = int(serial[8:16], 16)
    except ValueError:
        return False

    x0_provided = struct.unpack('<f', struct.pack('<I', key_int0))[0]
    x1_provided = struct.unpack('<f', struct.pack('<I', key_int1))[0]

    expected_serial = keygen(name)
    if expected_serial is None:
        return False

    exp_int0 = int(expected_serial[0:8], 16)
    exp_int1 = int(expected_serial[8:16], 16)
    x0_expected = struct.unpack('<f', struct.pack('<I', exp_int0))[0]
    x1_expected = struct.unpack('<f', struct.pack('<I', exp_int1))[0]

    # The crackme checks the two quadratic roots
    # Either order may be valid (x0,x1) or (x1,x0)
    eps = 1e-5
    match_direct = (abs(x0_provided - x0_expected) < eps and abs(x1_provided - x1_expected) < eps)
    match_swapped = (abs(x0_provided - x1_expected) < eps and abs(x1_provided - x0_expected) < eps)
    return match_direct or match_swapped



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
