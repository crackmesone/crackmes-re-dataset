import hashlib

# RSA private key (computed via: d = e^-1 mod phi(n), where e = 2^16+1)
# n = 0xAD08D0361CC7FE8D1D3EAC5A68394C95 = 230002204674084418548395124071717227669
# d was computed in the writeup's private_key.gp
D = 35066939730281390814817536468479435777
N = 0xAD08D0361CC7FE8D1D3EAC5A68394C95  # modulus n = p*q
E = 2**16 + 1  # public exponent


def _rotm1(s: str) -> bytes:
    """Subtract 1 from each character's ASCII value (ROT-1)."""
    return bytes([ord(c) - 1 for c in s])


def _rsa_encrypt(m: int, e: int, n: int) -> int:
    """RSA encryption: c = m^e mod n"""
    return pow(m, e, n)


def _rsa_decrypt(c: int, d: int, n: int) -> int:
    """RSA decryption: m = c^d mod n"""
    return pow(c, d, n)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.

    Steps:
      1. Apply ROT-1 to username (subtract 1 from each char).
      2. Compute MD5 of the ROT-1'd username.
      3. Replace the first 10 hex chars of the MD5 digest with '5321783072'.
      4. Interpret the resulting 32-char hex string as an integer c.
      5. Compute m = c^d mod n  (RSA decrypt with private key).
      6. Return hex(m) as the serial (without '0x' prefix or 'L' suffix).
    """
    shifted = _rotm1(name)
    md5_hex = hashlib.md5(shifted).hexdigest()          # 32 hex chars
    # Replace first 10 hex chars with fixed prefix '5321783072'
    # ASSUMPTION: this forced prefix ensures c < n so RSA makes sense
    md5_modified = "5321783072" + md5_hex[10:]
    c = int(md5_modified, 16)
    m = _rsa_decrypt(c, D, N)
    serial = hex(m).rstrip('L').lstrip('0x')
    if serial == '':
        serial = '0'
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a (username, serial) pair.

    The crackme checks:  serial^e mod n  == modified_md5_as_int
    i.e. RSA-encrypt the serial and compare to the modified MD5 value.

    Steps:
      1. Apply ROT-1 to username.
      2. Compute MD5 of the ROT-1'd username.
      3. Replace first 10 hex chars with '5321783072'.
      4. Interpret as integer c.
      5. RSA-encrypt the serial: c2 = serial_int^e mod n.
      6. Valid if c2 == c.
    """
    # Compute the expected ciphertext from the username
    shifted = _rotm1(name)
    md5_hex = hashlib.md5(shifted).hexdigest()
    md5_modified = "5321783072" + md5_hex[10:]
    c_expected = int(md5_modified, 16)

    # Parse the provided serial as a hex integer
    try:
        m = int(serial, 16)
    except ValueError:
        return False

    # RSA encrypt the serial and compare
    c_check = _rsa_encrypt(m, E, N)
    return c_check == c_expected



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
