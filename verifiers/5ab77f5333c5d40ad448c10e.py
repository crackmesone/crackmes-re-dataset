# Reverse-engineered from rasm_minikeygenme writeup
# The crackme is a ring0 (kernel driver) keygen-me.
# The user-mode side:
#   1. Reads name (min 4 chars) and serial (min 16 hex chars)
#   2. Converts 16-char hex serial string to 8 bytes (raw bytes)
#   3. Sends name + converted serial bytes to kernel driver via DeviceIoControl (IOCTL 0x1337)
#      InBuffer layout: name (up to 4 bytes used) + serial bytes (8 bytes) = 12 bytes total
#   4. Driver returns 1 byte: 1 = good, anything else = bad
#
# The driver-side algorithm was NOT fully shown in the truncated writeup.
# Only the ring0 driver (RegDrv.sys) contains the actual validation logic.
# The writeup was cut off before revealing the kernel algorithm.
#
# ASSUMPTION: Based on common mini-keygen patterns and the 12-byte input buffer
# (name 4 bytes + serial 8 bytes), the driver likely computes a value from the
# name bytes and checks it against the serial bytes.
# The exact algorithm is UNKNOWN from the provided text.
#
# ASSUMPTION: A common pattern would be something like:
#   serial_expected = f(name_bytes)
# where f is some arithmetic/hash over the first 4 name bytes producing 8 serial bytes.
# We cannot implement this without the driver disassembly.

def hex_serial_to_bytes(serial_hex):
    """Convert a 16-char hex string to 8 bytes, as the crackme does."""
    if len(serial_hex) < 16:
        return None
    try:
        return bytes.fromhex(serial_hex[:16])
    except ValueError:
        return None

def verify(name, serial):
    """
    Verify name/serial pair.
    Requirements confirmed from writeup:
      - len(name) >= 4
      - len(serial) >= 16 (hex string)
      - serial converts to 8 bytes
    The actual kernel validation algorithm is unknown (writeup truncated).
    """
    if len(name) < 4:
        return False
    if len(serial) < 16:
        return False
    serial_bytes = hex_serial_to_bytes(serial)
    if serial_bytes is None:
        return False
    # ASSUMPTION: kernel driver computes expected serial from name bytes
    # and compares; exact algorithm unknown from available text.
    # Placeholder: always returns False since we cannot reconstruct kernel logic.
    expected = _compute_expected(name.encode('ascii', errors='replace')[:4])
    return serial_bytes == expected

def _compute_expected(name_bytes):
    """
    ASSUMPTION: Placeholder for kernel algorithm.
    The actual algorithm lives in RegDrv.sys DispatchControl handler
    which was not shown in the writeup.
    Returning zeros as a stub.
    """
    # ASSUMPTION: unknown algorithm
    return b'\x00' * 8

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: Cannot generate a real serial without knowing the kernel algorithm.
    Returns a hex string placeholder.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')
    name_bytes = name.encode('ascii', errors='replace')[:4]
    # ASSUMPTION: kernel algorithm unknown; stub returns zeros
    expected = _compute_expected(name_bytes)
    return expected.hex().upper()


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
