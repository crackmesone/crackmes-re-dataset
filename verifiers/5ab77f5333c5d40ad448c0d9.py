from Crypto.Cipher import DES
import sys

# Constants derived from the crackme source
# var = 1337, leet = 32, tlu = 16, xxx = 16
# offset = (var * leet) / (tlu * xxx) = (1337 * 32) / (16 * 16) = 167
OFFSET = (1337 * 32) // (16 * 16)  # = 167

KEY1 = b'13248657'  # first DES key (outer layer for encryption, first decrypt)
KEY2 = b'13377331'  # second DES key (inner layer for encryption, second decrypt)


def _des_encrypt(data: bytes, key: bytes) -> bytes:
    """DES ECB encryption with PKCS#5 padding (Java default)."""
    cipher = DES.new(key, DES.MODE_ECB)
    # Java's Cipher uses PKCS5Padding by default
    pad_len = 8 - (len(data) % 8)
    data_padded = data + bytes([pad_len] * pad_len)
    return cipher.encrypt(data_padded)


def _des_decrypt(data: bytes, key: bytes) -> bytes:
    """DES ECB decryption, strips PKCS#5 padding."""
    cipher = DES.new(key, DES.MODE_ECB)
    dec = cipher.decrypt(data)
    # strip PKCS5 padding
    pad_len = dec[-1]
    return dec[:-pad_len]


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.

    Serial format: space-separated decimal integers, e.g. "196 80 0 40 ..."

    Verification steps (from crackme source):
      1. Split serial by spaces, parse each as int.
      2. Subtract OFFSET (167) from each value -> byte array ac[]
      3. DES-decrypt ac[] with KEY1 (13248657) -> xu[]
      4. DES-decrypt xu[] with KEY2 (13377331) -> io[]
      5. Convert io[] to string and compare with name.
    """
    if len(name) > 15:
        return False
    try:
        parts = serial.strip().split(' ')
        # Step 1+2: parse integers and subtract offset
        ac = bytes([(int(p) - OFFSET) & 0xFF for p in parts])
        # Step 3: decrypt with KEY1
        xu = _des_decrypt(ac, KEY1)
        # Step 4: decrypt xu with KEY2
        io = _des_decrypt(xu, KEY2)
        # Step 5: compare
        return io.decode('latin-1') == name
    except Exception:
        return False


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Keygen steps (reverse of verification):
      1. Encrypt name bytes with KEY2 (13377331) -> intermediate
      2. Encrypt intermediate with KEY1 (13248657) -> raw_serial
      3. For each byte b in raw_serial: output_value = (b + OFFSET) & 0xFF
         (but Java byte is signed; we need to match the original formula)
      4. Join as space-separated decimal integers.

    Note: The rotateSerialReverse in solution2 adds offset to the signed byte
    then takes & 0xFF to get the unsigned representation for display.
    """
    if len(name) > 15:
        raise ValueError('Name must be <= 15 characters')
    name_bytes = name.encode('latin-1')
    # Encrypt with KEY2 first (inner), then KEY1 (outer)
    step1 = _des_encrypt(name_bytes, KEY2)
    step2 = _des_encrypt(step1, KEY1)
    # Add offset: treat each byte as signed Java byte, add 167, then display as unsigned
    result_ints = []
    for b in step2:
        # b is 0-255 (unsigned Python), convert to signed Java byte first
        signed_b = b if b < 128 else b - 256
        val = (signed_b + OFFSET) & 0xFF
        result_ints.append(val)
    return ' '.join(str(v) for v in result_ints)



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
