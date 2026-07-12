# Reverse-engineered keygen for keygenMe2 by c00lw0lf
# Based on map file and symbol names only - no actual disassembly was provided.
#
# From the map file we can identify:
#   - RSA-style modular exponentiation (Powmod, mirvar, mirsys - MIRACL big-number library)
#   - A hash function (Hash_init, Hash_pad, hash_process)
#   - A stream cipher (StreamCipher)
#   - Public key constants visible in data segment:
#       e = 10001 (hex) = 65537
#       n (modulus) = 0x92b78b3c7dbb28... (truncated in writeup)
#       and 'b567' possibly another constant
#   - The MIRACL library is used for elliptic curves AND RSA,
#     but the primary check appears RSA-based given Powmod + cinstr/cotstr
#
# ASSUMPTION: The algorithm is:
#   1. Hash the username with a custom hash (Hash_init/Hash_pad/hash_process)
#   2. The serial is validated by: serial^e mod n == hash(name)
#      i.e., RSA signature verification where the crackme holds the public key
#      and we need the private key d to generate valid serials.
#
# ASSUMPTION: The modulus n is '92b78b3c7dbb28...' - the full value is TRUNCATED
#   in the writeup so we cannot complete the keygen without the full n.
#
# ASSUMPTION: The hash algorithm is unknown (custom); we only know the symbol names.
#
# ASSUMPTION: The stream cipher (StreamCipher) may XOR the serial or hash before
#   the RSA check - exact usage unknown.
#
# Without the full disassembly/algorithm description, this is a SKELETON only.

import hashlib
import struct

# Public key constants (from data segment symbols in map file)
# ASSUMPTION: e = 0x10001 = 65537
E = 65537

# ASSUMPTION: n starts with 0x92b78b3c7dbb28... but is TRUNCATED - full value unknown
# We cannot perform actual RSA operations without the full modulus.
N_HEX = '92b78b3c7dbb28'  # TRUNCATED - incomplete
N = int(N_HEX, 16)  # This is NOT the real modulus - it is truncated

# Private key d - unknown, cannot be derived without factoring N
# ASSUMPTION: D would be computed as modular inverse of E mod phi(N)
D = None  # UNKNOWN


def custom_hash(name: str) -> int:
    """
    ASSUMPTION: The custom hash (Hash_init/Hash_pad/hash_process) processes
    the username bytes. Exact algorithm unknown - using SHA1 as placeholder.
    The real implementation must be reverse-engineered from the binary.
    """
    # ASSUMPTION: placeholder using SHA-1
    h = hashlib.sha1(name.encode('ascii', errors='replace')).digest()
    return int.from_bytes(h, 'big')


def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: Serial is a hex string representing a big integer S.
    Verification: S^E mod N == hash(name)
    This cannot work correctly because N is truncated.
    """
    if N_HEX == '92b78b3c7dbb28':
        # We don't have the real modulus
        # ASSUMPTION: return False since we can't verify
        raise NotImplementedError(
            'Full modulus N is truncated in the writeup - cannot verify')
    try:
        s = int(serial.replace('-', '').replace(' ', ''), 16)
    except ValueError:
        return False
    h = custom_hash(name)
    result = pow(s, E, N)
    return result == h


def keygen(name: str) -> str:
    """
    ASSUMPTION: To generate a serial, we need the private key D such that:
      serial = hash(name)^D mod N
    Since D is unknown (we don't have the private key and N is truncated),
    this cannot be implemented.
    """
    if D is None:
        raise NotImplementedError(
            'Private key D is unknown - cannot generate serial. '
            'The full modulus N is truncated in the writeup.')
    h = custom_hash(name)
    s = pow(h, D, N)
    return hex(s)[2:].upper()



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
