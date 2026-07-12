import struct

def _compute_st0(hwid_str, name):
    """
    Compute ST(0) accumulator as described in the writeup.
    hwid_str: string like '1234-CDEF' (the driver string)
    name: user name string
    """
    # Filter out '-' from hwid for iteration (but keep cycling through original)
    st0 = 0
    counter = 0x1388

    hwid_bytes = hwid_str.encode('ascii') if isinstance(hwid_str, str) else hwid_str
    name_bytes = name.encode('ascii') if isinstance(name, str) else name

    hwid_idx = 0
    name_idx = 0

    while counter > 0:
        # Get next non-null, non-'-' byte from hwid (cycling)
        while True:
            ch_hwid = hwid_bytes[hwid_idx % len(hwid_bytes)]
            hwid_idx += 1
            if ch_hwid == 0:
                # restart hwid
                continue
            if ch_hwid == ord('-'):
                continue
            break

        dw1 = ch_hwid

        # Get next non-null byte from name (cycling)
        while True:
            ch_name = name_bytes[name_idx % len(name_bytes)]
            name_idx += 1
            if ch_name != 0:
                break

        # XOR then multiply by counter (signed 32-bit imul)
        xored = (ch_name ^ dw1) & 0xFFFFFFFF
        # imul ecx: signed multiply, take lower 32 bits
        product = ctypes_imul32(xored, counter)
        esp = product
        st0 += esp

        # At specific counter values, multiply esp by 0x1988 and add
        if counter in (0x5DC, 0x2EE, 0x145, 0x64):
            dw1_extra = 0x1988
            extra = ctypes_imul32(product, dw1_extra)
            st0 += extra

        # Add counter itself
        st0 += counter
        counter -= 1

    return st0


def ctypes_imul32(a, b):
    """Signed 32-bit multiply, return lower 32 bits as signed int."""
    # Treat a as signed 32-bit
    a_s = a if a < 0x80000000 else a - 0x100000000
    result = (a_s * b) & 0xFFFFFFFF
    return result


def _make_hwid_str(volume_serial, total_bytes_low):
    """
    Build the HWID string: VolumeSerialNumber XOR TotalNumberOfBytes.LowPart,
    formatted as 'XXXX-XXXX' (8 hex digits with dash after 4th).
    """
    hwid = (volume_serial ^ total_bytes_low) & 0xFFFFFFFF
    s = '%08X' % hwid
    return s[:4] + '-' + s[4:]


def verify(name, serial):
    """
    Verify the serial against the name.
    NOTE: The real crackme also uses machine-specific HWID (VolumeSerial XOR TotalBytes).
    For a machine-independent verify we must accept the HWID as embedded in the serial
    or assume a fixed HWID. Here we demonstrate the algorithm with a placeholder HWID.
    The serial is a decimal integer string.
    The check is: st0 - 0x0BEC5E4 == int(serial)
    # ASSUMPTION: We use hwid_str='0000-0000' as placeholder since real HWID is machine-specific.
    """
    # ASSUMPTION: placeholder HWID - in real crackme this comes from the machine
    hwid_str = '0000-0000'  # ASSUMPTION: machine-specific, replace with real value
    st0 = _compute_st0(hwid_str, name)
    expected_serial = (st0 - 0x0BEC5E4) & 0xFFFFFFFFFFFFFFFF
    try:
        input_serial = int(serial)
    except ValueError:
        return False
    # Handle potential negative wrap
    return input_serial == expected_serial or input_serial == (st0 - 0x0BEC5E4)


def keygen(name, hwid_str='0000-0000'):
    """
    Generate the serial for the given name and HWID string.
    hwid_str format: '1234-CDEF' (8 hex chars with dash).
    # ASSUMPTION: Caller must provide the real HWID from the target machine.
    The real HWID = '%04X-%04X' % ((vserial ^ total_bytes_low) >> 16 & 0xFFFF, (vserial ^ total_bytes_low) & 0xFFFF)
    Actually format is just 8 hex chars of (VolumeSerial XOR TotalBytes.LowPart) split at 4.
    """
    st0 = _compute_st0(hwid_str, name)
    serial_val = st0 - 0x0BEC5E4
    return str(serial_val)



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
