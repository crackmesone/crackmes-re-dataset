#!/usr/bin/env python3
"""
KeygenMe Nr.2 by dihux / the_hoax
Reverse-engineered from solution writeups by KernelJ and andrewl.

Product key format: 37911-DIHUX-62119-FUNNY-XXXXX
  - GroupA = '37911' (digits 0-9, fixed)
  - GroupB = 'DIHUX' (chars C-X, fixed)
  - GroupC = '62119' (digits 0-9, fixed)
  - GroupD = 'FUNNY' (chars C-X, decrypted from hardcoded bytes, fixed)
  - GroupE = any 5 hex chars (free)

Activation key format: 2-<B>
  where B = (K * N - S2) mod (P-1), all in big integers (base 16)

Constants recovered from andrewl's keygen.cpp:
  P  = 0xCBEC5F1F97FB14C803CB  (prime)
  P1 = P - 1 = 0xCBEC5F1F97FB14C803CA
  R  = 0x1BBE0FE2BADBB5B5854   (the 'R' from keygen: 2^R = X mod P)
  S2 = 0x3E8D7E69A6195CC4FAD6  (2*S mod P-1)
  B  = R*N + (-S2) mod P-1  (negify S_ means subtract)

The activation code the keygen produces is: '2-' + hex(B)

NOTE: The product key is essentially fixed for any name:
  37911-DIHUX-62119-FUNNY-<5 free hex chars>
The activation key depends on name (via N = bignum(name)).
"""

def _bytes_to_big(b: bytes) -> int:
    """Convert raw bytes to big integer (big-endian)."""
    result = 0
    for byte in b:
        result = (result << 8) | byte
    return result


# Constants from andrewl's keygen.cpp (hex strings, MIRACL IOBASE=16)
P1 = int('CBEC5F1F97FB14C803CA', 16)  # P - 1
R  = int('1BBE0FE2BADBB5B5854',  16)  # R such that 2^R = X (mod P)
S2 = int('3E8D7E69A6195CC4FAD6', 16)  # 2*S (mod P-1)


def _compute_activation_b(name: str) -> int:
    """
    B = R*N - 2*S  (mod P-1)
    where N = bignum(name bytes, big-endian)
    """
    N = _bytes_to_big(name.encode('ascii'))
    # mad(R, N, S_, P_, P_, B) with negify(S_) means:
    # B = R*N + (-S2) mod P-1  =  (R*N - S2) mod P-1
    B = (R * N - S2) % P1
    return B


def keygen(name: str) -> dict:
    """
    Generate product key and activation key for a given name.
    Returns dict with 'product' and 'activation' keys.

    Constraints:
      - 4 < len(name) <= 20
    """
    if len(name) <= 4:
        raise ValueError('Name must be longer than 4 characters')
    if len(name) > 20:
        raise ValueError('Name must be at most 20 characters')

    # Product key is essentially fixed (GroupE can be any 5 hex chars)
    # ASSUMPTION: GroupE is arbitrary; we use '00000' as placeholder
    product = '37911-DIHUX-62119-FUNNY-00000'

    B = _compute_activation_b(name)
    activation = '2-' + format(B, 'X')

    return {'product': product, 'activation': activation}


def verify(name: str, serial: str) -> bool:
    """
    Verify activation serial for a given name.

    The serial should be in the format: '2-<HEXSTRING>'
    where HEXSTRING = hex(R*N - 2*S mod P-1), N=bignum(name)

    Product key verification (fixed checks) is also noted but
    not fully re-implemented here since the product key is essentially
    constant (37911-DIHUX-62119-FUNNY-XXXXX).

    ASSUMPTION: Only the activation key math is verified here;
    the product key RC4-like buffer check and bignum cube check
    are not fully re-implemented.
    """
    if len(name) <= 4 or len(name) > 20:
        return False

    # Serial must start with '2-'
    if not serial.startswith('2-'):
        return False

    hex_part = serial[2:]
    if not hex_part:
        return False

    try:
        B_given = int(hex_part, 16)
    except ValueError:
        return False

    B_expected = _compute_activation_b(name)
    return B_given == B_expected



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
