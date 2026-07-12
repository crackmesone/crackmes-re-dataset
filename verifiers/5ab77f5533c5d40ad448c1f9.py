import hashlib
import struct
import socket

# NOTE: The algorithm depends on the computer name (GetComputerNameA).
# For verify() we accept an optional computer_name parameter.
# The 'debug' flag controls whether al=0x19 (debug) or al=1 (normal).

def crc_init():
    crcpoly = 0xEDB88320
    table = []
    for i in range(256):
        t = i
        for _ in range(8):
            if t & 1:
                t = (t >> 1) ^ crcpoly
            else:
                t >>= 1
        table.append(t)
    return table

CRC_TABLE = crc_init()

def docrc(data: bytes) -> int:
    crc32 = 0xFFFFFFFF
    for b in data:
        crc32 = CRC_TABLE[(crc32 ^ b) & 0xFF] ^ (crc32 >> 8)
    return (~crc32) & 0xFFFFFFFF

def md5_hex(data: bytes) -> str:
    """Standard MD5 as hex string (lowercase)."""
    return hashlib.md5(data).hexdigest()

def bswap32(v: int) -> int:
    v &= 0xFFFFFFFF
    return (((v & 0xFF) << 24) |
            ((v & 0xFF00) << 8) |
            ((v & 0xFF0000) >> 8) |
            ((v & 0xFF000000) >> 24))

def compute_s2(name: str, u1: int, u2: int) -> int:
    # ASSUMPTION: s1 is computed as only the low byte (AL register)
    s2 = 0
    l1 = len(name)
    for i in range(l1):
        char_val = ord(name[l1 - i - 1])
        s1 = (((char_val + 0x55) ^ u1) << u2) & 0xFF
        s2 = s2 + s1
        s2 = s2 ^ 0x45875614
        s2 &= 0xFFFFFFFF
    return s2

def generate_serial(name: str, computer_name: str = None, debug: bool = False) -> str:
    if computer_name is None:
        # ASSUMPTION: use local hostname as fallback
        computer_name = socket.gethostname().upper()

    # Truncate/pad computer name to match Windows behavior (max 15 chars + null)
    # We'll use bytes of the computer name
    comp_bytes = computer_name.encode('ascii', errors='replace')
    size = len(comp_bytes)  # corresponds to 'size' from GetComputerNameA

    if debug:
        al = u2 = 0x19
    else:
        al = u2 = 1

    u1 = (0x25 - ((al + 0x25) ^ 0x34)) & 0xFF

    s2 = compute_s2(name, u1, u2)
    s3 = (s2 ^ 0x12345678) & 0xFFFFFFFF
    s4 = bswap32(s3)
    s5 = (s4 * 0x4523) & 0xFFFFFFFF
    s6 = (s5 - 0x500) & 0xFFFFFFFF

    # Build h1 string: "%.8X%.8X%.8X%.8X" % (s6, s5, s4, s2)
    h1_str = "%08X%08X%08X%08X" % (s6, s5, s4, s2)
    # fixMD5: if len(h1_str) < 8, set h1_str[len] = 0x80 -- here len >= 8 always, so skip
    # l2 = len(h1_str) = 32
    l2 = len(h1_str)
    h1_bytes = h1_str.encode('ascii')

    # GetMD5(h1, l2, h2) -- standard MD5 of h1_bytes
    h2_str = md5_hex(h1_bytes).upper()  # 32 hex chars

    # Process computer name
    crc1 = docrc(comp_bytes)
    bcrc = bswap32(crc1)

    # XOR first 8 bytes of CompName
    comp_list = list(comp_bytes)
    # Pad if needed
    while len(comp_list) < 8:
        comp_list.append(0)

    comp_list[0] = comp_list[0] ^ (crc1 & 0xFF)
    comp_list[1] = comp_list[1] ^ ((crc1 >> 8) & 0xFF)
    comp_list[2] = comp_list[2] ^ ((crc1 >> 16) & 0xFF)
    comp_list[3] = comp_list[3] ^ ((crc1 >> 24) & 0xFF)
    comp_list[4] = comp_list[4] ^ (bcrc & 0xFF)
    comp_list[5] = comp_list[5] ^ ((bcrc >> 8) & 0xFF)
    comp_list[6] = comp_list[6] ^ ((bcrc >> 16) & 0xFF)
    # ASSUMPTION: The C code has a precedence bug on index 7: ((bcrc&0xFF000000))>>24
    comp_list[7] = comp_list[7] ^ ((bcrc >> 24) & 0xFF)

    comp_modified = bytes(comp_list[:size] if size <= len(comp_list) else comp_list)

    # fixMD5: if size < 8, set byte at index size to 0x80
    comp_for_md5 = bytearray(comp_modified)
    if size < 8:
        if len(comp_for_md5) > size:
            comp_for_md5[size] = 0x80
        else:
            comp_for_md5.append(0x80)
    comp_for_md5 = bytes(comp_for_md5)

    h3_str = md5_hex(comp_for_md5).upper()  # 32 hex chars

    # Build h4:
    # for i in range(len(h2)), j starts at len(h3) and decrements
    # h4[i] = (((h2[j-1] ^ h3[i]) + h1[j-1]) << 6) ^ u1
    # All values treated as byte values (ASCII codes)
    h2_bytes = h2_str.encode('ascii')
    h3_bytes = h3_str.encode('ascii')
    h1_ascii = h1_str.encode('ascii')

    h4 = bytearray()
    j = len(h3_str)  # = 32
    for i in range(len(h2_str)):  # i in 0..31
        # j goes from 32 downto 1
        jj = j - i  # j-1 in C (j starts at 32, decrements each iteration via j--)
        # Actually: i increments, j decrements => j_current = len(h3) - i
        # h2[j-1] means h2[len(h3)-i - 1]
        # h1[j-1] means h1[len(h3)-i - 1]
        idx = j - i - 1  # = 31 - i
        val_h2 = h2_bytes[idx] if idx < len(h2_bytes) else 0
        val_h3 = h3_bytes[i] if i < len(h3_bytes) else 0
        val_h1 = h1_ascii[idx] if idx < len(h1_ascii) else 0
        raw = (((val_h2 ^ val_h3) + val_h1) << 6) ^ u1
        # ASSUMPTION: stored as byte (C uses char array, implicit truncation)
        h4.append(raw & 0xFF)

    l3 = len(h4)
    h5_str = md5_hex(bytes(h4)).upper()  # 32 hex chars

    # Compute CRC of h5
    crc2 = docrc(h5_str.encode('ascii'))
    crc_str = "%08X" % crc2  # 8 chars

    # Replace h5[8..11] with CRC chars [0..3]
    h5_list = list(h5_str)
    for i in range(4):
        h5_list[8 + i] = crc_str[i]

    # Insert dashes at positions 7, 15, 23
    for pos in [7, 15, 23]:
        h5_list[pos] = '-'

    serial_inner = ''.join(h5_list)
    serial = "DRP-" + serial_inner
    return serial

def verify(name: str, serial: str, computer_name: str = None, debug: bool = False) -> bool:
    """Verify name/serial pair. Requires the same computer name used during keygen."""
    expected = generate_serial(name, computer_name=computer_name, debug=debug)
    return serial.upper() == expected.upper()

def keygen(name: str, computer_name: str = None, debug: bool = False) -> str:
    """Generate serial for given name."""
    if computer_name is None:
        computer_name = socket.gethostname().upper()
    return generate_serial(name, computer_name=computer_name, debug=debug)


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
