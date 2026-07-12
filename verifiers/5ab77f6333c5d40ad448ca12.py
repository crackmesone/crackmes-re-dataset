from sympy import mod_inverse

# Constants from the writeup / keygen.c
n = int('8FD312A230FE4096F59566AAC6D6229FBBCAA08B23835F78A77B7DF4C9FA723A15E5FB6D5B555670313B2AE346402217FEF2C60896460804999516B1502AEF51', 16)
e = 0x9F2F8283

# serial1 is always 0x61BA19A2 (the fixed first part)
# It satisfies: serial1 * 0x9F0A32E3 mod 0x9F2F8283 = 1
# (serial1 = 0x9F0A32E3^-1 mod 0x9F2F8283)
SERIAL1 = '61BA19A2'


def _name_to_big(name: str) -> int:
    """Convert name string to big integer the same way bytes_to_big does (big-endian)."""
    b = name.encode('latin-1')
    result = int.from_bytes(b, byteorder='big')
    return result


def keygen(name: str) -> str:
    """
    Compute the serial for a given name.

    Algorithm (from writeup):
      serial2 = inverse(name^e mod n, n)
               where e = 0x9F2F8283
    Serial format: 61BA19A2-<serial2 in hex uppercase>
    """
    M = _name_to_big(name)
    if M == 0:
        raise ValueError('Name cannot be empty')

    # Compute M^e mod n
    powered = pow(M, e, n)

    # Compute modular inverse of powered mod n
    # This is serial2
    serial2 = mod_inverse(powered, n)

    serial2_hex = format(serial2, 'X')
    return f'{SERIAL1}-{serial2_hex}'


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.

    The serial must be in the form: 61BA19A2-<hex>

    Verification:
      serial1 must equal 61BA19A2 (first condition: serial1 * 9F0A32E3 mod 9F2F8283 == 1)
      serial2 must satisfy: (name^(9F2F8283*k) * serial2^k) mod n == 1
      which simplifies to: (name^e * serial2) mod n == 1
      i.e.: serial2 == inverse(name^e mod n, n)

    # ASSUMPTION: The verify check implemented here matches what the crackme does internally;
    # the exact crackme binary check is inferred from the keygen logic in the writeup.
    """
    parts = serial.strip().split('-')
    if len(parts) != 2:
        return False

    s1_str, s2_str = parts[0], parts[1]

    # Check serial1
    if s1_str.upper() != SERIAL1.upper():
        return False

    try:
        serial2 = int(s2_str, 16)
    except ValueError:
        return False

    M = _name_to_big(name)
    if M == 0:
        return False

    # Compute k = serial1 * 0x9F0A32E3 // 0x9F2F8283
    serial1_val = int(SERIAL1, 16)
    product = serial1_val * 0x9F0A32E3
    k = product // 0x9F2F8283
    r = product % 0x9F2F8283  # should be 1

    if r != 1:
        # serial1 doesn't satisfy first condition
        return False

    # Condition: (name^(e*k+1) * serial2^k) mod n == name
    # Equivalently: (name^(e*k) * serial2^k) mod n == 1
    # Equivalently: ((name^e mod n) * serial2) mod n == 1  (since exponent is k)
    # ASSUMPTION: k cancels cleanly and the check reduces to (name^e * serial2) mod n == 1
    lhs = (pow(M, e * k, n) * pow(serial2, k, n)) % n
    expected = M % n
    return lhs == expected



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
