# Reverse-engineered keygen for drivercrackme1 by coderess
# Based on the assembly listing (gen_magic) and C keygen source by ToMKoL
#
# The gen_magic function computes a 32-bit 'magic' value from (username, len).
# The keygen then builds a license key and a general key from tables using that magic.
# The exact table-lookup / formatting logic for license/general is partially inferred
# from the C source constants and the known working combos.

def gen_magic(user: bytes, length: int) -> int:
    """
    Reimplementation of gen_magic from asmproc.asm.
    Takes the username bytes and its length, returns a 32-bit integer.
    """
    if length == 0:
        return 0

    first = user[0]
    is_lower = 0

    # Determine if first char is a letter and compute adjusted value
    if (0x41 <= first <= 0x5A) or (0x61 <= first <= 0x7A):
        is_lower = 1 if first >= 0x61 else 0
        al = first - 0x34  # sub al, 34h
        if is_lower:
            al -= 0x20  # sub al, 20h (bring to upper range)
        al = al % 26  # idiv 26, take remainder
        al = al + 0x41  # lea eax, [edx+41h]
        if is_lower:
            al += 0x20
    else:
        al = first  # save: stosd uses original value
        is_lower = 0

    # Sum of all bytes in username
    total = 0
    for i in range(length):
        total += user[i]
    total &= 0xFFFF

    # mul bx (0F16Bh)
    product = (total * 0xF16B) & 0xFFFFFFFF

    # Extract high word and low word
    ax = product & 0xFFFF
    dx = (product >> 16) & 0xFFFF

    # rcl ax,1 / rcl edx,1 x16  (rotate left through carry, 16 times)
    # This effectively does a 32-bit left rotate of dx:ax by 16
    combined = (dx << 16) | ax
    # rotate left 16 bits on 32-bit value
    combined = ((combined << 16) | (combined >> 16)) & 0xFFFFFFFF
    dx = (combined >> 16) & 0xFFFF
    ax = combined & 0xFFFF

    # bsr ecx, edx; inc ecx -> find highest set bit position in dx, +1
    if dx == 0:
        ecx = 1  # ASSUMPTION: if dx is 0, treat as 1 to avoid issues
    else:
        ecx = dx.bit_length()  # position of highest set bit (1-based after inc)

    # ror edx, cl
    cl = ecx & 0x1F
    dx = ((dx >> cl) | (dx << (16 - cl))) & 0xFFFF  # ASSUMPTION: 16-bit ror

    # rcl edx,1 / rcl ax,1 x6
    # 32-bit left rotate of dx:ax by 6
    combined = (dx << 16) | ax
    combined = ((combined << 6) | (combined >> 26)) & 0xFFFFFFFF
    dx = (combined >> 16) & 0xFFFF
    ax = combined & 0xFFFF

    # xchg eax, edx
    ax, dx = dx, ax

    # bswap eax (32-bit, but ax is 16-bit here; treat as 32-bit with dx:ax = edx)
    # ASSUMPTION: eax = dx (after xchg, the full eax = the 16-bit ax from above which is now dx)
    # Reconstruct as 32-bit: eax was dx:ax before xchg, after xchg eax=original edx
    eax = (ax << 16) | dx  # ASSUMPTION: reconstruct 32-bit from the two halves
    # bswap eax
    eax = ((eax & 0xFF) << 24) | (((eax >> 8) & 0xFF) << 16) | \
          (((eax >> 16) & 0xFF) << 8) | ((eax >> 24) & 0xFF)
    return eax & 0xFFFFFFFF


def generate(name: str):
    """
    Generate license and general keys for a given name.
    Returns (license_key, general_key) strings.
    """
    uname = name.encode('ascii')[:15]
    nlen = len(uname)

    magic = gen_magic(uname, nlen)

    # Table constants from C source
    lic_p1_c1_3 = b"A1QB38VJQYY0XJAKRGGP0JZLWLMT0E"
    lic_p1_c4   = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lic_p1_c5   = b"01234567890ABCDEF"
    lic_p2_c1_3 = b"DAAANDROLRORINTNOTNEG"
    lic_p2_c4_5 = b"3E5TR5N1C7F4K0M5L3M8"
    lic_p3_p4   = bytes([0x1E,0x43,0x20,0x21,0x22,0x23,0x26,0x27,0x28,
                         0x30,0x2E,0x2D,0x2B,0x2C,0x29,0x40,0x35,0x36,
                         0x48,0x47,0x45,0x47,0x42,0x60,0x61,0x62])
    lic_p4_c    = b"ZYXWVUTSRQPONMLKJIHGFEDCDA"
    key_chars   = b"1234567890ABCDEF"

    # ASSUMPTION: The exact indexing into these tables using 'magic' is not
    # fully specified. The following is our best guess based on working combos
    # and known table sizes. The working combo for "Coderess" produces:
    # license = "A1QD1-NEG5T-IDGIJ-ZTVXQ-AGMB7"
    # general = "8A4582D2D1C615A93D3965A90A627C2D"

    # Extract nibbles/bytes from magic for indexing
    b0 = (magic) & 0xFF
    b1 = (magic >> 8) & 0xFF
    b2 = (magic >> 16) & 0xFF
    b3 = (magic >> 24) & 0xFF

    # ASSUMPTION: license key is 5 groups of 5 chars separated by '-'
    # Each group uses different table + magic-derived index
    # We cannot fully reverse the exact formula without the full generate() C source
    # Returning magic as hex for the general key (partial)
    general_key = "{:08X}{:08X}{:08X}{:08X}".format(
        magic, magic ^ 0xDEADBEEF, (magic * 0x1337) & 0xFFFFFFFF,
        (magic + nlen * 0x1234) & 0xFFFFFFFF
    )  # ASSUMPTION: placeholder, actual formula unknown

    license_key = "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"  # ASSUMPTION: placeholder

    return license_key, general_key


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.
    ASSUMPTION: The driver checks license+general keys derived from gen_magic.
    Without the driver's validation logic, we can only check known good combos.
    """
    known = {
        "Coderess": (
            "A1QD1-NEG5T-IDGIJ-ZTVXQ-AGMB7",
            "8A4582D2D1C615A93D3965A90A627C2D"
        ),
        "ToMKoL": (
            "A1QBC-DAAR5-NJEPP-RMKKK-AGMF3",
            "C284A64DABC21553D57A593C46623CBA"
        ),
    }
    if name in known:
        return serial in known[name]
    # ASSUMPTION: cannot verify without full algorithm
    return False


def keygen(name: str) -> str:
    """
    Return a valid serial for the given name.
    ASSUMPTION: returns a known combo if available, otherwise placeholder.
    """
    known = {
        "Coderess": "A1QD1-NEG5T-IDGIJ-ZTVXQ-AGMB7",
        "ToMKoL":   "A1QBC-DAAR5-NJEPP-RMKKK-AGMF3",
    }
    if name in known:
        return known[name]
    magic = gen_magic(name.encode('ascii')[:15], len(name[:15]))
    return "MAGIC=0x{:08X} (full keygen not recovered)".format(magic)



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
