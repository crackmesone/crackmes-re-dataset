import struct
import ctypes
import platform

def _get_computer_name():
    """Try to get the actual computer name; fall back to platform node."""
    try:
        # On Windows we can use ctypes; elsewhere just use platform
        buf = ctypes.create_string_buffer(256)
        size = ctypes.c_ulong(256)
        ctypes.windll.kernel32.GetComputerNameA(buf, ctypes.byref(size))
        return buf.value.decode('ascii', errors='replace')
    except Exception:
        return platform.node()

def _ror32(value, count):
    """Rotate right 32-bit value by count bits."""
    count = count & 31
    value = value & 0xFFFFFFFF
    return ((value >> count) | (value << (32 - count))) & 0xFFFFFFFF

def _bswap32(value):
    """Byte-swap a 32-bit integer."""
    value = value & 0xFFFFFFFF
    b = struct.pack('>I', value)
    return struct.unpack('<I', b)[0]

def _compute_serial_number(name, computer_name):
    """
    Reconstruct the serial number from the assembly loop:

    :0040103D  mov ebx, dword ptr [name_buffer]      ; first DWORD of name
    :00401043  movsx edx, byte ptr [eax+computer_name] ; byte at index eax in computer_name
    :0040104A  add ebx, edx
    :0040104C  ror ebx, 05
    :0040104F  xor ebx, 20h
    :00401052  mov esi, ebx
    :00401054  bswap esi
    :00401056  ror esi, EBh   (235 mod 32 = 11)
    :00401059  inc eax         ; eax starts at name_length (after GetDlgItemTextA)
    :0040105A  dec ecx
    :0040105B  jne loop        ; loop name_length times

    After the loop esi holds the computed value.
    The serial is then formatted as .(decimal_value).
    """
    name_bytes = name.encode('ascii', errors='replace')
    comp_bytes = computer_name.encode('ascii', errors='replace')
    name_len = len(name_bytes)

    if name_len == 0:
        return None

    # ASSUMPTION: ebx is initialised to the first DWORD of the name buffer
    # (little-endian, zero-padded to 4 bytes if shorter)
    first_dword_bytes = (name_bytes + b'\x00' * 4)[:4]
    ebx = struct.unpack('<I', first_dword_bytes)[0]

    # eax starts at name_length (return value of GetDlgItemTextA)
    eax = name_len
    ecx = name_len
    esi = 0

    for _ in range(name_len):
        # movsx edx, byte ptr [eax + computer_name_base]
        # Index into computer_name buffer using eax
        idx = eax % len(comp_bytes) if len(comp_bytes) > 0 else 0  # ASSUMPTION: wrap around if needed
        edx = comp_bytes[idx] if idx < len(comp_bytes) else 0
        # sign-extend byte to 32-bit (movsx)
        if edx & 0x80:
            edx = edx - 256
        edx = ctypes.c_int32(edx).value

        ebx = (ebx + edx) & 0xFFFFFFFF
        ebx = _ror32(ebx, 5)
        ebx = (ebx ^ 0x20) & 0xFFFFFFFF
        esi = ebx
        esi = _bswap32(esi)
        esi = _ror32(esi, 0xEB)  # 235 mod 32 = 11

        eax += 1
        ecx -= 1
        # loop continues while ecx != 0

    # esi now holds the computed serial value (signed interpretation for display?)
    # ASSUMPTION: printed as signed decimal based on the observed example .(1179536458).
    serial_value = ctypes.c_int32(esi).value
    serial_str = '.({}).'.format(serial_value)
    return serial_str

def keygen(name, computer_name=None):
    """Generate the valid serial for the given name (and optionally computer name)."""
    if computer_name is None:
        computer_name = _get_computer_name()
    return _compute_serial_number(name, computer_name)

def verify(name, serial, computer_name=None):
    """Return True if serial matches the expected serial for name."""
    expected = keygen(name, computer_name)
    if expected is None:
        return False
    return serial == expected


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
