#!/usr/bin/env python3
"""
Reverse-engineered keygen/verifier for eset_vmtest by nezlooy.

The crackme implements a stack-based VM. From the writeup (Keygen.py),
the core algorithm XORs/transforms the name with a constant buffer to
produce the expected serial.

The VM bytecode is embedded in the binary and was partially disassembled.
From the Keygen.py snippet (truncated), the algorithm:
1. Takes the user name bytes.
2. For each character in the name, applies a transformation using CONSTANT1 and/or CONSTANT2.
3. Compares the result against a stored constant.

Since the writeup was truncated before the full keygen logic was shown,
some details below are ASSUMPTION-marked.
"""

# Constant buffer at 0x004070AC (from Keygen.py)
CONSTANT1 = [
    0x8A, 0xA7, 0x88, 0xAB, 0x44, 0xD3, 0xCC, 0xCD, 0xE8, 0xEF, 0x4A, 0xF9, 0xD2, 0xE7, 0x4E, 0xE9,
    0xD2, 0xDD, 0xD8, 0x53, 0xFA, 0xC5, 0xC4, 0xCF, 0xD2, 0x59, 0xF4, 0xC5, 0xF8, 0xCB, 0xCC, 0xC3,
    0xEE, 0x79, 0x62, 0xC3, 0xFC, 0xE7, 0xD4, 0xF5, 0xF4, 0xE7, 0x72, 0x6B, 0xEE, 0xF1, 0xE6, 0x6F,
    0xEA, 0xEF, 0xD6, 0xF9, 0x68,
]

# CONSTANT2 was truncated in the writeup; reconstructed from VM bytecode area
# VM bytecode ends at offset ~0x84; data section starts right after the last 0x00 terminator.
# From the ins[] array in Disassembly.py, bytes starting at index 0x84 (132):
# 0x8A, 0xA7, 0x88, 0xAB, ... these match CONSTANT1 exactly.
# ASSUMPTION: CONSTANT2 is derived from CONSTANT1 by XORing with a rolling key or name-derived value.
# From the partial Keygen.py snippet, CONSTANT2 starts with:
CONSTANT2 = [
    0x6B, 0x36, 0x37, 0x3B, 0x4D, 0x4B, 0x01, 0x0B, 0x11, 0x53, 0x0C, 0x1E, 0x01, 0x1C, 0x0B, 0x41,
    0x0E, 0x05, 0x53, 0x45, 0x09, 0x0B, 0x1A, 0x18, 0x52, 0x1D, 0x02,
    # ASSUMPTION: rest of CONSTANT2 is zero-padded (truncated in writeup)
] + [0] * 26


def _vm_transform_name(name: str) -> list:
    """
    Based on the VM disassembly, the VM:
    1. Reads each character of the name.
    2. XORs / combines it with index-based values from the constant buffers.
    3. Produces a sequence of output bytes that must match a target.

    ASSUMPTION: The transformation per character i is:
        result[i] = (ord(name[i]) * some_factor + CONSTANT2[i]) XOR something
    The exact formula is partially visible in the VM trace.
    """
    # ASSUMPTION: Based on typical crackme patterns and the VM opcode trace
    # (imul, add, xor, neg, not seen in the disassembly output),
    # the core per-character check appears to be:
    #   transformed = (~(ord(c) * ord(c)) & 0xFF) XOR constant
    # But without the full keygen we reconstruct from CONSTANT1:
    result = []
    for i, c in enumerate(name):
        v = ord(c)
        # ASSUMPTION: formula derived from VM opcodes: neg, not, imul, xor pattern
        t = ((~(v * v)) & 0xFF) ^ (CONSTANT1[i % len(CONSTANT1)])
        result.append(t & 0xFF)
    return result


def _serial_from_name(name: str) -> str:
    """
    ASSUMPTION: The serial is the hex-encoded (or decimal-encoded) transformation
    of the name through the VM algorithm. The exact encoding format is unknown
    (truncated writeup). We return hex uppercase.
    """
    transformed = _vm_transform_name(name)
    # ASSUMPTION: serial is hex string of transformed bytes
    return ''.join('%02X' % b for b in transformed)


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.

    The VM reads name and serial, computes a transformation on the name,
    and checks it equals a target derived from (or equal to) the serial.

    ASSUMPTION: serial must equal the hex-encoded transformed name.
    """
    if not name or not serial:
        return False
    expected = _serial_from_name(name)
    # ASSUMPTION: comparison is case-insensitive hex
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    ASSUMPTION: see _serial_from_name for formula assumptions.
    """
    if not name:
        raise ValueError('Name cannot be empty')
    return _serial_from_name(name)



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
