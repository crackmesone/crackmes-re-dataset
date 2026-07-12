import struct

def _transform_block(val):
    """Apply the block transformation: bswap, rol 4, xor 0x0004D101, ror 5"""
    # bswap (32-bit byte swap)
    val = val & 0xFFFFFFFF
    val = struct.unpack('<I', struct.pack('>I', val))[0]
    # rol 4
    val = ((val << 4) | (val >> 28)) & 0xFFFFFFFF
    # xor 0x0004D101
    val ^= 0x0004D101
    # ror 5
    val = ((val >> 5) | (val << 27)) & 0xFFFFFFFF
    return val


def _generate_serial_string(name):
    """
    Function1 + Function2/3/4:
    Iterates over 12 name characters (with wrap-around at char 8).
    For each character position (edx = 1..12):
      - Compute: bl = ((name_char + edx) XOR 0x21F) ROL 0x14 AND 0x0F + 0x30
      - Place bl into output buffer (edi)
      - At positions edx==4, 8, 12: place '-' and apply block transform to preceding 4 bytes
    """
    # Pad or cycle name to work with 12 iterations
    # At edx==8, name pointer goes back 6 (sub eax, 6), so chars used:
    # edx=1: name[0], edx=2: name[1], ..., edx=7: name[6]
    # edx=8: name[7] but then sub eax,6 -> eax points to name[2] again
    # Wait: at the START of function1 eax = base of name, edx starts at 1
    # eax is incremented each iteration (inc eax at :70001B63)
    # At edx==8 we sub eax, 6 -- so next iteration eax points to name[3] (was at name[8], sub 6 = name[2]+1 ... let's trace carefully)
    # edx=1: eax=name[0], inc eax -> name[1]
    # edx=2: eax=name[1], inc eax -> name[2]
    # ...
    # edx=7: eax=name[6], inc eax -> name[7]
    # edx=8: eax=name[7], inc eax -> name[8], then sub eax,6 -> name[2]
    # edx=9: eax=name[2], inc eax -> name[3]
    # ...
    # edx=12: eax=name[5]
    # So name chars used: name[0],name[1],name[2],name[3],name[4],name[5],name[6],name[7],name[2],name[3],name[4],name[5]

    name_bytes = name.encode('ascii') if isinstance(name, str) else name
    # Ensure name is long enough; pad with spaces if needed
    if len(name_bytes) < 8:
        name_bytes = name_bytes + b' ' * (8 - len(name_bytes))

    # Sequence of name byte indices accessed
    # edx=1..8: indices 0..7, edx=9..12: indices 2..5
    indices = list(range(0, 8)) + list(range(2, 6))

    out = bytearray()
    edx = 0
    for i, idx in enumerate(indices):
        edx += 1  # inc edx at start of loop
        nb = name_bytes[idx] if idx < len(name_bytes) else 0x20
        ebx = (nb + edx) & 0xFFFFFFFF
        ebx ^= 0x0000021F
        # rol bl, 0x14 = rol bl, 20 -- but bl is only 8 bits, so 20 mod 8 = 4
        bl = ebx & 0xFF
        bl = ((bl << 4) | (bl >> 4)) & 0xFF  # rol 8-bit by 4
        ebx = bl
        ebx &= 0x0F
        ebx += 0x30
        out.append(ebx & 0xFF)

        if edx == 4 or edx == 8:
            # Place '-' at current position
            out.append(0x2D)  # '-'
            # Apply block transform to the 4 bytes preceding the '-'
            # edi-04 means the 4 bytes before the '-' we just placed
            preceding = out[-5:-1]  # 4 bytes before the '-'
            val = struct.unpack('<I', bytes(preceding))[0]
            val = _transform_block(val)
            new_bytes = list(struct.pack('<I', val))
            out[-5:-1] = new_bytes

    # After edx==12 (end of loop), apply function4 to last 4 bytes
    # edi-04 = last 4 bytes of out
    preceding = out[-4:]
    val = struct.unpack('<I', bytes(preceding))[0]
    val = _transform_block(val)
    new_bytes = list(struct.pack('<I', val))
    out[-4:] = new_bytes

    return out


def _apply_serial_transform(serial_str):
    """
    Function5: applies block transform to each 4-byte group of the serial.
    The serial is structured as XXXX-XXXX-XXXX (groups of 4 separated by '-').
    esi advances by 5 each time (4 chars + 1 dash) -- reads DWORD at esi.
    """
    serial_bytes = serial_str.encode('ascii') if isinstance(serial_str, str) else serial_str
    ser = bytearray(serial_bytes)
    # Three groups at offsets 0, 5, 10
    for offset in [0, 5, 10]:
        if offset + 4 <= len(ser):
            val = struct.unpack('<I', bytes(ser[offset:offset+4]))[0]
            val = _transform_block(val)
            ser[offset:offset+4] = struct.pack('<I', val)
    return bytes(ser)


def keygen(name):
    """
    Generate valid serial for given name.
    The valid serial S satisfies: _apply_serial_transform(S) == _generate_serial_string(name)
    Since _transform_block is its own inverse (applied 4 times cycles), we need the inverse.
    """
    # Generate the target string from name
    target = _generate_serial_string(name)
    target_str = bytes(target)

    # To find serial S such that transform(S) == target,
    # we need inverse of _transform_block.
    # _transform_block: bswap -> rol4 -> xor 0x4D101 -> ror5
    # inverse: rol5 -> xor 0x4D101 -> ror4 -> bswap
    def inverse_transform(val):
        val = val & 0xFFFFFFFF
        # rol 5 (inverse of ror 5)
        val = ((val << 5) | (val >> 27)) & 0xFFFFFFFF
        # xor 0x0004D101 (self-inverse)
        val ^= 0x0004D101
        # ror 4 (inverse of rol 4)
        val = ((val >> 4) | (val << 28)) & 0xFFFFFFFF
        # bswap (self-inverse)
        val = struct.unpack('<I', struct.pack('>I', val))[0]
        return val

    ser = bytearray(target_str)
    for offset in [0, 5, 10]:
        if offset + 4 <= len(ser):
            val = struct.unpack('<I', bytes(ser[offset:offset+4]))[0]
            val = inverse_transform(val)
            ser[offset:offset+4] = struct.pack('<I', val)
    return bytes(ser).decode('ascii', errors='replace')


def verify(name, serial):
    """
    Verify name/serial pair.
    Applies transformation to serial and compares with generated string from name.
    """
    target = bytes(_generate_serial_string(name))
    transformed_serial = _apply_serial_transform(serial)
    # Compare the transformed serial with the generated target
    # Both should be 14 bytes: 4 + '-' + 4 + '-' + 4 (but target from keygen is 14 bytes with dashes)
    # ASSUMPTION: exact byte-by-byte comparison of 14-byte strings
    return transformed_serial == target



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
