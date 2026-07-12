#!/usr/bin/env python3
"""
Keygen for 'crypto_namecompanyserial_keygenme' by c0dehaz4rd.

From the solution write-up:
- The serial is AES-encrypted data, base64-encoded (hex-encoded base64 in the sample).
- The key/IV for AES is derived from name + company.
- The plaintext that gets encrypted is some combination of name + company.

Sample:
  name:    ToMKoL
  company: [c4U]
  serial:  4F4E2F32634E5941674943344F796155...

Decoding the serial:
  hex -> bytes -> base64-decode -> AES decrypt -> plaintext

From analysis of the sample serial:
  hex_decode(serial) gives a base64 string
  base64_decode(that) gives AES-CBC encrypted bytes

The AES key and IV must be derived from name+company.

ASSUMPTION: The AES key is derived by hashing or padding name+company.
  From the VB source references (CRijndael class, 256-bit key likely),
  we assume key = (name+company) zero-padded or repeated to 32 bytes,
  and IV = first 16 bytes of key or zero-padded name.

ASSUMPTION: The plaintext encrypted is name+company (or some fixed format).

ASSUMPTION: The serial encoding is: AES_encrypt(plaintext) -> base64 -> hex_encode.

Note: Without the actual VB source of Form1.frm we cannot determine the exact
  key derivation or plaintext. The below is our best reconstruction.
"""

import base64
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def derive_key_iv(name: str, company: str):
    # ASSUMPTION: key is name+company encoded as bytes, padded/truncated to 32 bytes
    combined = (name + company).encode('latin-1')
    key = (combined * ((32 // len(combined)) + 1))[:32]
    # ASSUMPTION: IV is first 16 bytes of key
    iv = key[:16]
    return key, iv


def derive_plaintext(name: str, company: str) -> bytes:
    # ASSUMPTION: plaintext is name+company as a string
    return (name + company).encode('latin-1')


def keygen(name: str, company: str) -> str:
    """
    Generate a serial for the given name and company.
    Returns the serial as an uppercase hex string (as shown in the sample).
    """
    key, iv = derive_key_iv(name, company)
    plaintext = derive_plaintext(name, company)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plaintext, 16))
    b64 = base64.b64encode(encrypted)
    serial = binascii.hexlify(b64).decode('ascii').upper()
    return serial


def verify(name: str, company: str, serial: str) -> bool:
    """
    Verify that serial matches name+company.
    Decodes serial: hex -> base64 -> AES decrypt -> check plaintext.
    """
    try:
        b64 = binascii.unhexlify(serial)
        encrypted = base64.b64decode(b64)
        key, iv = derive_key_iv(name, company)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), 16)
        expected = derive_plaintext(name, company)
        return decrypted == expected
    except Exception:
        return False



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
