def _rol8(val, count):
    """Rotate left 8-bit value by count bits."""
    val &= 0xFF
    count %= 8
    return ((val << count) | (val >> (8 - count))) & 0xFF

def _ror8(val, count):
    """Rotate right 8-bit value by count bits."""
    val &= 0xFF
    count %= 8
    return ((val >> count) | (val << (8 - count))) & 0xFF

def _encrypt_name_byte(b):
    """Apply the name encryption transform to a single byte."""
    b = _rol8(b, 2)
    b = (b + 0x32) & 0xFF
    b ^= 0x15
    b ^= 0x16
    return b

def _decrypt_file_byte(b):
    """Apply the keyfile decryption transform to a single byte."""
    b ^= 0x16
    b ^= 0x15
    b = (b - 0x32) & 0xFF
    b = _ror8(b, 2)
    return b

def _keybyte_for_name_byte(b):
    """
    Compute the keyfile byte whose decrypted form equals the encrypted name byte.
    
    encrypt_name(b) must equal decrypt_file(keyfile_byte)
    => keyfile_byte = encrypt(encrypt_name(b))
    i.e. apply the name-encryption transform a second time to the already-encrypted name byte.
    
    This matches the Delphi keygen:
      tmp = rol(tmp,2); tmp+=0x32; tmp^=0x15; tmp^=0x16;  <- encrypt name byte
      rol(tmp,2); tmp+=0x32; tmp^=0x15; tmp^=0x16;        <- produce keyfile byte
    """
    enc = _encrypt_name_byte(b)  # encrypted name byte
    # apply encrypt transform again to produce keyfile byte
    kf = _encrypt_name_byte(enc)
    return kf

def keygen(name):
    """
    Generate the bytes that should be written to file.nfo for the given name.
    Returns a bytes object (write in binary mode to file.nfo).
    """
    result = bytearray()
    for ch in name:
        b = ord(ch) if isinstance(ch, str) else ch
        result.append(_keybyte_for_name_byte(b))
    return bytes(result)

def verify(name, serial):
    """
    Simulate the crackme check.
    
    name   - string entered in the dialog
    serial - bytes or str representing the content of file.nfo
             (if str, encoded as latin-1 to get raw bytes)
    
    The check:
      1. Encrypt each name byte with: rol2 -> +0x32 -> xor 0x15 -> xor 0x16
      2. Decrypt each keyfile byte with: xor 0x16 -> xor 0x15 -> -0x32 -> ror2
      3. len(name) must equal len(keyfile_content)
      4. encrypted_name[i] == decrypted_file[i] for all i
    """
    if isinstance(serial, str):
        serial = serial.encode('latin-1')
    if len(name) != len(serial):
        return False
    for i, ch in enumerate(name):
        nb = ord(ch) if isinstance(ch, str) else ch
        enc_name = _encrypt_name_byte(nb)
        dec_file = _decrypt_file_byte(serial[i])
        if enc_name != dec_file:
            return False
    return True

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
