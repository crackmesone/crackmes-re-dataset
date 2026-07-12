import hashlib
import struct

# TEA (Tiny Encryption Algorithm) - standard implementation
# Key used: 'crackmes\x00Hmm,but' (16 bytes)
TEA_KEY = b'crackmes\x00Hmm,but'

def tea_encrypt_block(v0, v1, key):
    """Encrypt a single 64-bit block (v0, v1) using TEA with the given 128-bit key."""
    k = struct.unpack('<4I', key)
    delta = 0x9E3779B9
    total = 0
    mask = 0xFFFFFFFF
    for _ in range(32):
        total = (total + delta) & mask
        v0 = (v0 + (((v1 << 4) + k[0]) ^ (v1 + total) ^ ((v1 >> 5) + k[1]))) & mask
        v1 = (v1 + (((v0 << 4) + k[2]) ^ (v0 + total) ^ ((v0 >> 5) + k[3]))) & mask
    return v0, v1

def keygen(name):
    """
    Generate serial for a given name.
    Name must be at least 4 characters long.
    Serial format: <MD5_part1>-<TEA_part2>
    with byte substitutions at specific positions.
    """
    if len(name) < 4:
        return None

    name_bytes = name.encode('ascii') if isinstance(name, str) else name

    # Part 1: MD5 of name, formatted as 4 groups of 8 hex chars each (big-endian dwords)
    # The C++ code uses %.2x%.2x%.2x%.2x for each 4-byte group in order,
    # effectively producing lowercase hex of the raw MD5 bytes.
    # The ASM solution uses %.8X for each 4-byte little-endian dword -> uppercase
    # The C++ keygen uses lowercase; the crackme verifier likely accepts uppercase (edit box has ES_UPPERCASE)
    # We'll produce lowercase hex matching the MD5 byte order as in the C++ solution.

    md5_bytes = hashlib.md5(name_bytes).digest()  # 16 bytes

    # Format: for x in 0,4,8,12: sprintf("%.2x%.2x%.2x%.2x", b[x],b[x+1],b[x+2],b[x+3])
    # This just produces the standard lowercase hex MD5 string
    md5_hex = ''.join('%02x' % b for b in md5_bytes)  # 32 hex chars

    # Part 2: TEA encrypt the first 8 bytes of the name
    # The name buffer is used directly; if name < 8 bytes the rest is zero-padded
    name_padded = name_bytes[:8].ljust(8, b'\x00')
    v0, v1 = struct.unpack('<II', name_padded)
    ev0, ev1 = tea_encrypt_block(v0, v1, TEA_KEY)

    # C++ code:
    # for(x=4;x>=0;x-=4): sprintf(szTemp, "%.2x%.2x%.2x%.2x", byTemp[x+3],byTemp[x+2],byTemp[x+1],byTemp[x])
    # byTemp is the output of ProcessBlock which writes ev0 then ev1 in little-endian
    # byTemp[0..3] = ev0 LE, byTemp[4..7] = ev1 LE
    # x=4: sprintf("%.2x%.2x%.2x%.2x", byTemp[7],byTemp[6],byTemp[5],byTemp[4]) -> ev1 big-endian hex
    # x=0: sprintf("%.2x%.2x%.2x%.2x", byTemp[3],byTemp[2],byTemp[1],byTemp[0]) -> ev0 big-endian hex
    # So tea_hex = ev1_be_hex + ev0_be_hex
    ev0_bytes = struct.pack('<I', ev0)
    ev1_bytes = struct.pack('<I', ev1)
    # Reversed byte order for each = big-endian representation
    tea_hex = ''.join('%02x' % b for b in reversed(ev1_bytes)) + \
              ''.join('%02x' % b for b in reversed(ev0_bytes))
    # This equals: '%08x%08x' % (ev1, ev0)  (big-endian value printed)
    # Actually reversed(LE bytes) = BE bytes, so value printed big-endian
    # Which is just: '%08x' % ev1 + '%08x' % ev0
    # Let's verify: struct.pack('<I', ev1) reversed = big-endian bytes of ev1 = '%08x' % ev1
    # Yes, that's correct.

    # Build serial = md5_hex + "-" + tea_hex (16 chars)
    serial = list(md5_hex + '-' + tea_hex)

    # Apply byte substitutions (0-indexed positions in serial string):
    # szSerial[6]  = 'C'  (0x43)
    # szSerial[20] = 'X'  (0x58)
    # szSerial[31] = '$'  (0x24)
    serial[6] = 'C'
    serial[20] = 'X'
    serial[31] = '$'

    return ''.join(serial).upper()


def verify(name, serial):
    """
    Verify that serial matches the expected serial for name.
    Comparison is case-insensitive (serial field uses ES_UPPERCASE).
    """
    if len(name) < 4:
        return False
    expected = keygen(name)
    if expected is None:
        return False
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
