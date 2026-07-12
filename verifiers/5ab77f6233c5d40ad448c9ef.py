from math import gcd

# RSA-256 parameters extracted from the writeup
# N and D are the private key components (D is the private exponent)
# E is the public exponent
N_HEX = 'CE53EF71DCC51B962FC9F71138D25D66A0814940001DDEB42F1987ACDD30CF11'
D_HEX = '7F7B930DCA37AB74DF702D8CE18BF112B4CB4ACB2FF064FECFD0B67F99B05BA5'
E = 0x10001

N = int(N_HEX, 16)
D = int(D_HEX, 16)


def get_bytes(name: str) -> int:
    """
    Reverse the name, convert each character to its hex ASCII value,
    then reverse that hex string, and interpret as a big integer.

    Steps (from writeup):
      1. Reverse name string
      2. Convert each char to 2-digit hex => hex_str
      3. Reverse hex_str
      4. Interpret as hex integer
    """
    # Step 1: reverse the name
    a = name[::-1]
    # Step 2: convert each char to 2-digit hex
    b = ''.join(format(ord(c), '02X') for c in a)
    # Step 3: reverse the hex string
    b_rev = b[::-1]
    # Step 4: interpret as integer
    # Pad to even length if necessary
    if len(b_rev) % 2 != 0:
        b_rev = '0' + b_rev
    return int(b_rev, 16)


def rsa_decrypt(ct_int: int) -> int:
    """Compute ct ^ D mod N (RSA decryption / signing)"""
    return pow(ct_int, D, N)


def rsa_encrypt(m_int: int) -> int:
    """Compute m ^ E mod N (RSA encryption / verification)"""
    return pow(m_int, E, N)


def int_to_hex_str(value: int) -> str:
    """Convert integer to uppercase hex string (no 0x prefix)"""
    h = format(value, 'X')
    if len(h) % 2 != 0:
        h = '0' + h
    return h


def keygen(name: str) -> str:
    """
    Generate serial for given name.

    The crackme computes: expected = name_bytes ^ D mod N
    and displays it as the serial.

    The serial is the RSA 'signature' (decryption) of the name bytes.
    """
    if not name:
        return 'Enter your name!'
    m = get_bytes(name)
    # Ensure m < N
    m = m % N
    serial_int = rsa_decrypt(m)
    return int_to_hex_str(serial_int)


def verify(name: str, serial: str) -> bool:
    """
    Verify that serial is correct for name.

    The crackme:
      1. Converts name to integer M via get_bytes()
      2. Takes entered serial as hex integer C
      3. Computes C ^ E mod N
      4. Checks if result == M

    i.e., verify that serial ^ E mod N == name_bytes
    """
    if not name or not serial:
        return False
    try:
        c = int(serial, 16)
    except ValueError:
        return False
    m = get_bytes(name) % N
    result = rsa_encrypt(c)
    return result == m



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
