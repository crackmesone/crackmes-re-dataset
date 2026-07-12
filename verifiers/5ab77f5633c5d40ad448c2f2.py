import struct

def _xor_forward(data, key):
    """XOR each byte in data (list) with rotating key, updating key in-place."""
    key = list(key)
    j = 0
    for i in range(len(data)):
        orig = data[i]
        data[i] = (key[j] ^ orig) & 0xFF
        key[j] = orig
        j = (j + 1) % 5
    return data

def _xor_backward(data, key):
    """XOR each byte in data (list) from end to start with rotating key, updating key in-place."""
    key = list(key)
    j = 0
    for i in range(len(data) - 1, -1, -1):
        orig = data[i]
        data[i] = (key[j] ^ orig) & 0xFF
        key[j] = orig
        j = (j + 1) % 5
    return data


def _compute_serial(name: str) -> str:
    # Name must be at least 4 chars
    if len(name) < 4:
        return ''

    # The crackme works on name[1:] (skips first char) but still uses full length for accumulation
    # Based on keygen.c and sashaNull's keygen.py:
    # encryptedUsername = bytes of name[1:] (plus a trailing 0 byte per sashaNull)
    # However natitati's C code indexes input[inp_index + 1] starting inp_index=0,
    # meaning it processes name[1], name[2], ... name[len-1], which is name[1:]
    # The accumulation loop uses indices 1..inputLength (inclusive) of the full name buffer,
    # which after XOR transforms corresponds to encryptedUsername[0..len-2] (name[1:])
    # sashaNull appends a trailing 0; natitati's C loops inp_index < inputLength covering name[1..len]
    # We follow natitati's C keygen (solution 4) as the most explicit reference.

    inputLength = len(name)  # number of chars (after stripping newline)

    # Work on a mutable list of the full string bytes
    buf = [ord(c) for c in name]

    # Pass 1: forward XOR on buf[1..inputLength] (indices 1 to inputLength-1 of buf)
    # natitati processes inp_index 0..inputLength-1, accessing input[inp_index+1]
    # so it accesses buf[1] through buf[inputLength] but buf only has indices 0..inputLength-1
    # The last index accessed is buf[inputLength-1+1] = buf[inputLength] which would be out of bounds
    # ASSUMPTION: natitati's C fgets leaves a null at input[inputLength] so it XORs name[1..inputLength]
    # but since Python strings don't have that, we process buf[1..inputLength-1] (name[1:])
    # sashaNull's keygen.py: encryptedUsername = [ord(c) for c in username[1:]] + [0]
    # and loops 0..len(encryptedUsername)-1, so effectively processes name[1:] + [0]
    # We'll follow sashaNull's approach as it's cleaner Python

    enc = [ord(c) for c in name[1:]] + [0]
    n = len(enc)  # = len(name)  (len(name)-1 chars + 1 zero)

    key1 = [0xAA, 0x89, 0xC4, 0xFE, 0x46]
    key2 = [0x78, 0xF0, 0xD0, 0x03, 0xE7]
    key3 = [0xF7, 0xFD, 0xF4, 0xE7, 0xB9]
    key4 = [0xB5, 0x1B, 0xC9, 0x50, 0x73]

    enc = _xor_forward(enc, key1)
    enc = _xor_backward(enc, key2)
    enc = _xor_forward(enc, key3)
    enc = _xor_backward(enc, key4)

    # Accumulate into 4-byte array
    # natitati: for i in 1..inputLength: arrOf4[(i-1)%4] += input[i]
    # This corresponds to enc[0..inputLength-1] (the transformed name[1:] part, excluding trailing 0)
    # sashaNull: for i in range(len(encryptedUsername)): x[i%4] += encryptedUsername[i]
    # sashaNull includes the trailing 0 in the loop but +0 doesn't change anything
    # We use all of enc (including trailing 0, which contributes 0)
    arr4 = [0, 0, 0, 0]
    for i in range(len(enc)):
        arr4[i % 4] = (arr4[i % 4] + enc[i]) & 0xFF

    # Build 32-bit little-endian number
    num = arr4[0] | (arr4[1] << 8) | (arr4[2] << 16) | (arr4[3] << 24)

    # Convert to decimal string
    if num == 0:
        return '0'
    digits = []
    tmp = num
    while tmp > 0:
        digits.append(chr(tmp % 10 + ord('0')))
        tmp //= 10
    return ''.join(reversed(digits))


def verify(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    expected = _compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')
    return _compute_serial(name)



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
