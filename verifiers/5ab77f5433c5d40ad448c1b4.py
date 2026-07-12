# Keygen for rif_crackme_2 by korbut
# Reversed from algo.asm by bF!
#
# Protection: name/serial
# The serial has format: C1!C2@C3-bF!
# where C1, C2, C3 are chosen from the alphabet table below.
#
# Algorithm (from algo.asm):
#   Let name = EnteredName, serial_prefix = brute (3 chars: b0, b1, b2)
#
#   edi = 0
#   al = name[0] ^ 0x3C ^ 0x09  => pushed as ebx
#   eax = sign_extend(al)
#   edi += eax
#
#   al = brute[0] ^ 0x09
#   al = al ^ bl  (bl = name[0] ^ 0x3C ^ 0x09)
#   eax = sign_extend(al)
#   edi += eax
#
#   al = name[2] + brute[1]
#   eax = sign_extend(al)
#   ebx = sign_extend(brute[1])
#   eax = eax + ebx
#   edi += eax
#
#   al = brute[2]
#   bl = name[4]
#   eax = sign_extend(al)
#   ebx = sign_extend(bl)
#   eax = eax + ebx
#   edi += eax
#
#   edi ^= 0x90
#   check: edi == 0x14F
#
# Name must be >= 5 chars.
# Only chars at positions 1, 3 of brute (serial[0], serial[2], serial[4])
# are used in the final Serial string as: Serial = C1 + '!' + C2 + '@' + C3 + '-bF!'

import ctypes

# Alphabet table from the .data section
alpha = (
    bytes([
        0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,
        0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,
        0x6B,0x6C,0x6D,0x6E,0x6F,0x70,0x71,0x72,0x73,0x74,
        0x75,0x76,0x77,0x78,0x79,0x7A,0x41,0x42,0x43,0x44,
        0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,
        0x4F,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,
        0x59,0x5A,0x60,0x7E,0x21,0x40,0x23,0x24,0x25,0x5E,
        0x26,0x2A,0x28,0x29,0x5F,0x2B,0x2D,0x3D,0x5B,0x5D,
        0x7B,0x7D,0x5C,0x7C,0x3B,0x27,0x3A,0x22,0x2C,0x2E,
        0x3C,0x3E,0x2F,0x3F,0x20,
    ])
)

# alphalen is 143 in the asm, but the alpha table above has only 95 bytes + null.
# ASSUMPTION: alphalen = len(alpha) = 95; the asm says 143 (0x8F) which seems
# to be the declared size of the table region, but the table itself ends at index 94
# (95 entries + null terminator). We use 95 to stay within valid table entries.
ALPHALEN = len(alpha)  # 95


def _signed8(v):
    """Sign-extend an 8-bit value to a Python int."""
    v = v & 0xFF
    if v >= 0x80:
        return v - 0x100
    return v


def _algo(name_bytes, b0, b1, b2):
    """Run the crackme's check algorithm. Returns edi after xor 0x90."""
    edi = 0

    # step 1: name[0] ^ 0x3C ^ 0x09
    al = (name_bytes[0] ^ 0x3C ^ 0x09) & 0xFF
    bl = al  # saved via push/pop
    edi += _signed8(al)

    # step 2: brute[0] ^ 0x09 ^ bl
    al = (b0 ^ 0x09 ^ bl) & 0xFF
    edi += _signed8(al)

    # step 3: (name[2] + brute[1]) sign-extended + sign-extended(brute[1])
    al = (name_bytes[2] + b1) & 0xFF
    bl_val = b1
    eax = _signed8(al)
    ebx = _signed8(bl_val)
    edi += eax + ebx

    # step 4: sign-extended(brute[2]) + sign-extended(name[4])
    eax = _signed8(b2)
    ebx = _signed8(name_bytes[4])
    edi += eax + ebx

    # final xor
    # edi can be any python int here; we keep it as 32-bit for the xor
    edi32 = ctypes.c_int32(edi).value
    edi32 ^= 0x90
    return edi32


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    if len(name) < 5:
        return False
    # Serial format: C1 + '!' + C2 + '@' + C3 + '-bF!'
    if len(serial) < 9:
        return False
    if serial[1] != '!' or serial[3] != '@' or serial[4:] != serial[4] + '-bF!':
        pass  # We check the suffix below
    # Expected suffix: positions [5:] should be '-bF!'
    if serial[1] != '!' or serial[3] != '@' or serial[5:] != '-bF!':
        return False

    name_bytes = [ord(c) & 0xFF for c in name]
    b0 = ord(serial[0]) & 0xFF
    b1 = ord(serial[2]) & 0xFF
    b2 = ord(serial[4]) & 0xFF

    result = _algo(name_bytes, b0, b1, b2)
    return result == 0x14F


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long.")

    name_bytes = [ord(c) & 0xFF for c in name]

    for i0 in range(ALPHALEN):
        for i1 in range(ALPHALEN):
            for i2 in range(ALPHALEN):
                b0 = alpha[i0]
                b1 = alpha[i1]
                b2 = alpha[i2]
                result = _algo(name_bytes, b0, b1, b2)
                if result == 0x14F:
                    c0 = chr(b0)
                    c1 = chr(b1)
                    c2 = chr(b2)
                    return f"{c0}!{c1}@{c2}-bF!"

    raise ValueError(f"No serial found for name '{name}'")



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
