import struct

def _float_to_hex8(f):
    """Convert a Python float to its 32-bit IEEE 754 hex representation (as 8 uppercase hex chars)."""
    # Pack as single-precision (32-bit) float, then interpret as unsigned int
    packed = struct.pack('<f', f)
    val = struct.unpack('<I', packed)[0]
    return '{:08X}'.format(val)

def keygen(name):
    """Generate a valid serial for the given name (must be at least 4 chars)."""
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters long')

    # n1..n4 are single-precision floats of the first 4 ASCII char values
    n1 = float(ord(name[0]))
    n2 = float(ord(name[1]))
    n3 = float(ord(name[2]))
    n4 = float(ord(name[3]))

    det = n1 * n4 - n2 * n3
    if det == 0.0:
        raise ValueError('Determinant is zero for this name; cannot generate serial')

    # Matrix inverse of [[n1,n2],[n3,n4]] scaled so that:
    # key1 = n4 / (n1*n4 - n2*n3)   => n21
    # key2 = n2 / (n2*n3 - n1*n4)   => n22
    # key3 = n3 / (n2*n3 - n1*n4)   => n23
    # key4 = n1 / (n1*n4 - n2*n3)   => n24
    # All computed as 32-bit floats (matching the original C code using 'float')
    import ctypes

    def to_f32(x):
        """Round-trip through 32-bit float to match original single-precision arithmetic."""
        return struct.unpack('<f', struct.pack('<f', x))[0]

    n1f = to_f32(n1)
    n2f = to_f32(n2)
    n3f = to_f32(n3)
    n4f = to_f32(n4)

    det_f = to_f32(n1f * n4f - n2f * n3f)
    neg_det_f = to_f32(-det_f)

    key1 = to_f32(n4f / det_f)       # n21
    key2 = to_f32(n2f / neg_det_f)   # n22  (n2/(n2*n3-n1*n4) = n2/(-det))
    key3 = to_f32(n3f / neg_det_f)   # n23
    key4 = to_f32(n1f / det_f)       # n24

    serial = '{}-{}-{}-{}'.format(
        _float_to_hex8(key1),
        _float_to_hex8(key2),
        _float_to_hex8(key3),
        _float_to_hex8(key4)
    )
    return serial

def verify(name, serial):
    """Verify that the serial is valid for the given name."""
    if len(name) < 4:
        return False

    # Serial format: 8HEX-8HEX-8HEX-8HEX  => total length = 8+1+8+1+8+1+8 = 35 chars
    # The writeup says length should be 0x23 = 35 chars
    if len(serial) != 35:
        return False

    parts = serial.split('-')
    if len(parts) != 4:
        return False

    try:
        raw_parts = [int(p, 16) for p in parts]
    except ValueError:
        return False

    # Decode each part as a 32-bit float
    def hex_to_f32(val):
        return struct.unpack('<f', struct.pack('<I', val & 0xFFFFFFFF))[0]

    n21 = hex_to_f32(raw_parts[0])
    n22 = hex_to_f32(raw_parts[1])
    n23 = hex_to_f32(raw_parts[2])
    n24 = hex_to_f32(raw_parts[3])

    def to_f32(x):
        return struct.unpack('<f', struct.pack('<f', x))[0]

    # Name integers
    n1 = to_f32(float(ord(name[0])))
    n2 = to_f32(float(ord(name[1])))
    n3 = to_f32(float(ord(name[2])))
    n4 = to_f32(float(ord(name[3])))

    # Apply the transformation described in the writeup:
    # new_n1 = n4*n24 + n3*n22
    # new_n2 = n4*n23 + n3*n21
    # new_n3 = n2*n24 + n1*n22
    # new_n4 = n2*n23 + n1*n21
    new_n1 = to_f32(to_f32(n4 * n24) + to_f32(n3 * n22))
    new_n2 = to_f32(to_f32(n4 * n23) + to_f32(n3 * n21))
    new_n3 = to_f32(to_f32(n2 * n24) + to_f32(n1 * n22))
    new_n4 = to_f32(to_f32(n2 * n23) + to_f32(n1 * n21))

    # After applying transformation, result should be identity matrix:
    # new_n1 == 1, new_n2 == 0, new_n3 == 0, new_n4 == 1
    # The crackme checks n21==1, n22==0, n23==0, n24==1 after the transform
    # which corresponds to checking that serial encodes the inverse of the name matrix.
    eps = 1e-4
    return (abs(new_n1 - 1.0) < eps and
            abs(new_n2 - 0.0) < eps and
            abs(new_n3 - 0.0) < eps and
            abs(new_n4 - 1.0) < eps)


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
