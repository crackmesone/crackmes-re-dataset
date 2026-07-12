#!/usr/bin/env python3
"""
KeygenMe #1 by saduff (Borland Delphi)
Reverse-engineered from BoRoV's write-up.

Algorithm (as described):

1. XOR each byte of Name with a cycling key table at offsets 0x467734..0x46773B
   (8 bytes, indices 1..8 in the write-up, ebx starts at 1, wraps at 9->1)
   to produce a Blowfish key string.

2. Blowfish-encrypt the Name using that key -> encrypted_name (bytes)

3. ZLib-compress encrypted_name (level=zcDefault, i.e. level 6 / zlib default)
   -> compressed bytes

4. Hex-encode compressed bytes -> hex_str (uppercase or lowercase, ASSUMPTION)

5. Take first 6 chars of hex_str -> some_hex_string (this is the 'expected' token)

6. Serial validation:
   a. Convert input serial from hex string to raw bytes
   b. ZLib-decompress those raw bytes
   c. Blowfish-decrypt the result using the same key derived from Name
   d. Compare decrypted result with some_hex_string
   If equal -> valid serial.

NOTE: The 8-byte XOR table at 0x467734 in the original binary is UNKNOWN.
      We assume a placeholder table below (ASSUMPTION).
      Replace XOR_TABLE with the actual bytes extracted from the binary.
"""

import zlib
import struct
from Crypto.Cipher import Blowfish  # pip install pycryptodome

# ASSUMPTION: The 8-byte XOR table read from address 0x467734 in the binary.
# Bytes at [ebx+0x467733] for ebx=1..8, i.e. table[0..7].
# These must be extracted from the actual crackme binary.
XOR_TABLE = bytes([0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48])  # ASSUMPTION: placeholder


def derive_blowfish_key(name: str) -> bytes:
    """
    XOR each character of name with XOR_TABLE[ebx-1], cycling ebx from 1..8.
    Produces the blowfish key string (same length as name).
    """
    name_bytes = name.encode('latin-1')
    key_bytes = bytearray()
    ebx = 1  # starts at 1, wraps back to 1 when it reaches 9
    for ch in name_bytes:
        xor_val = XOR_TABLE[ebx - 1]  # table[ebx-1]
        key_bytes.append(ch ^ xor_val)
        ebx += 1
        if ebx == 9:
            ebx = 1
    return bytes(key_bytes)


def blowfish_encrypt(data: bytes, key: bytes) -> bytes:
    """
    Blowfish ECB encryption.
    ASSUMPTION: mode is ECB (most common for simple keygenmes).
    Pads data to multiple of 8 bytes with null bytes.
    """
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    # Pad to block size (8 bytes)
    pad_len = (8 - len(data) % 8) % 8
    padded = data + b'\x00' * pad_len
    return cipher.encrypt(padded)


def blowfish_decrypt(data: bytes, key: bytes) -> bytes:
    """
    Blowfish ECB decryption.
    """
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    # Pad to block size if necessary
    pad_len = (8 - len(data) % 8) % 8
    padded = data + b'\x00' * pad_len
    return cipher.decrypt(padded)


def compute_some_hex_string(name: str) -> str:
    """
    Steps 1-5: derive the expected 6-char hex token from the name.
    """
    key = derive_blowfish_key(name)
    name_bytes = name.encode('latin-1')

    # Blowfish encrypt the name
    encrypted_name = blowfish_encrypt(name_bytes, key)

    # ZLib compress (level 6 = default, zcDefault=2 maps to zlib default level)
    # ASSUMPTION: zcDefault in ZLibEx corresponds to zlib compression level -1 (default=6)
    compressed = zlib.compress(encrypted_name, level=6)

    # Hex-encode
    # ASSUMPTION: uppercase hex
    hex_str = compressed.hex().upper()

    # Take first 6 characters
    some_hex_string = hex_str[:6]
    return some_hex_string


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    The serial, when validated, must:
      a. Be decoded from hex -> raw bytes
      b. ZLib decompressed -> intermediate
      c. Blowfish decrypted with key derived from name -> result
      d. result == some_hex_string

    So we construct serial by:
      1. Compute some_hex_string
      2. Blowfish encrypt some_hex_string bytes using the key
      3. ZLib compress the result
      4. Hex-encode -> this is the serial
    """
    key = derive_blowfish_key(name)
    some_hex_string = compute_some_hex_string(name)

    # Blowfish encrypt some_hex_string
    token_bytes = some_hex_string.encode('latin-1')
    encrypted = blowfish_encrypt(token_bytes, key)

    # ZLib compress
    compressed = zlib.compress(encrypted, level=6)

    # Hex encode
    serial = compressed.hex().upper()
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.

    Validation steps (from write-up):
      1. Derive blowfish key from name (XOR with table)
      2. Compute some_hex_string from name (encrypt name, compress, hex, take 6 chars)
      3. Convert serial from hex string to raw bytes
      4. ZLib decompress those bytes
      5. Blowfish decrypt the result using the key
      6. Strip null padding from decrypted result
      7. Compare with some_hex_string
    """
    try:
        key = derive_blowfish_key(name)
        some_hex_string = compute_some_hex_string(name)

        # Step 3: serial hex -> bytes
        try:
            serial_bytes = bytes.fromhex(serial)
        except ValueError:
            return False

        # Step 4: ZLib decompress
        try:
            decompressed = zlib.decompress(serial_bytes)
        except zlib.error:
            return False

        # Step 5: Blowfish decrypt
        decrypted = blowfish_decrypt(decompressed, key)

        # Strip null padding
        decrypted_str = decrypted.rstrip(b'\x00').decode('latin-1')

        # Step 6: Compare
        return decrypted_str == some_hex_string

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
