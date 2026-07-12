# Reconstruction of hmx0101's Keygenme #5 validation algorithm
# Based on ToMKoL's writeup. The keygenme is BUGGED (CRC32 reads out-of-bounds
# memory), so a fully correct offline keygen is impossible. This script
# implements all deterministic parts and marks the buggy/unknown parts.

import hashlib
import struct

# ---------------------------------------------------------------------------
# Name / Company length checks
# ---------------------------------------------------------------------------

def name_length_ok(name: str) -> bool:
    """0xC80 <= ((len*5) << 8) >> 1 <= 0x5000  =>  5 <= len <= 32"""
    n = len(name)
    val = ((n * 5) << 8) >> 1
    return 0xC80 <= val <= 0x5000

def company_length_ok(company: str) -> bool:
    """0x86888 <= (((len+0xFF)*((len+0xFF)>>1))<<4) - 0xC8 <= 0x97788  =>  8 <= len <= 24"""
    n = len(company)
    t = n + 0xFF
    val = ((t * (t >> 1)) << 4) - 0xC8
    return 0x86888 <= val <= 0x97788

# ---------------------------------------------------------------------------
# Serial encoding applied BEFORE comparison
# serial[i] += 0x14  (i.e. each byte of the user-entered serial is incremented)
# ---------------------------------------------------------------------------

def encode_serial(s: str) -> bytes:
    """Encoding applied to the user-entered serial before comparison."""
    return bytes((b + 0x14) & 0xFF for b in s.encode('latin-1'))

# ---------------------------------------------------------------------------
# Modified MD5 of name  (details of 'modification' not fully disclosed)
# ASSUMPTION: The modification is minor / unknown; we use standard MD5 as
# a placeholder. The real implementation computes a custom MD5 variant.
# ---------------------------------------------------------------------------

def modified_md5_hexstring(name: str) -> str:
    # ASSUMPTION: Using standard MD5; actual implementation uses a 'modified MD5'
    return hashlib.md5(name.encode('latin-1')).hexdigest().upper()

# ---------------------------------------------------------------------------
# Modified CRC32 of company
# The writeup explicitly states this part is BUGGY: it reads crc_table entries
# far out of bounds (crc_table + 0xFFF*4) and then reads beyond the company
# string starting at company+0x80-2. The result is non-deterministic across
# instances because it depends on random memory contents.
# ASSUMPTION: We return a placeholder of 8 hex chars.
# ---------------------------------------------------------------------------

def modified_crc32_hexstring(company: str) -> str:
    # ASSUMPTION: This is a placeholder. The real function reads out-of-bounds
    # memory making it instance-specific and impossible to replicate offline.
    # A standard CRC32 is shown for structural completeness only.
    import binascii
    crc = 0xFFFFFFFF
    # ASSUMPTION: standard CRC32 used here; actual algo uses corrupted table
    crc = binascii.crc32(company.encode('latin-1'), crc) & 0xFFFFFFFF
    return format(crc, '08X')

# ---------------------------------------------------------------------------
# Serial generation
# 1. Compute modified MD5 hex of name  -> base string (32 hex chars)
# 2. Replace certain positions in the MD5 string with CRC32 hex of company
#    (writeup: 'crc value replaces MD5 hash on positions pointed out by buffer')
#    ASSUMPTION: exact replacement positions unknown; we replace chars 0-7
# 3. Insert '-' after every 8 chars of the 32-char result
# 4. Apply serial encoding (each byte += 0x14) to produced serial for
#    internal comparison; keygen must output the UN-encoded form
# ---------------------------------------------------------------------------

def generate_serial(name: str, company: str) -> str:
    """Generate the serial that should be entered by the user."""
    if not name_length_ok(name):
        raise ValueError(f'Name length must be 5-32 chars (got {len(name)})')
    if not company_length_ok(company):
        raise ValueError(f'Company length must be 8-24 chars (got {len(company)})')

    md5_hex = modified_md5_hexstring(name)          # 32 hex chars
    crc_hex = modified_crc32_hexstring(company)      # 8 hex chars

    # ASSUMPTION: CRC32 replaces the first 8 positions of the MD5 string
    base = list(md5_hex)
    for i, ch in enumerate(crc_hex):
        base[i] = ch
    base_str = ''.join(base)  # 32 chars

    # Insert '-' after every 8 chars  -> 'XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX'
    parts = [base_str[i:i+8] for i in range(0, 32, 8)]
    serial = '-'.join(parts)
    return serial

# ---------------------------------------------------------------------------
# keygen entry point
# ---------------------------------------------------------------------------

def keygen(name: str, company: str = 'MyCompany') -> str:
    """Return a candidate serial for the given name and company."""
    return generate_serial(name, company)

# ---------------------------------------------------------------------------
# verify  - checks whether a user-entered serial matches the expected one
# The keygenme encodes the entered serial (+=0x14) then compares to the
# encoded generated serial.  Equivalently we compare plain serials.
# ---------------------------------------------------------------------------

def verify(name: str, serial: str, company: str = 'MyCompany') -> bool:
    """Return True if serial matches the generated serial for name+company."""
    if not serial:  # at least 1 char required
        return False
    try:
        expected = generate_serial(name, company)
    except ValueError:
        return False
    # Compare after applying the same encoding to both sides
    return encode_serial(serial) == encode_serial(expected)

# ---------------------------------------------------------------------------
# Demo
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
