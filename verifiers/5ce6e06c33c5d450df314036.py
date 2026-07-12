import hashlib

# Reference values from the .data section of the binary
# These are the target BigInt values that (a,b,c,d) must match
ref_A = 0x1360c554fd8f1854e088068581813641971
ref_B = 0x0567d9219d633c8545008938310657f7de6
ref_C = 0x0b6c0f3a5189e6bce5f9c1b08b56079cf90
ref_D = 0x032fb0ce324549719a8ae49f0bd02af58f1

# Known correct password SHA1 hashes (from comments)
# SHA1 = c2008e29ab0ea2383a1afb5010309d4097f8f7c3  (intended)
# SHA1 = 7c9072c5d04b607523834d174e51366cc65cd666  (alternate, due to bug)


def password_to_bits(password):
    """Convert a password string to the bit stream used by the algorithm.
    
    For each character, extract bits from LSB to MSB, stopping after
    the last set bit (i.e., leading zeros within the byte are discarded).
    This matches the do { x = ch & 1; ch >>= 1; } while (ch != 0) loop.
    """
    bits = []
    for ch in password:
        n = ord(ch)
        while True:
            bit = n & 1
            bits.append(bit)
            n >>= 1
            if n == 0:
                break
    return bits


def simulate(bits):
    """Run the BigInt state machine on a bit stream.
    
    Initial state: a=1, b=0, c=0, d=1
    For each bit:
        if bit == 0: d += c, b += a
        if bit == 1: c += d, a += b
    Returns (a, b, c, d)
    """
    a, b, c, d = 1, 0, 0, 1
    for bit in bits:
        if bit == 0:
            d += c
            b += a
        else:
            c += d
            a += b
    return a, b, c, d


def verify(name, serial):
    """Verify a password (serial) against the reference values.
    Note: 'name' is unused; this crackme only checks the password.
    """
    bits = password_to_bits(serial)
    a, b, c, d = simulate(bits)
    return a == ref_A and b == ref_B and c == ref_C and d == ref_D


# --- Keygen via reverse Euclidean algorithm ---

def solve_euclidean(x, y, initial_state):
    """Work backwards from (x, y) to (1, 0) or (0, 1) using a subtraction
    variant of the Euclidean algorithm, collecting bits along the way.
    
    initial_state: (1, 0) means we stop when (a, b) = (1, 0) -> last bit = 1
                   (0, 1) means we stop when (a, b) = (0, 1) -> last bit = 0
    Returns list of bits (forward order, i.e. reversed after collection).
    """
    bits = []
    # We want to reduce (x, y) toward the starting conditions
    # If x >= y: previous step was bit=1 (a += b, so a was a-b)
    # If x < y:  previous step was bit=0 (b += a, so b was b-a)
    # We stop when we reach the pre-loop state
    # For (a,b) pair starting at (1,0): initial before any bit-1 step gives (1,0)
    # For (c,d) pair starting at (0,1): initial before any bit-0 step gives (0,1)
    while True:
        if initial_state == (1, 0):
            # a starts at 1, b starts at 0
            # terminal condition: a=1, b=0
            if x == 1 and y == 0:
                break
            if y == 0:
                # degenerate
                break
            if x >= y:
                x = x - y
                bits.append(1)
            else:
                y = y - x
                bits.append(0)
        else:
            # c starts at 0, d starts at 1
            # terminal condition: c=0, d=1
            if x == 0 and y == 1:
                break
            if x == 0:
                break
            if y >= x:
                y = y - x
                bits.append(0)
            else:
                x = x - y
                bits.append(1)
    return bits


def bits_to_char(bits_lsb_first):
    """Convert a list of bits (LSB first) to a character.
    The bits are in LSB-first order as produced by password_to_bits.
    """
    val = 0
    for i, b in enumerate(bits_lsb_first):
        val |= (b << i)
    return chr(val)


def dfs_bits_to_string(bits, exclude_chars=None):
    """Try to reconstruct a printable ASCII string from a bit stream (LSB-first).
    
    Printable ASCII chars (0x20-0x7e) contribute either 6 or 7 bits
    (since bit length of n = floor(log2(n))+1, for 0x20-0x3f: 6 bits, 0x40-0x7f: 7 bits).
    The MSB of each char is always 1 (not stored in stream), so:
      - 6-bit contribution: chars 0x20-0x3f (bit[5] must be 1)
      - 7-bit contribution: chars 0x40-0x7f (bit[6] must be 1)
    """
    if exclude_chars is None:
        exclude_chars = set()
    
    results = []
    
    def dfs(pos, current_str):
        if pos == len(bits):
            results.append(current_str)
            return
        if len(results) >= 10:  # limit results
            return
        for num_bits in [6, 7]:
            if pos + num_bits > len(bits):
                continue
            # The MSB of the char within num_bits must be 1
            if bits[pos + num_bits - 1] != 1:
                continue
            ch = bits_to_char(bits[pos:pos + num_bits])
            code = ord(ch)
            if 0x20 <= code <= 0x7e and ch not in exclude_chars:
                dfs(pos + num_bits, current_str + ch)
    
    dfs(0, '')
    return results


def keygen(name):
    """Generate a valid password for the crackme.
    name is ignored (crackme doesn't use a name).
    
    Strategy:
    1. Use reverse Euclidean on (ref_A, ref_B) to get the (a,b) bit stream.
    2. Use reverse Euclidean on (ref_C, ref_D) to get the (c,d) bit stream.
    3. The two bit streams must be identical (same password drives both pairs).
       ASSUMPTION: The longer stream is the correct one; they should agree.
    4. Convert bit stream back to printable ASCII string.
    """
    # Solve for (a, b) pair: starts at (1, 0)
    bits_ab = solve_euclidean(ref_A, ref_B, (1, 0))
    bits_ab_fwd = bits_ab[::-1]  # reverse to get forward order
    
    # Solve for (c, d) pair: starts at (0, 1)
    bits_cd = solve_euclidean(ref_C, ref_D, (0, 1))
    bits_cd_fwd = bits_cd[::-1]  # reverse to get forward order
    
    # Use the longer bit stream
    # ASSUMPTION: both streams should be the same; take the longer one
    if len(bits_ab_fwd) >= len(bits_cd_fwd):
        bits = bits_ab_fwd
    else:
        bits = bits_cd_fwd
    
    # Try to convert bit stream to printable string
    candidates = dfs_bits_to_string(bits)
    if candidates:
        return candidates[0]
    
    # Fallback: return raw bit stream as string representation
    return ''.join(str(b) for b in bits)



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
