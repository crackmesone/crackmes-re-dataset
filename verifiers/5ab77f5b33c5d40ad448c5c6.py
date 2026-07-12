# Hackerman crypto crackme #1 - keygen / verifier
# Algorithm: RSA signature (really just modular exponentiation)
#   serial = name_as_bignum ^ d  mod  n
# where the name bytes are interpreted as a base-256 big-integer (little-endian,
# i.e. _BigInB256 loads bytes as-is, first byte is least-significant).
# The serial is then output as a hex string (big-endian, uppercase).
#
# Constants extracted from the assembly source (hckman_kg.Asm):
#   n = AB185AE9243F57C7428B7CE76B62A5E1321CA3A3F966659  (hex, but note the
#       string in the .data section appears to be missing a nibble - padded below)
#   d = 10001  (hex) = 65537  (this is the PUBLIC exponent, so this is actually
#       an RSA *encryption* not a traditional signature - see ASSUMPTION below)
#
# ASSUMPTION: The 'n' value in the source is "AB185AE9243F57C7428B7CE76B62A5E1321CA3A3F966659"
#             which is 47 hex digits (odd length). We assume a leading zero is implied,
#             making it 48 hex digits / 192-bit modulus:
#             n = 0xAB185AE9243F57C7428B7CE76B62A5E1321CA3A3F966659
#
# ASSUMPTION: _BigInB256 treats the input byte array as a big-endian big integer
#             (most natural and common convention). If it is little-endian the
#             byte order would need to be reversed.
#
# ASSUMPTION: _BigOutB16 outputs the result as an uppercase hex string without
#             leading zeros, zero-padded to even length.
#
# ASSUMPTION: d = 0x10001 is used directly as the exponent (as shown in source).
#             In a normal RSA scheme d would be the private exponent, but the
#             author used the public exponent here.

N_HEX = "0AB185AE9243F57C7428B7CE76B62A5E1321CA3A3F966659"  # padded to even length
D_HEX = "10001"

N = int(N_HEX, 16)
D = int(D_HEX, 16)


def _name_to_bignum(name: str) -> int:
    """Convert name string to big integer using _BigInB256 semantics.
    ASSUMPTION: big-endian byte interpretation (first byte = most significant).
    """
    encoded = name.encode('latin-1')  # ASSUMPTION: single-byte encoding
    return int.from_bytes(encoded, byteorder='big')


def keygen(name: str) -> str:
    """Generate the serial for the given name.
    serial = (name_as_bignum ^ D) mod N, output as uppercase hex string.
    """
    if not name:
        raise ValueError("Name must not be empty")
    m = _name_to_bignum(name)
    # ASSUMPTION: m must be less than N for RSA to work correctly
    result = pow(m, D, N)
    # Format as uppercase hex, even number of digits
    hex_result = format(result, 'X')
    if len(hex_result) % 2 != 0:
        hex_result = '0' + hex_result
    return hex_result


def verify(name: str, serial: str) -> bool:
    """Verify that serial matches the expected serial for name.
    Comparison is case-insensitive (hex strings).
    """
    if not name or not serial:
        return False
    expected = keygen(name)
    return expected.upper() == serial.strip().upper()



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
