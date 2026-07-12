import hashlib
import struct
import itertools
import random
import string

# CRC16-CCITT (initial value 0xFFFF, poly 0x1021)
def crc16_ccitt(data: bytes, init: int = 0xFFFF) -> int:
    crc = init
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest().upper()


# ASSUMPTION: big-integer multiplication is standard Python integer multiplication
# ASSUMPTION: Str2Big converts a hex string to a Python integer
# ASSUMPTION: big2HexEx converts the big integer result to a hex string (byte-swapped/big-endian)
# The assembly shows: result = MD5(key_hex) * 0x11DE784A * 0x11DE784A
# Then CRC16 of that result string is compared to CRC16 of the name.

MULTIPLIER = 0x11DE784A


def compute_serial_hash(serial_str: str) -> int:
    """Compute CRC16 of the big-integer result derived from MD5 of the serial."""
    # Get MD5 of the 16-char serial (as ASCII bytes)
    md5_hex_str = md5_hex(serial_str.encode('ascii'))
    # ASSUMPTION: Str2Big parses the MD5 hex string as a big integer
    md5_int = int(md5_hex_str, 16)
    # Multiply twice by 11DE784A
    result_int = md5_int * MULTIPLIER * MULTIPLIER
    # ASSUMPTION: big2HexEx produces an uppercase hex string of the result (no leading zeros trimmed)
    result_hex = format(result_int, 'X')
    # Compute CRC16 of that hex string as ASCII bytes
    return crc16_ccitt(result_hex.encode('ascii'))


def compute_name_hash(name: str) -> int:
    return crc16_ccitt(name.encode('ascii'))


def verify(name: str, serial: str) -> bool:
    """Check if the serial is valid for the given name."""
    if len(serial) != 16:
        return False
    name_crc = compute_name_hash(name)
    serial_crc = compute_serial_hash(serial)
    return name_crc == serial_crc


# Keygen strategy: brute-force over hex chars 'a'-'f' (as noted in writeup)
# Since CRC16 has 65536 possible values, collisions are easy to find.
# We generate random 16-char hex strings until CRC16 matches.

CHARSET = 'abcdef'


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    target_crc = compute_name_hash(name)
    # Try random 16-char strings from 'a'-'f' (as the author did)
    # ASSUMPTION: key is exactly 16 hex chars (lowercase a-f)
    attempts = 0
    while True:
        candidate = ''.join(random.choices(CHARSET, k=16))
        if compute_serial_hash(candidate) == target_crc:
            return candidate
        attempts += 1
        if attempts > 2_000_000:
            # Fallback: try 'a'-'f' + '0'-'9'
            candidate = ''.join(random.choices(string.hexdigits[:16].lower(), k=16))
            if compute_serial_hash(candidate) == target_crc:
                return candidate



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
