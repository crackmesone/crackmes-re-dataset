import hashlib
import math


def is_numeric(name: str) -> bool:
    """Return True if all characters in name are digits."""
    return name.isdigit()


def checksum(name: str) -> float:
    """
    Compute the custom checksum of the name string.

    Algorithm (from the C keygen source):
      constant = len * len * len * 5
      sum = 0.0
      for i in 0 .. len-2:
          quotient = sum / (i + 1)
          sum += name[i] + constant
          sum += quotient
          sum = round(sum)   # FRNDINT emulation
      return sum
    """
    length = len(name)
    constant = length * length * length * 5
    total = 0.0
    for i in range(length - 1):
        quotient = total / (i + 1)
        total += ord(name[i]) + constant
        total += quotient
        # Emulate x87 FRNDINT (round half to even, i.e. Python's built-in round)
        total = float(round(total))
    return total


def get_sha256_hash(data: bytes) -> str:
    """Return SHA-256 hash as uppercase hex string (64 chars)."""
    return hashlib.sha256(data).hexdigest().upper()


def keygen(name: str) -> str:
    """
    Generate the serial for the given name.

    Steps:
      1. Validate name length: 5 < len <= 12  (i.e. 6..12)
      2. Name must not be purely numeric.
      3. Compute checksum of name.
      4. Build plaintext = name + str(int(checksum))   ("%.0lf" formatting)
      5. SHA-256 hash the plaintext.
      6. Serial = first NameLength*2 hex chars of the SHA-256 hash (uppercase).
    """
    name_length = len(name)

    # Validation
    if name_length < 6 or name_length > 12:
        raise ValueError(f"Name length must be between 6 and 12, got {name_length}")
    if is_numeric(name):
        raise ValueError("Name must not be purely numeric")

    # Step 3: Checksum
    chksum = checksum(name)
    # "%.0lf" formatting: round to nearest integer, no decimal point
    chksum_str = str(int(round(chksum)))

    # Step 4: Plaintext = Name + Checksum string
    plaintext = name + chksum_str

    # Step 5: SHA-256
    sha256_hex = get_sha256_hash(plaintext.encode('ascii'))

    # Step 6: Take first NameLength*2 characters
    serial = sha256_hex[:name_length * 2]

    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that the serial matches the expected serial for the given name.
    """
    try:
        expected = keygen(name)
    except ValueError:
        return False
    return serial.upper() == expected.upper()



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
