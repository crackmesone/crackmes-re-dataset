# Reconstruction of keygenme_3 by imp
# Based on the ExponentFinder and keygen writeup
#
# The crackme uses a 64-bit permutation/bit-shuffling scheme.
# The shift table defines a permutation on bit indices 0..63.
# The key is validated by checking that applying the permutation
# (with inverse step: index = FindIndexInShiftTable(bit - 11)) some
# number of times (the 'exponent') to each bit position yields a
# specific target configuration.
#
# The ExponentFinder finds all valid exponents e (1..65535) such that
# applying the inverse permutation e times is equivalent to applying
# the forward permutation 0x3D (61) times.
#
# ASSUMPTION: The serial/key is a 64-bit (8-byte) value whose bits are
# permuted. The name is used to derive an initial 64-bit value, and the
# serial must be that value permuted by a valid exponent.
# ASSUMPTION: The exact name->hash and serial format are not fully shown
# in the truncated writeup; we implement what is fully described.

SHIFT_TABLE = [
    0x0C, 0x1E, 0x05, 0x0E, 0x27, 0x00, 0x1F, 0x08,
    0x1C, 0x2C, 0x15, 0x2F, 0x25, 0x38, 0x3E, 0x2E,
    0x3B, 0x26, 0x13, 0x33, 0x2D, 0x0D, 0x21, 0x0A,
    0x31, 0x12, 0x10, 0x06, 0x0B, 0x3D, 0x3F, 0x30,
    0x2B, 0x34, 0x02, 0x17, 0x18, 0x22, 0x29, 0x04,
    0x32, 0x16, 0x23, 0x24, 0x37, 0x28, 0x3A, 0x39,
    0x07, 0x1B, 0x11, 0x14, 0x35, 0x1D, 0x3C, 0x0F,
    0x01, 0x03, 0x1A, 0x19, 0x09, 0x2A, 0x20, 0x36
]

def find_index_in_shift_table(element):
    """Find index c such that SHIFT_TABLE[c] == element"""
    for c in range(64):
        if SHIFT_TABLE[c] == element:
            return c
    raise ValueError(f"Element {element} not found in shift table")

# Precompute the inverse shift table for efficiency
INV_SHIFT_TABLE = [0] * 64
for i in range(64):
    INV_SHIFT_TABLE[SHIFT_TABLE[i]] = i

def apply_forward_perm(bit_idx):
    """One step of forward permutation: SHIFT_TABLE[bit] + 11 mod 64"""
    result = SHIFT_TABLE[bit_idx] + 11
    if result >= 64:
        result -= 64
    return result

def apply_inverse_perm(bit_idx):
    """One step of inverse permutation: FindIndexInShiftTable(bit - 11 mod 64)"""
    val = bit_idx - 11
    if val < 0:
        val += 64
    return find_index_in_shift_table(val)

def compute_target_bits():
    """Compute acWantedKeyBits: for each bit, apply forward perm 0x3D=61 times"""
    target = []
    for bit in range(64):
        current = bit
        for _ in range(0x3D):
            current = apply_forward_perm(current)
        target.append(current)
    return target

def find_valid_exponents(max_exp=65535):
    """Find all exponents e such that applying inverse perm e times == target"""
    target = compute_target_bits()
    valid = []
    for e in range(1, max_exp + 1):
        ok = True
        for bit in range(64):
            current = bit
            for _ in range(e):
                current = apply_inverse_perm(current)
            if current != target[bit]:
                ok = False
                break
        if ok:
            valid.append(e)
    return valid

# Precompute valid exponents (expensive, cached)
_VALID_EXPONENTS = None

def get_valid_exponents():
    global _VALID_EXPONENTS
    if _VALID_EXPONENTS is None:
        # Use efficient approach with precomputed inverse perm
        target = compute_target_bits()
        # Build inverse perm as array
        inv_perm = [apply_inverse_perm(b) for b in range(64)]
        valid = []
        for e in range(1, 65536):
            ok = all(
                _apply_perm_n_times(inv_perm, b, e) == target[b]
                for b in range(64)
            )
            if ok:
                valid.append(e)
        _VALID_EXPONENTS = valid
    return _VALID_EXPONENTS

def _apply_perm_n_times(perm, start, n):
    current = start
    for _ in range(n):
        current = perm[current]
    return current

def permute_bits_64(value, perm):
    """Apply a bit permutation to a 64-bit integer.
    perm[i] = j means bit i of output comes from bit j of input.
    # ASSUMPTION: perm[i] = j means output bit i = input bit perm[i]
    """
    result = 0
    for i in range(64):
        src_bit = perm[i]
        if (value >> src_bit) & 1:
            result |= (1 << i)
    return result

def name_to_hash(name):
    """Derive a 64-bit value from name.
    # ASSUMPTION: The exact hash function is not fully described in the writeup.
    # Using a simple accumulation as a placeholder.
    """
    # ASSUMPTION: Simple sum-based hash - actual algorithm unknown
    h = 0
    for i, ch in enumerate(name.encode('ascii', errors='replace')):
        h ^= (ch << (i % 64))
    h &= 0xFFFFFFFFFFFFFFFF
    return h

def build_inv_perm_n(inv_perm_1, n):
    """Build the permutation that is inv_perm applied n times."""
    # Represent as array: result[i] = final position of bit i
    current = list(range(64))
    for _ in range(n):
        current = [inv_perm_1[current[i]] for i in range(64)]
    return current

def verify(name, serial):
    """
    Verify name/serial pair.
    # ASSUMPTION: serial is an integer (64-bit) or hex string.
    # The check: permuting the serial's bits by the inverse permutation
    # (applied e times for some valid exponent e) yields the name hash,
    # OR equivalently, serial = permute(name_hash, forward_perm^e).
    # ASSUMPTION: actual serial format (string vs int) unknown.
    """
    if isinstance(serial, str):
        try:
            serial_int = int(serial, 16)
        except ValueError:
            return False
    else:
        serial_int = int(serial)

    name_hash = name_to_hash(name)

    inv_perm_1 = [apply_inverse_perm(b) for b in range(64)]
    valid_exps = get_valid_exponents()

    for e in valid_exps:
        perm_e = build_inv_perm_n(inv_perm_1, e)
        if permute_bits_64(serial_int, perm_e) == name_hash:
            return True
    return False

def keygen(name):
    """
    Generate a valid serial for a given name.
    # ASSUMPTION: We use the first valid exponent and the forward permutation.
    """
    name_hash = name_to_hash(name)
    valid_exps = get_valid_exponents()
    if not valid_exps:
        raise RuntimeError("No valid exponents found")
    e = valid_exps[0]
    # Forward perm: SHIFT_TABLE[bit] + 11 mod 64
    fwd_perm = [apply_forward_perm(b) for b in range(64)]
    # Apply forward perm e times
    perm_e = build_inv_perm_n(fwd_perm, e)  # reuse helper
    serial_int = permute_bits_64(name_hash, perm_e)
    return hex(serial_int)


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
