# ipoly crackme by ghiribizzo
# Reverse-engineered from FL.ASM disassembly + solution writeup
#
# High-level summary (from writeup + ASM):
#   1. The name is used to derive a "scramble count" (di = 0x20 + (name_length XOR something))
#      and an initial 8-byte state loaded from the name bytes.
#   2. A permutation/mixing loop runs 'di' times on registers ax,bx,cx,dx.
#   3. The resulting 32-bit value is split into 8 nibbles -> stored as dwords at [0x538..0x554].
#      Nibbles that are 0 are bumped to 1, and all four "root" nibbles must be distinct
#      (incremented if equal).
#   4. The serial is 8 signed integers entered by the user.
#      The first four serial values (s0..s3) are the polynomial ROOTS (x-values).
#      The last four serial values (s4..s7) are the polynomial VALUES at those roots.
#   5. Validation: for each i in 0..3,
#         round( root_i * A/B + root_i^2 * C/D + root_i^3 * E/F + root_i^4 * G/H ) == value_i
#      where A/B, C/D, E/F, G/H come from nibbles 4..7 of the computed key.
#
# The polynomial is:  P(x) = (c1/c2)*x + (c3/c4)*x^2 + (c5/c6)*x^3 + (c7/c8)*x^4
# (no constant term).
#
# The keygen approach (from writeup): solve the 4x4 Vandermonde-like system to find
# the polynomial coefficients from 4 (root, value) pairs.
#
# ASSUMPTION: The exact byte-level mixing loop and the mapping from name bytes to the
#             8 nibbles (coefficients) could not be fully reconstructed from the truncated
#             ASM. The scramble below is a best-effort reconstruction.
# ASSUMPTION: The coefficient nibbles (flt_0_518..flt_0_534) are the nibbles at offsets
#             0x538-0x554 produced by the name hash. We approximate with a simplified hash.
# ASSUMPTION: The serial "roots" s0..s3 are the first 4 signed integers and
#             "values" s4..s7 are the next 4 signed integers in the input.

import struct

