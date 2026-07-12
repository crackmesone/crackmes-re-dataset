from hashlib import sha1
import os
import base64

# Elliptic curve parameters from the keygen source
# Curve: y^2 = x^3 + a*x + b mod p
a = 0x3A5C2EA6DBC2B8743BCC7F8E41D5C014247BC269
b = 0x330B45FB89841E4FB9EFC5E1F0D1FC18A55853A4
p = 0x86ED17A02A08E5EBD2B428612B10BA391C803FDF
n = 0x86ED17A02A08E5EBD2B428612B10BA391C803FDF  # same as p (anomalous curve!)

# Generator point G (EP1)
# bytes_EP1x = {0x6A, 0x42} => Gx = 0x6A42
# bytes_EP1y = {0x60,0x41,0xAA,0x60,0x1D,0x01,0x5B,0xD7,0x54,0xE0,0x01,0xC0,0xE0,0xA2,0xA1,0xCB,0xAA,0x62,0xF2,0xC7}
Gx = 0x6A42
Gy = 0x6041AA601D015BD754E001C0E0A2A1CBAA62F2C7

# Public key point Q (EP2)
# bytes_EP2x
Qx = 0x7A7EDF4DF9A06083F22DE61CE339A86815E08B2C
# bytes_EP2y
Qy = 0x4A68C352654B4177D5D18FBB74751B7709D0A36D

# Private key (from keygen source)
pk_hex = "21043BADFD4715E6F8221311B09652B4E1"
private_key = int(pk_hex, 16)

def modinv(x, m):
    return pow(x, -1, m)

def point_add(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if y1 != y2 or y1 == 0:
            return None
        # Point doubling
        lam = (3 * x1 * x1 + a) * modinv(2 * y1, p) % p
    else:
        lam = (y2 - y1) * modinv(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def point_mul(k, P, a, p):
    R = None
    Q_pt = P
    while k > 0:
        if k & 1:
            R = point_add(R, Q_pt, a, p)
        Q_pt = point_add(Q_pt, Q_pt, a, p)
        k >>= 1
    return R

def sha1_bytes(data: bytes) -> bytes:
    return sha1(data).digest()

def keygen(name: str) -> str:
    """
    Implements the keygen logic from keygen.c:
    1. Pick random r mod p
    2. T = r*G; get Tx
    3. sign1 = SHA1(Tx_bytes)
    4. hash1 = SHA1(EP2x_bytes || EP2y_bytes || name_bytes)
    5. combined = sign1 XOR hash1
    6. bt1 = combined mod p
    7. sign2 = (r - bt1) * modinv(pk, n) mod p
    8. Encode [len_sign1, sign1_bytes, len_sign2, sign2_bytes] as base64
    """
    name_bytes = name.encode('latin-1')

    G = (Gx, Gy)

    # Step 1: random r
    r = int.from_bytes(os.urandom(20), 'big') % p
    if r == 0:
        r = 1

    # Step 2: T = r * G
    T = point_mul(r, G, a, p)
    if T is None:
        return keygen(name)
    Tx, Ty = T

    # Step 3: sign1 = SHA1(Tx as 20 bytes big-endian)
    Tx_bytes = Tx.to_bytes(20, 'big')
    hash_val = sha1_bytes(Tx_bytes)
    sign1_int = int.from_bytes(hash_val, 'big')

    # Step 4: hash1 = SHA1(EP2x_bytes || EP2y_bytes || name_bytes)
    EP2x_bytes = Qx.to_bytes(20, 'big')
    EP2y_bytes = Qy.to_bytes(20, 'big')
    h1 = sha1(EP2x_bytes + EP2y_bytes + name_bytes).digest()
    hash1_int = int.from_bytes(h1, 'big')

    # Step 5 & 6: XOR and mod p
    combined = sign1_int ^ hash1_int
    bt1 = combined % p

    # Step 7: sign2 = (r - bt1) * modinv(pk, n) mod p
    pk_inv = modinv(private_key, n)
    sign2_int = ((r - bt1) * pk_inv) % p
    # The code does add(bt1,p,bt1); divide(bt1,p,p) which is just mod p
    sign2_int = sign2_int % p

    # Step 8: encode
    sign1_bytes = sign1_int.to_bytes(20, 'big').lstrip(b'\x00')
    if not sign1_bytes:
        sign1_bytes = b'\x00'
    sign2_bytes = sign2_int.to_bytes(20, 'big').lstrip(b'\x00')
    if not sign2_bytes:
        sign2_bytes = b'\x00'

    len1 = len(sign1_bytes)
    len2 = len(sign2_bytes)

    # Build tmp2: [len1, sign1..., len2, sign2...]
    tmp2 = bytes([len1]) + sign1_bytes + bytes([len2]) + sign2_bytes

    # Encode as base64 (MIRACL cotstr with IOBASE=64 produces base64-like output)
    serial = base64.b64encode(tmp2).decode('ascii')
    return serial


def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The crackme verifies the serial by checking that
    pk * sign2 + bt1 == r (mod p), and that sign1 == SHA1(Tx)
    where Tx comes from sign1 (sign1 IS SHA1(Tx)), so the verify
    would re-derive bt1 from name and check consistency.
    
    Since we don't have the verifier source, this implements a
    plausibility check using the known private key.
    """
    try:
        data = base64.b64decode(serial)
    except Exception:
        return False

    if len(data) < 4:
        return False

    # Parse tmp2
    idx = 0
    len1 = data[idx]; idx += 1
    if idx + len1 > len(data):
        return False
    sign1_bytes = data[idx:idx+len1]; idx += len1
    len2 = data[idx]; idx += 1
    if idx + len2 > len(data):
        return False
    sign2_bytes = data[idx:idx+len2]

    sign1_int = int.from_bytes(sign1_bytes, 'big')
    sign2_int = int.from_bytes(sign2_bytes, 'big')

    # Compute hash1 from name
    name_bytes = name.encode('latin-1')
    EP2x_bytes = Qx.to_bytes(20, 'big')
    EP2y_bytes = Qy.to_bytes(20, 'big')
    h1 = sha1(EP2x_bytes + EP2y_bytes + name_bytes).digest()
    hash1_int = int.from_bytes(h1, 'big')

    # bt1 = (sign1 XOR hash1) mod p
    combined = sign1_int ^ hash1_int
    bt1 = combined % p

    # ASSUMPTION: r = pk * sign2 + bt1 mod p
    # Then verify T = r*G has SHA1(Tx) == sign1
    r_recovered = (private_key * sign2_int + bt1) % p

    G = (Gx, Gy)
    T = point_mul(r_recovered, G, a, p)
    if T is None:
        return False
    Tx, Ty = T
    Tx_bytes = Tx.to_bytes(20, 'big')
    expected_sign1 = int.from_bytes(sha1_bytes(Tx_bytes), 'big')

    return expected_sign1 == sign1_int



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
