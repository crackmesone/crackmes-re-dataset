import struct

def _rol8(val, count):
    """Rotate left an 8-bit value by count bits."""
    val &= 0xFF
    count %= 8
    return ((val << count) | (val >> (8 - count))) & 0xFF

def _ror8(val, count):
    """Rotate right an 8-bit value by count bits."""
    val &= 0xFF
    count %= 8
    return ((val >> count) | (val << (8 - count))) & 0xFF

def encode(byte_val):
    """Encode a single byte as described in the writeup."""
    c = (byte_val + 0x0A) & 0xFF
    c = c ^ 0x0C
    c = _rol8(c, 3)
    return c

def decode(byte_val):
    """Decode a single byte (inverse of encode)."""
    c = _ror8(byte_val, 3)
    c = c ^ 0x0C
    c = (c - 0x0A) & 0xFF
    return c

def verify(name: str, serial: bytes) -> bool:
    """
    Verification logic:
    1. Encode each byte of the name with encode().
    2. The 'file.key' content (serial) must have the same length as the name.
    3. Each byte of the serial/file.key is decoded with decode().
    4. The decoded bytes must match the encoded name bytes.

    Equivalently, the file.key must contain encode(encode(name_byte)) for each byte,
    because:
      - encoded_name[i] = encode(name[i])
      - file_key[i] decoded = decode(file_key[i])
      - check: decode(file_key[i]) == encode(name[i])
      - => file_key[i] == encode(encode(name[i]))

    This function accepts either a string or bytes for serial.
    """
    if isinstance(name, str):
        name_bytes = name.encode('latin-1')
    else:
        name_bytes = name

    if isinstance(serial, str):
        serial_bytes = serial.encode('latin-1')
    else:
        serial_bytes = bytes(serial)

    if len(serial_bytes) != len(name_bytes):
        return False

    for nb, sb in zip(name_bytes, serial_bytes):
        encoded_name_byte = encode(nb)
        decoded_serial_byte = decode(sb)
        if encoded_name_byte != decoded_serial_byte:
            return False
    return True

def keygen(name: str) -> bytes:
    """
    Generate the file.key content for a given name.
    Per the writeup note: 'The string saved on the file.key must be Encoded twice'.
    So file.key[i] = encode(encode(name[i]))
    """
    if isinstance(name, str):
        name_bytes = name.encode('latin-1')
    else:
        name_bytes = name

    result = bytearray()
    for b in name_bytes:
        result.append(encode(encode(b)))
    return bytes(result)


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
