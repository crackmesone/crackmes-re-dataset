import struct

# Based on the keygen ASM source for Nordic Crackme #2 by figugegl.
# The crackme is machine-dependent (uses volume serial number of C: drive).
# The keygen ASM calls GetVolumeInformation to get dwVolumeSerialNumber,
# then combines it with a name-derived value.
#
# Since the full CalculateSerial procedure was truncated, we reconstruct
# the most common pattern for this style of crackme:
#   1. Get the volume serial number of the C: drive
#   2. Derive a value from the name (sum/xor of char values)
#   3. Combine them into a serial string
#
# The description says "plain byte-flipping" and "machine-dependent keys".

def _get_volume_serial():
    """Try to get C: drive volume serial number on Windows."""
    try:
        import ctypes
        volumeNameBuffer = ctypes.create_unicode_buffer(1024)
        fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
        serial_number = ctypes.c_uint32(0)
        max_component_length = ctypes.c_uint32(0)
        file_system_flags = ctypes.c_uint32(0)
        result = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p('C:\\'),
            volumeNameBuffer, ctypes.sizeof(volumeNameBuffer),
            ctypes.byref(serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(file_system_flags),
            fileSystemNameBuffer, ctypes.sizeof(fileSystemNameBuffer)
        )
        if result:
            return serial_number.value
    except Exception:
        pass
    return None


def _name_hash(name: str) -> int:
    """Derive a DWORD from the name.
    ASSUMPTION: simple sum of character values (common 'byte-flip' style).
    The actual algorithm in the truncated ASM may differ.
    """
    total = 0
    for ch in name:
        total += ord(ch)
    return total & 0xFFFFFFFF


def _combine(vol_serial: int, name_val: int) -> int:
    """Combine volume serial and name-derived value.
    ASSUMPTION: XOR combination, then possibly add/rotate.
    The actual operation from the truncated ASM is unknown.
    """
    # ASSUMPTION: serial = vol_serial XOR name_val (or some arithmetic combo)
    return (vol_serial ^ name_val) & 0xFFFFFFFF


def _format_serial(value: int) -> str:
    """Format the DWORD as a serial string.
    ASSUMPTION: formatted as uppercase hex XXXXXXXX or decimal.
    Common format in crackmes of this era: XXXX-XXXX (hex groups).
    """
    # ASSUMPTION: two 16-bit halves formatted as XXXX-XXXX
    hi = (value >> 16) & 0xFFFF
    lo = value & 0xFFFF
    return '%04X-%04X' % (hi, lo)


def keygen(name: str, vol_serial: int = None) -> str:
    """Generate serial for a given name.
    vol_serial: the C: drive volume serial number (machine-dependent).
    If not provided, attempts to read it from the system.
    """
    if vol_serial is None:
        vol_serial = _get_volume_serial()
        if vol_serial is None:
            raise RuntimeError(
                'Cannot determine volume serial number. '
                'Provide it explicitly as vol_serial parameter.'
            )
    name_val = _name_hash(name)
    combined = _combine(vol_serial, name_val)
    return _format_serial(combined)


def verify(name: str, serial: str, vol_serial: int = None) -> bool:
    """Verify name/serial pair. Requires the machine's C: drive volume serial."""
    try:
        expected = keygen(name, vol_serial=vol_serial)
        return serial.upper() == expected.upper()
    except RuntimeError:
        return False



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
