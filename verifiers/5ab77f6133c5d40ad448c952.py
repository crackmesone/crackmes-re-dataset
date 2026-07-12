# NOTE: This crackme's keygen reads values DIRECTLY from the running cm.exe process memory
# (buf at baseAddr+0x1C89, block3 at baseAddr+0x30F0).
# Without the actual cm.exe binary and its in-memory state after the user enters a name,
# we cannot implement a standalone verify(name, serial) or keygen(name).
#
# What we CAN reconstruct are the helper routines and the serial-assembly steps
# from the keygen source, but the key inputs (buf[0..15], block3[168..175], ebx_value)
# all come from reading the crackme's memory at runtime, NOT from the name string directly.
#
# The algorithm is therefore only PARTIALLY recovered: we have the serial-construction
# logic but not the name->hash transformation (that lives inside cm.exe).

import struct

# --- Reconstructed helpers ---

def asciify(eax):
    """Convert lower 32 bits of eax to 8 hex-like ASCII characters (big-endian nibbles).
    Returns list of 8 bytes (ASCII)."""
    result = [0]*8
    for i in range(8, 0, -1):
        nibble = eax & 0x0F
        ch = nibble + 0x30
        if ch > 0x39:
            ch += 7
        result[i-1] = ch
        eax >>= 4
    return result

# ASSUMPTION: block3 and buf come from cm.exe memory; we cannot derive them from name alone.
# ASSUMPTION: transform64 implements a 64-bit butterfly/bit-reversal then multiply;
#             the exact values depend on block3 constants loaded from cm.exe.

def build_serial_part1(buf_bytes, block1, block2):
    """Build first 4 characters of serial from buf[8..11]."""
    serial = [0]*13
    serial[4] = ord('-')
    j = 0
    for i in range(4, 0, -1):
        k = buf_bytes[8 + j] - 0x30
        if k > 9:
            k -= 0x11
            # ASSUMPTION: block2 index by k (after adjustment)
            serial[i-1] = k + block2[k] + 0x41 + 1
        else:
            serial[i-1] = k + block1[k] + 0x41 - (i-1)
        j += 1
    return serial

def build_serial_part2(serial, buf_bytes, ebx_value):
    """Build last 8 characters of serial (positions 5..12)."""
    j = 5
    k = 1
    for i in range(8):
        if (k & ebx_value) != 0:
            val = 0x41 - (buf_bytes[i] - buf_bytes[8+i])
        else:
            val = 0x41 - (buf_bytes[8+i] - buf_bytes[i])
        serial[j] = val & 0xFF
        j += 1
        k = k << 1
    return serial

def bytes_to_serial(serial_bytes):
    return ''.join(chr(b) for b in serial_bytes if b != 0)

# These constants are taken directly from keygen.c
block1 = bytes([0x03,0x03,0x01,0x03,0x06,0x0A,0x0F,0xFC,0x03,0x0B,0xFF,0x04,0x24])
block2 = bytes([0x00,0x0B,0xFE,0x0B,0x00,0x0F])

def verify(name, serial):
    """
    Cannot be fully implemented without cm.exe running.
    The crackme reads a hash from its own process memory after the user
    enters the name and clicks OK. There is no standalone name->serial mapping.
    """
    # ASSUMPTION: We cannot verify without the running process.
    raise NotImplementedError(
        "verify() requires cm.exe to be running and its memory to be read. "
        "The algorithm inside cm.exe that hashes the name is not provided in the writeup."
    )

def keygen(name):
    """
    Cannot generate serial without cm.exe running.
    The writeup shows the keygen reads buf and block3 from cm.exe's memory
    AFTER the user has typed a name. No standalone name->serial algorithm is described.
    """
    # ASSUMPTION: Full keygen requires attaching to cm.exe and reading its memory.
    raise NotImplementedError(
        "keygen() requires cm.exe to be running. "
        "Attach to the process, read buf from baseAddr+0x1C89 (16 bytes) "
        "and block3 from baseAddr+0x30F0 (0xB0 bytes), "
        "then call build_serial_part1/build_serial_part2 with the extracted values."
    )


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
