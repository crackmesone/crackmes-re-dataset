# Reverse-engineered from greeneye crackme by freesoul
# Based on the writeup tut.txt
#
# The crackme uses RSA to validate a serial.
# Known constants from the binary:
#   N = 34635909423724510763859457992932165648710947611467118203801379129711257194721
#   E = 132479505
#   C = 8382173512113752806825395558955981828336979140938946849912911380411769562975
#
# Validation steps (from writeup):
# 1. Name must only contain chars: A-Z, a-z, 0-9, '-', '_'
# 2. A buffer is computed from name XOR serial chars, mod 10, + 0x30 ('0')
#    i.e. each output_byte = ((name[i % len(name)] XOR serial[i % len(serial)]) % 10) + ord('0')
#    This produces a numeric string.
# 3. That numeric string is converted to a big integer M.
# 4. RSA check: M^E mod N == C  (verify)
#    Or equivalently for keygen: serial is derived so that the buffer encodes C^(1/E) mod N
#    i.e. M = C^D mod N where D = modular inverse of E mod phi(N)
#
# ASSUMPTION: The XOR loop uses serial chars cycling over the derived buffer length.
#   Specifically: buffer[i] = ((ord(name[i % name_len]) ^ ord(serial[i % serial_len])) % 10) + ord('0')
#   and the resulting buffer string, interpreted as an integer, when raised to E mod N equals C.
# ASSUMPTION: The buffer length equals the length of the serial (or is determined by the serial length).
# ASSUMPTION: phi(N) is not directly given; keygen requires factoring N or knowing the private key D.
#   The writeup does not provide D or phi(N), so full keygen is not possible without factoring.
# ASSUMPTION: The name validation loop uses ESI cycling back to 0 when it reaches len(name),
#   meaning name chars are used cyclically for the XOR.

import re

N = 34635909423724510763859457992932165648710947611467118203801379129711257194721
E = 132479505
C = 8382173512113752806825395558955981828336979140938946849912911380411769562975

VALID_CHARS = re.compile(r'^[A-Za-z0-9\-_]+$')


def _is_valid_name(name: str) -> bool:
    return bool(name) and bool(VALID_CHARS.match(name))


def _is_valid_serial(serial: str) -> bool:
    return bool(serial) and bool(VALID_CHARS.match(serial))


def _compute_buffer(name: str, serial: str) -> str:
    """
    XOR each name[i % name_len] with serial[i % serial_len],
    take mod 10, add ord('0').
    Buffer length = len(serial).
    ASSUMPTION: buffer length equals serial length.
    """
    name_len = len(name)
    serial_len = len(serial)
    buf = []
    for i in range(serial_len):
        n_char = ord(name[i % name_len])
        s_char = ord(serial[i % serial_len])
        val = ((n_char ^ s_char) % 10) + ord('0')
        buf.append(chr(val))
    return ''.join(buf)


def verify(name: str, serial: str) -> bool:
    """
    Returns True if the serial is valid for the given name.
    """
    if not _is_valid_name(name):
        return False
    if not _is_valid_serial(serial):
        return False

    buf = _compute_buffer(name, serial)

    # Convert buffer string to integer
    try:
        M = int(buf)
    except ValueError:
        return False

    # RSA check: M^E mod N == C
    return pow(M, E, N) == C


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    To keygen:
    1. We need M such that M^E ≡ C (mod N), i.e. M = C^D mod N
       where D = modular_inverse(E, phi(N)).
    2. ASSUMPTION: phi(N) is unknown without factoring N.
       We cannot fully compute D here.
    3. Even if M is known, we need to find serial chars such that
       ((name[i%name_len] XOR serial[i%serial_len]) % 10) + 48 == digit_i of M.
       => serial[i] = name[i%name_len] XOR ((digit_val_i) + k*10) for some k
       where digit_val_i = ord(M_str[i]) - 48.
       We need to pick k such that the XOR result is a valid char.

    ASSUMPTION: N = p*q with p, q prime. Without knowing the factorization,
    we provide a brute-force modular inverse attempt using sympy if available,
    otherwise raise NotImplementedError.
    """
    if not _is_valid_name(name):
        raise ValueError("Invalid name")

    # Try to compute phi(N) via sympy factorization
    try:
        from sympy import factorint
        factors = factorint(N)
        phi = 1
        for p, exp in factors.items():
            phi *= (p - 1) * (p ** (exp - 1))
        D = pow(E, -1, phi)
        M = pow(C, D, N)
    except Exception as ex:
        raise NotImplementedError(
            f"Cannot compute private key D without factoring N: {ex}\n"
            "N = {N}"
        )

    M_str = str(M)
    serial_len = len(M_str)  # ASSUMPTION: serial length equals buffer length equals len(M_str)
    name_len = len(name)
    serial_chars = []

    for i in range(serial_len):
        digit_val = ord(M_str[i]) - ord('0')  # 0..9
        n_char = ord(name[i % name_len])
        # We need: (n_char XOR s_char) % 10 == digit_val
        # Try to find s_char in valid range that satisfies this
        found = None
        for s_char in range(256):
            candidate_char = chr(s_char)
            if not VALID_CHARS.match(candidate_char):
                continue
            if (n_char ^ s_char) % 10 == digit_val:
                found = candidate_char
                break
        if found is None:
            # ASSUMPTION: fallback - use digit char directly (may not be valid)
            found = str(digit_val)
        serial_chars.append(found)

    serial = ''.join(serial_chars)
    # Verify before returning
    if not verify(name, serial):
        raise RuntimeError("Keygen produced invalid serial - algorithm assumption may be wrong.")
    return serial



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
