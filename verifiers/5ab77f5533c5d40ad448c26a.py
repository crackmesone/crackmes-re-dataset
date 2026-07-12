import hashlib
import struct

# RSA-like scheme using MIRACL big numbers
# Based on the writeup by Cyclops for pallas by [_j_]
#
# The algorithm:
# 1. Get VolumeSerialNumber (Windows-specific, hardcoded here for keygen demo)
# 2. Convert serial number to hex string via sprintf("%x", vsn)
# 3. hash = SHA1(hex_string_of_vsn)
# 4. Convert hash bytes to bignum Big4 (bytes_to_big, 8 bytes used per writeup)
# 5. Big4 = pow(Big4, 7, Big5)  -- Big5 is the RSA modulus n
# 6. Read user serial, convert to bignum Big3
# 7. Big6 = pow(Big3, Big1, Big2)  -- Big1 is public exponent e, Big2 is modulus
# 8. Compare Big6 == Big4
#
# NOTE: The writeup says:
#   - Big1 = RSA public exponent (e)
#   - Big2 = RSA modulus (n) for serial check
#   - Big5 = another modulus used for the hash step
#   - The keygen computes: serial = pow(Big4, modinv(Big1, phi(Big2)), Big2)
#
# ASSUMPTION: Big1, Big2, Big5 are partially shown in the writeup.
# The writeup shows Big1 starts with:
#   2B7893403C69D8FEB1C4A36D219298438722F2CEB82792230A0B9B8F2DD6804D
#   B9E64381AEDC6B070AF501522781368C6D76A176223F98FADBFF5F26B5FBAD81
#   4C62143C2A430667CEDDD19C91F20E8EDCAA2A1773F71A18DA3CFAD34B75A623
#   7243
# but the writeup was TRUNCATED, so Big2 and Big5 are NOT fully known.
#
# ASSUMPTION: The bytes_to_big call uses the first 8 bytes of the SHA1 hash
# (the writeup says 'push 8' before bytes_to_big)
#
# ASSUMPTION: The crackme only runs on the specific Windows machine that
# generated Big4 from its volume serial number. The verify() function below
# accepts the VSN as an integer parameter instead of calling GetVolumeInformationA.

# Partially recovered constants (Big1 is partial, Big2 and Big5 are UNKNOWN)
# ASSUMPTION: These are placeholders; real values must be extracted from the binary
# via OllyDbg as described in the writeup.
Big1 = int(
    "2B7893403C69D8FEB1C4A36D219298438722F2CEB82792230A0B9B8F2DD6804D"
    "B9E64381AEDC6B070AF501522781368C6D76A176223F98FADBFF5F26B5FBAD81"
    "4C62143C2A430667CEDDD19C91F20E8EDCAA2A1773F71A18DA3CFAD34B75A623"
    "7243",
    16
)
# ASSUMPTION: Big2 and Big5 are unknown due to writeup truncation
Big2 = None  # RSA modulus for serial verification (UNKNOWN - truncated writeup)
Big5 = None  # Modulus for hash transform step (UNKNOWN - truncated writeup)

E_HASH = 7  # exponent used in hash transform step (from 'push 7' -> _power call)


def get_hash_bignum(volume_serial_number: int) -> int:
    """
    Steps 1-4 of the algorithm:
    - Format VSN as hex string (no 0x prefix, lowercase, no leading zeros)
    - SHA1 hash it
    - Take first 8 bytes of hash, convert to big-endian integer (bytes_to_big)
    """
    # sprintf("%x", VolumeSerialNumber) -- lowercase hex, no prefix
    vsn_hex_str = "%x" % volume_serial_number
    vsn_bytes = vsn_hex_str.encode('ascii')

    sha1 = hashlib.sha1()
    sha1.update(vsn_bytes)
    digest = sha1.digest()  # 20 bytes

    # ASSUMPTION: bytes_to_big uses first 8 bytes in big-endian order
    # (push 8 was seen before bytes_to_big call)
    hash_int = int.from_bytes(digest[:8], 'big')
    return hash_int


def compute_target(volume_serial_number: int) -> int:
    """
    Computes the target value that the serial must match:
    Big4 = pow(hash_bignum, 7, Big5)
    """
    if Big5 is None:
        raise NotImplementedError(
            "Big5 (hash modulus) is unknown due to truncated writeup. "
            "Extract it from the binary using OllyDbg at the cinstr call."
        )
    big4 = get_hash_bignum(volume_serial_number)
    big4 = pow(big4, E_HASH, Big5)
    return big4


def verify(name: str, serial: str, volume_serial_number: int = 0) -> bool:
    """
    Verify a serial number for the given volume serial number.
    NOTE: 'name' is not used in the algorithm (the crackme is machine-locked,
    not name-based). It is kept in the signature for interface compatibility.
    ASSUMPTION: name is unused based on the writeup which only mentions VSN.
    """
    if Big1 is None or Big2 is None or Big5 is None:
        raise NotImplementedError(
            "Big1 (partial), Big2, and Big5 are not fully known. "
            "Extract them from the binary with OllyDbg."
        )

    try:
        # Convert serial (hex string) to bignum Big3
        big3 = int(serial.strip(), 16)
    except ValueError:
        return False

    # Compute target: Big4 = pow(hash, 7, Big5)
    big4 = compute_target(volume_serial_number)

    # Big6 = pow(Big3, Big1, Big2)
    big6 = pow(big3, Big1, Big2)

    return big6 == big4


def modinv(a: int, m: int) -> int:
    """Extended Euclidean algorithm to compute modular inverse."""
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise ValueError("Modular inverse does not exist")
    return x % m


def extended_gcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x


def keygen(name: str, volume_serial_number: int = 0) -> str:
    """
    Generate a valid serial for the given volume serial number.
    Algorithm:
      1. Compute Big4 = pow(SHA1_hash(hex(VSN))[:8], 7, Big5)
      2. Factorize Big2 to get phi(Big2) -- ASSUMPTION: Big2 = p*q (RSA)
      3. d = modinv(Big1, phi(Big2))
      4. serial = pow(Big4, d, Big2)
    NOTE: 'name' is unused (machine-locked crackme).
    ASSUMPTION: Big2 is a product of two primes p and q (standard RSA).
    ASSUMPTION: phi(Big2) is unknown without factoring Big2 or having p,q.
    """
    if Big2 is None or Big5 is None:
        raise NotImplementedError(
            "Big2 and Big5 are unknown due to truncated writeup. "
            "Extract them from the binary using OllyDbg as described in the writeup,\n"
            "then factor Big2 (or recover p,q) to compute phi(Big2) = (p-1)*(q-1),\n"
            "then compute d = modinv(Big1, phi(Big2)),\n"
            "then serial = hex(pow(Big4, d, Big2))."
        )

    big4 = compute_target(volume_serial_number)

    # ASSUMPTION: phi_big2 must be known (requires factoring Big2 or having p,q)
    # phi_big2 = (p - 1) * (q - 1)
    # ASSUMPTION: placeholder - replace with actual phi(Big2)
    raise NotImplementedError(
        "phi(Big2) is required to compute the private exponent d. "
        "Factor Big2 to recover it."
    )

    # Unreachable but shows the intended computation:
    # d = modinv(Big1, phi_big2)
    # serial_int = pow(big4, d, Big2)
    # return hex(serial_int)[2:].upper()



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