def _name_to_nibbles(name: str):
    """
    Reconstruct the 8 nibbles from the name using the mixing loop described in FL.ASM.
    ASSUMPTION: best-effort reconstruction; the exact bit-manipulation is partially unclear.
    """
    name_bytes = name.encode('ascii', errors='replace')
    n = len(name_bytes)
    if n == 0:
        name_bytes = b'\x00'
        n = 1

    # From ASM: ax = ds:5E8h (length byte), xor al,ah, and ax,0FFh
    # ds:5E8h is the length of the name. The buffer at 5E7h stores length then chars.
    # xor al, ah: al = length & 0xFF, ah = 0 typically for a length byte -> di = 0x20 + (length ^ 0) = 0x20 + length
    length_byte = n & 0xFF
    # ASSUMPTION: ah is the high byte of the word at 5E8h which might be the first char
    # but more likely it's 0 (length stored as byte). We'll go with di = 0x20 + length.
    di = 0x20 + length_byte

    # Load initial 8-byte state as 4 words: dx, cx, bx, ax (lodsw x4 from name buffer)
    # Pad name to at least 8 bytes
    padded = (name_bytes * 4)[:8]
    dx = struct.unpack_from('<H', padded, 0)[0]
    cx = struct.unpack_from('<H', padded, 2)[0]
    bx = struct.unpack_from('<H', padded, 4)[0]
    ax = struct.unpack_from('<H', padded, 6)[0]

    # Mixing loop (di iterations)
    # From ASM loc_0_132:
    #   bp = ax
    #   al = ah; ax = ax & 0xFF (so ax = ah as byte, bp = original ax)
    #   swap ax <-> bp  => ax = original ax, bp = ah (low byte)
    #   xor ah, bl
    #   xor ah, ch
    #   xor ah, al  (al is low byte of original ax)
    #   al = bh
    #   bh = bl; bl = ch; ch = cl; cl = dh; dh = dl
    #   dx = (dx & 0xFF00) | (bp & 0xFF)
    #   inc si; cmp si, di; jle loop

    # Let's work with 16-bit registers as integers
    for _ in range(di):
        ah = (ax >> 8) & 0xFF
        al = ax & 0xFF
        bp = ax  # original ax
        # xchg ax, bp: ax = bp (original ax), bp = ah as 8-bit value
        # But before xchg: al was set to ah, ax &= 0xFF so ax = ah
        # then xchg ax, bp => ax = original ax (bp), bp = ah
        # This means after xchg: ax = bp_before = original_ax, bp = ah
        bp_val = ah  # bp holds the old ah (8-bit)
        # ax is restored to original ax
        # xor ah, bl
        bl = bx & 0xFF
        bh = (bx >> 8) & 0xFF
        cl = cx & 0xFF
        ch = (cx >> 8) & 0xFF
        dl = dx & 0xFF
        dh = (dx >> 8) & 0xFF

        new_ah = ah ^ bl ^ ch ^ al
        new_al = bh
        new_bh = bl
        new_bl = ch
        new_ch = cl
        new_cl = dh
        new_dh = dl
        new_dl = bp_val

        ax = ((new_ah & 0xFF) << 8) | (new_al & 0xFF)
        bx = ((new_bh & 0xFF) << 8) | (new_bl & 0xFF)
        cx = ((new_ch & 0xFF) << 8) | (new_cl & 0xFF)
        dx = ((new_dh & 0xFF) << 8) | (new_dl & 0xFF)

    # After loop: shl eax,10h; mov ax,cx => eax = (ax<<16) | cx
    eax = ((ax & 0xFFFF) << 16) | (cx & 0xFFFF)

    # Split into 8 nibbles (lowest nibble first -> stored at 0x538, next at 0x53C, ...)
    nibbles = []
    val = eax & 0xFFFFFFFF
    for _ in range(8):
        nibbles.append(val & 0xF)
        val >>= 4

    # Ensure first 4 nibbles non-zero
    for i in range(4):
        if nibbles[i] == 0:
            nibbles[i] = 1

    # Ensure first 4 nibbles all distinct (increments as in ASM)
    # ASM checks pairs: (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
    pairs = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    for (a, b) in pairs:
        if nibbles[a] == nibbles[b]:
            nibbles[b] += 1

    return nibbles


def poly(x, n):
    """
    Evaluate the polynomial P(x) = (n[0]/n[4])*x + (n[1]/n[5])*x^2 + (n[2]/n[6])*x^3 + (n[3]/n[7])*x^4
    ASSUMPTION: nibbles 0..3 are numerators (flt_0_518..flt_0_524) and
                nibbles 4..7 are denominators (flt_0_528..flt_0_534),
                matching the fimul/fidiv pattern in the ASM.
    """
    a1, a2, a3, a4 = n[0], n[1], n[2], n[3]
    b1, b2, b3, b4 = n[4], n[5], n[6], n[7]
    # Guard against zero denominators
    if 0 in (b1, b2, b3, b4):
        raise ValueError("Zero denominator in polynomial")
    return (a1/b1)*x + (a2/b2)*x**2 + (a3/b3)*x**3 + (a4/b4)*x**4


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Serial format: 8 signed integers separated by whitespace or commas.
    First 4 are roots (x-values), last 4 are expected polynomial values.
    """
    # Parse serial: 8 integers
    import re
    parts = re.split(r'[,\s]+', serial.strip())
    if len(parts) != 8:
        return False
    try:
        vals = [int(p) for p in parts]
    except ValueError:
        return False

    roots = vals[:4]
    expected = vals[4:]

    nibbles = _name_to_nibbles(name)

    for i in range(4):
        computed = poly(roots[i], nibbles)
        rounded = round(computed)
        if rounded != expected[i]:
            return False
    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    Strategy: pick 4 distinct roots, compute polynomial values, return as serial.
    ASSUMPTION: roots can be any integers; we pick small ones.
    """
    nibbles = _name_to_nibbles(name)
    roots = [1, 2, 3, 4]  # arbitrary distinct roots
    values = []
    for r in roots:
        computed = poly(r, nibbles)
        values.append(round(computed))
    all_vals = roots + values
    return ' '.join(str(v) for v in all_vals)



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
