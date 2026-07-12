# Cryptok KeygenMe {2} by profdracula
# Reverse-engineered from the solution writeup.
#
# Summary of what the writeup reveals:
#   1. The DLL checks for a file named 'danbrown' in the current directory.
#      The file must be exactly 13 (0x0D) bytes long.
#      Finding it causes two increments of an internal counter.
#   2. The file is then read (13 bytes) and more increments happen (up to 4 total).
#   3. Only when that counter == 4 does the DLL actually read the username/serial
#      from the dialog and validate them.
#   4. The crypto used (identified by KANAL/PEiD) is CRC32 and SHA-256.
#   5. The full serial-validation math is NOT fully described in the writeup
#      (it was truncated at the ReadFile call), so gaps are filled with ASSUMPTIONS.

import hashlib
import struct

# ---------------------------------------------------------------------------
# CRC32 helper (standard)
# ---------------------------------------------------------------------------
def _crc32(data: bytes) -> int:
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF

# ---------------------------------------------------------------------------
# The 'danbrown' file requirement
# The file must exist in CWD and be exactly 13 bytes.
# Its content is read and used in the key-check logic.
# ASSUMPTION: the 13-byte content of 'danbrown' is the 'key material' that
#             is hashed (SHA-256) together with the username to derive the
#             expected serial.
# ---------------------------------------------------------------------------
DANBROWN_FILE = 'danbrown'
DANBROWN_LEN  = 13          # 0x0D


def _read_danbrown() -> bytes:
    """Read the 13-byte 'danbrown' file from CWD."""
    try:
        with open(DANBROWN_FILE, 'rb') as fh:
            data = fh.read()
        if len(data) != DANBROWN_LEN:
            raise ValueError(f"'danbrown' must be exactly {DANBROWN_LEN} bytes")
        return data
    except FileNotFoundError:
        raise FileNotFoundError("'danbrown' file not found in current directory")


# ---------------------------------------------------------------------------
# Serial derivation
# ASSUMPTION: The expected serial is derived as follows:
#   1. Compute SHA-256 of (danbrown_content + username_bytes).
#   2. Compute CRC32 of the username.
#   3. XOR the first 4 bytes of the SHA-256 digest with the CRC32 value.
#   4. Express the final 32-byte (256-bit) value as an uppercase hex string,
#      with the first word replaced by the XOR result.
# This is speculative beyond what the writeup explicitly states.
# ---------------------------------------------------------------------------

def _derive_serial(name: str, danbrown: bytes) -> str:
    """
    ASSUMPTION: serial = uppercase-hex of:
        SHA256(danbrown || name) with first 4 bytes XOR-ed with CRC32(name)
    """
    name_bytes = name.encode('ascii', errors='replace')

    # SHA-256 over file content concatenated with username
    digest = hashlib.sha256(danbrown + name_bytes).digest()

    # CRC32 of username
    crc = _crc32(name_bytes)
    crc_bytes = struct.pack('<I', crc)  # ASSUMPTION: little-endian

    # XOR first 4 bytes
    mixed = bytearray(digest)
    for i in range(4):
        mixed[i] ^= crc_bytes[i]

    return bytes(mixed).hex().upper()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify(name: str, serial: str) -> bool:
    """
    Returns True if serial is valid for the given name.
    Requires 'danbrown' (13-byte file) in the current directory.
    """
    try:
        danbrown = _read_danbrown()
    except (FileNotFoundError, ValueError) as exc:
        print(f'[!] Prerequisite not met: {exc}')
        return False

    expected = _derive_serial(name, danbrown)
    # ASSUMPTION: comparison is case-insensitive
    return serial.strip().upper() == expected.upper()


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name.
    Requires 'danbrown' (13-byte file) in the current directory.
    """
    danbrown = _read_danbrown()
    return _derive_serial(name, danbrown)


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

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
