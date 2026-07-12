# crypto_keygenme_2 by byteptr
# Reversed from writeup by kao
#
# The crackme uses Blowfish encryption to validate a (key, serial) pair
# against the Volume Serial Number of the Windows drive.
#
# Flow:
#   1. Get Volume Serial Number (Windows-specific, hardware-dependent)
#   2. Read email, key, serial from dialog
#   3. Convert key and serial strings to DWORDs (decimal -> int)
#   4. Pack [key_dword, serial_dword] into bSomeBuf2
#   5. Call sub_40132F (Blowfish-like encrypt) on bSomeBuf2 -> bSomeBuf3
#   6. Check:
#        bSomeBuf3[0] == VolumeSerialNumber
#        bSomeBuf3[4] == VolumeSerialNumber ^ 0x65747942 ^ 0x00727450
#
# The Blowfish key schedule is seeded with the email address.
# sub_40132F is a standard Blowfish block encrypt of the 64-bit input
# (key_dword || serial_dword) using P-array and S-boxes derived from
# the email via subCreateWeirdBuffer (Blowfish_SetKey).
#
# To KEYGEN:
#   - We need the real Volume Serial Number (hardware value).
#   - We know what bSomeBuf3 must be:
#       bSomeBuf3[0] = VSN
#       bSomeBuf3[1] = VSN ^ 0x65747942 ^ 0x00727450
#   - We Blowfish-DECRYPT bSomeBuf3 with the email-derived key
#     to recover bSomeBuf2 = [key_dword, serial_dword]
#   - Output key_dword and serial_dword as decimal strings.
#
# ASSUMPTION: The Blowfish implementation uses standard Blowfish
# (the P-array and S-box constants in the assembly match standard Blowfish
# initial constants, and the loop in sub_40132F matches Blowfish encrypt).
# ASSUMPTION: subCreateWeirdBuffer is standard Blowfish key schedule
# keyed with the email bytes.
# ASSUMPTION: Volume Serial Number must be known at keygen time
# (it is hardware-specific; we cannot determine it without the target machine).
# ASSUMPTION: The 'aByteptr' string at 0x40116D contains bytes
# 42 79 74 65 ('Byte') and 50 74 72 00 ('Ptr\0'), giving:
#   dword_aByteptr[0] = 0x65747942  ('eByte' little-endian -> 'Byte' = 0x65747942)
#   dword_aByteptr[4] = 0x00727450  ('Ptr\0' = 0x00727450)
# From the writeup: xor eax, 65747942h / xor eax, 00727450h

try:
    from Crypto.Cipher import Blowfish as _BF
    import struct

    def _blowfish_encrypt_ecb(key_bytes, data_bytes):
        """Encrypt a single 8-byte block with Blowfish ECB."""
        cipher = _BF.new(key_bytes, _BF.MODE_ECB)
        return cipher.encrypt(data_bytes)

    def _blowfish_decrypt_ecb(key_bytes, data_bytes):
        """Decrypt a single 8-byte block with Blowfish ECB."""
        cipher = _BF.new(key_bytes, _BF.MODE_ECB)
        return cipher.decrypt(data_bytes)

    _PYCRYPTO_AVAILABLE = True
except ImportError:
    _PYCRYPTO_AVAILABLE = False


# ASSUMPTION: The volume serial number must be supplied externally.
# On a real Windows machine this would come from GetVolumeInformation.
# Default to 0 for testing; override as needed.
DEFAULT_VSN = 0x00000000  # <-- Set this to your actual Volume Serial Number

# Constants from disassembly ("aByteptr" string)
BYTEPTR_DWORD0 = 0x65747942  # 'Byte' in little-endian ASCII
BYTEPTR_DWORD1 = 0x00727450  # 'Ptr\0' in little-endian ASCII


def _compute_expected_somebuf3(vsn):
    """
    Compute what bSomeBuf3 must contain for a given Volume Serial Number.
    From the check:
      bSomeBuf3[0] == vsn
      bSomeBuf3[4] == vsn ^ BYTEPTR_DWORD0 ^ BYTEPTR_DWORD1
    """
    val0 = vsn & 0xFFFFFFFF
    val1 = (vsn ^ BYTEPTR_DWORD0 ^ BYTEPTR_DWORD1) & 0xFFFFFFFF
    return struct.pack('<II', val0, val1)


def _validate_email(email):
    """Basic email check: length >= 5, contains '@' and '.'."""
    return len(email) >= 5 and '@' in email and '.' in email


def verify(name, serial, vsn=DEFAULT_VSN):
    """
    Verify (name=email, serial) pair.
    'serial' should be a string of the form 'KEY SERIAL' (two decimal numbers
    separated by a space) or a tuple (key_str, serial_str).
    
    ASSUMPTION: 'name' is the email address used as Blowfish key.
    ASSUMPTION: vsn is the Volume Serial Number of the target machine.
    """
    if not _PYCRYPTO_AVAILABLE:
        raise RuntimeError("pycryptodome is required: pip install pycryptodome")

    if not _validate_email(name):
        return False

    # Parse serial
    if isinstance(serial, (tuple, list)):
        key_str, ser_str = serial[0], serial[1]
    elif isinstance(serial, str) and ' ' in serial:
        parts = serial.split()
        if len(parts) != 2:
            return False
        key_str, ser_str = parts
    else:
        return False

    try:
        key_dword = int(key_str) & 0xFFFFFFFF
        ser_dword = int(ser_str) & 0xFFFFFFFF
    except ValueError:
        return False

    # Pack bSomeBuf2 = [key_dword, serial_dword] little-endian
    somebuf2 = struct.pack('<II', key_dword, ser_dword)

    # Blowfish encrypt with email as key
    email_bytes = name.encode('ascii', errors='ignore')
    encrypted = _blowfish_encrypt_ecb(email_bytes, somebuf2)

    # Parse bSomeBuf3
    out0, out1 = struct.unpack('<II', encrypted)

    # Check against VSN
    expected0 = vsn & 0xFFFFFFFF
    expected1 = (vsn ^ BYTEPTR_DWORD0 ^ BYTEPTR_DWORD1) & 0xFFFFFFFF

    return out0 == expected0 and out1 == expected1


def keygen(name, vsn=DEFAULT_VSN):
    """
    Generate a valid (key, serial) pair for the given email address and VSN.
    Returns serial as string 'KEY SERIAL'.
    
    ASSUMPTION: We Blowfish-decrypt the target bSomeBuf3 to get bSomeBuf2.
    ASSUMPTION: The resulting key_dword and serial_dword are printed as
    decimal strings (no letters), matching what subDecToDWORD expects.
    ASSUMPTION: vsn is the Volume Serial Number of the target machine.
    """
    if not _PYCRYPTO_AVAILABLE:
        raise RuntimeError("pycryptodome is required: pip install pycryptodome")

    if not _validate_email(name):
        raise ValueError("Invalid email address")

    # Compute required output of Blowfish encrypt
    target_buf3 = _compute_expected_somebuf3(vsn)

    # Blowfish DECRYPT to get bSomeBuf2
    email_bytes = name.encode('ascii', errors='ignore')
    somebuf2 = _blowfish_decrypt_ecb(email_bytes, target_buf3)

    key_dword, ser_dword = struct.unpack('<II', somebuf2)

    # Return as decimal strings
    return f"{key_dword} {ser_dword}"



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
