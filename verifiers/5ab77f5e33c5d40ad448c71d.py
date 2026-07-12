# Reverse-engineered keygen for 'ownme..._keygen_me_please' by freesoul
# Based on the partial assembly writeup. The algorithm uses:
#   1. CRC32 of the name
#   2. A XOR-sum of adjacent bytes in the name
#   3. RSA32 modular exponentiation: c = xorsum^e mod n
#   4. Division: c = c // 0x989680
#   5. Linear transform on the result
#   6. TEA encryption of two 32-bit words
#   7. Final serial formatted as '%08X-%08X-%s'
#
# RSA parameters (from .data section):
#   e  = 0xFE7
#   n  = 0x41B6D7121
#   u  = 0x5F5E100  (unused in keygen path shown)
#   e2 = 0x20
#   d  = 0x26D22AAD3
#
# TEA key (from .data):
#   tea_key = [0x00FE0FE0, 0x60817714, 0x70777777, 0xB3197311]
#
# NOTE: The writeup is truncated so parts of the final serial assembly
# (TEA encoding step and format string usage) are reconstructed with assumptions.

import struct
import ctypes

# CRC32 table (standard CRC32 / IEEE 802.3)
def make_crc32_table():
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        table.append(crc)
    return table

CRC32_TABLE = make_crc32_table()

def crc32(data: bytes) -> int:
    """Compute CRC32, returns unsigned 32-bit value."""
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ CRC32_TABLE[(crc ^ b) & 0xFF]
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF


def xor_adjacent_sum(name: str) -> int:
    """XOR each pair of adjacent chars and sum, as shown in namecalc loop."""
    data = name.encode('latin-1')
    length = len(data)
    total = 0
    # loop: for edx in range(length): eax = data[edx+1] ^ data[edx]; total += eax
    # Note: data[edx+1] when edx == length-1 reads one past end -> 0 (null terminator)
    for i in range(length):
        c0 = data[i]
        c1 = data[i + 1] if i + 1 < length else 0
        total += (c0 ^ c1)
    return total & 0xFFFFFFFF


# RSA parameters
E = 0xFE7
N = 0x41B6D7121

# TEA parameters
TEA_KEY = [0x00FE0FE0, 0x60817714, 0x70777777, 0xB3197311]
TEA_DELTA = 0x9E3779B9
TEA_ROUNDS = 32

def tea_encrypt(v0: int, v1: int, key: list) -> tuple:
    """TEA encryption of two 32-bit words."""
    mask = 0xFFFFFFFF
    s = 0
    for _ in range(TEA_ROUNDS):
        s = (s + TEA_DELTA) & mask
        v0 = (v0 + (((v1 << 4) + key[0]) ^ (v1 + s) ^ ((v1 >> 5) + key[1]))) & mask
        v1 = (v1 + (((v0 << 4) + key[2]) ^ (v0 + s) ^ ((v0 >> 5) + key[3]))) & mask
    return v0, v1


# Global counter used in serial calculation (snn); starts at 0
# ASSUMPTION: snn resets to 0 each run; we use 0 as default.
_snn = 0

def _calc_serial_inner(name: str, snn: int = 0):
    """Core serial calculation, returns (dw1, part2, part3_str) and new snn."""
    mask32 = 0xFFFFFFFF

    # Step 1: CRC32 of the name buffer
    name_bytes = name.encode('latin-1') + b'\x00'  # null-terminated buffer
    dw1 = crc32(name_bytes[:-1])  # CRC32 of name (without null, matching GetDlgItemText length)
    # ASSUMPTION: CRC32 is computed over the name characters only (no null), matching 'eax' = string length.

    # Step 2: XOR-adjacent-byte sum -> dw3
    xorsum = xor_adjacent_sum(name)

    # Step 3: RSA: c = xorsum^E mod N
    c = pow(xorsum, E, N)

    # Step 4: c = c // 0x989680 (integer division, BigDiv32)
    c2 = c // 0x989680

    # Step 5: convert c2 to hex string, parse as int (hex2intp)
    hex_str = format(c2, 'X')  # uppercase hex
    # hex2intp parses the hex string back to integer
    c3 = int(hex_str, 16) if hex_str else 0

    # Step 6: lea eax, [eax+eax+0x20092010]  i.e.  eax = c3*2 + 0x20092010
    dw3 = (c3 * 2 + 0x20092010) & mask32

    # Step 7: compute eax = dw3 XOR dw1 XOR (snn + 0x00401AD5)
    edx = (snn + 0x00401AD5) & mask32
    eax = (dw3 ^ dw1 ^ edx) & mask32

    # Update snn
    new_snn = snn + 1
    if new_snn == 0x0B:
        new_snn = 0

    # tdata[0] = eax
    tdata0 = eax

    # Step 8: CRC32 of decimal string of tdata[0]
    decimal_str = str(tdata0).encode('latin-1')
    tdata1 = crc32(decimal_str)

    # Step 9: tdata[0] XOR tdata[1] -> dw3 updated
    # ASSUMPTION: based on 'xor eax, edx' in code after tdata[1] is set
    dw3_new = (tdata0 ^ tdata1) & mask32

    # tdata = [tdata0, tdata1]
    # TEA encode tdata with tea_key
    t0, t1 = tea_encrypt(tdata0, tdata1, TEA_KEY)

    # ASSUMPTION: Serial format is '%08X-%08X-%s' where the third part
    # is some derived value. Based on the format string pfx = "%08X-%08X-%s"
    # and partial code, the third part appears to be a hex representation
    # of dw3_new or similar. We use dw3_new as hex string for %s.
    part3 = format(dw3_new, '08X')

    return t0, t1, part3, new_snn


# Serial format: '%08X-%08X-%s'
def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    t0, t1, part3, _ = _calc_serial_inner(name, snn=0)
    serial = f"{t0 & 0xFFFFFFFF:08X}-{t1 & 0xFFFFFFFF:08X}-{part3}"
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair. Regenerates serial and compares."""
    if not name:
        return False
    expected = keygen(name)
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
