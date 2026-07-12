import binascii

def _string_to_hex(s):
    """Convert string to uppercase hex string (2 chars per byte)."""
    return binascii.hexlify(s.encode('latin-1')).upper().decode('ascii')

def _xor_step(text, password):
    """XOR each character of text cyclically with password characters."""
    result = []
    pwd_len = len(password)
    h = 0
    for i in range(len(text)):
        if h == pwd_len:
            h = 1
        else:
            h += 1
        xored = ord(text[i]) ^ ord(password[h-1]) ^ 255
        result.append(chr(xored))
    return ''.join(result)

def _rc4_encrypt_to_hex(text, password):
    """RC4 encrypt text with password, return uppercase hex string."""
    # Build S-box
    box = list(range(256))
    key_bytes = [ord(password[i % len(password)]) for i in range(256)]
    j = 0
    for i in range(256):
        j = (j + box[i] + key_bytes[i]) % 256
        box[i], box[j] = box[j], box[i]
    # Generate keystream and XOR
    cipher = []
    c = 0
    d = 0
    for i in range(len(text)):
        c = (c + 1) % 256
        d = (d + box[c]) % 256
        box[c], box[d] = box[d], box[c]
        e = box[(box[c] + box[d]) % 256]
        cipher_byte = ord(text[i]) ^ e
        cipher.append('%02X' % cipher_byte)
    return ''.join(cipher)

def _string_encrypt(i_encrypt, s_encrypt_text, s_encrypt_password, i_encrypt_level=1):
    """
    AutoIt _StringEncrypt implementation.
    i_encrypt=1 means encrypt.
    The loop runs from 0 to i_encrypt_level (inclusive), so i_encrypt_level+1 iterations.
    """
    if i_encrypt != 1:
        # ASSUMPTION: Only encryption (i_encrypt=1) is needed for keygen
        raise NotImplementedError("Only encryption mode implemented")
    if not s_encrypt_text or not s_encrypt_password:
        return ''
    if i_encrypt_level <= 0 or int(i_encrypt_level) != i_encrypt_level:
        i_encrypt_level = 1
    
    text = s_encrypt_text
    # Loop from 0 to i_encrypt_level inclusive (Step 1 means i_encrypt_level+1 iterations)
    for _ in range(i_encrypt_level + 1):
        # First: XOR step
        text = _xor_step(text, s_encrypt_password)
        # Then: RC4 step producing hex output
        text = _rc4_encrypt_to_hex(text, s_encrypt_password)
    return text

def keygen(name):
    """
    Generate a serial for the given name.
    Replicates the Iliad() function logic:
      1. If name length == 1, double it
      2. serial = _StringEncrypt(1, _StringToHex(name), name, 3)
      3. ello = len(serial)
      4. serial = StringTrimRight(serial, 5)  -> remove last 5 chars
      5. serial = StringTrimLeft(serial, ello - 60) -> remove (ello-60) chars from left
         (if ello-60 <= 0, nothing is removed)
    """
    s = name
    if len(s) == 1:
        s = s + s
    
    hex_name = _string_to_hex(s)
    serial = _string_encrypt(1, hex_name, s, 3)
    
    ello = len(serial)
    # StringTrimRight: remove last 5 chars
    serial = serial[:-5] if len(serial) > 5 else ''
    # StringTrimLeft: remove (ello - 60) chars from left
    trim_left = ello - 60
    if trim_left > 0:
        serial = serial[trim_left:]
    
    return serial

def verify(name, serial):
    """
    Verify that the serial matches the one generated for the given name.
    """
    expected = keygen(name)
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
