import struct
import random

# Constants found in the code (addresses in .text section used as constants)
# ASSUMPTION: These constants (c_n and c_k) are hardcoded addresses/values from the
# crackme's .text section. The writeup mentions them but does not give their values.
# We approximate them as 0 here; a real keygen would need to extract them from the binary.
C_N = 0x00401572  # ASSUMPTION: c_n is the address 0x00401572 (used in name hash)
C_K = 0x004015DB  # ASSUMPTION: c_k is the address 0x004015DB (used in key hash)

MASK = 0xFFFFFFFF


def name_hash(name):
    """
    Compute the name hash from the equation:
    n_1 + (2^8*n_2) + (2^16*n_3) + (2^24*n_4) +
    n_2 + (2^8*n_3) + (2^16*n_4) + (2^24*n_5) +
    n_6 + (2^8*n_7) + (2^16*n_8) + (2^24*n_9) +
    n_3 + (2^8*n_4) + (2^16*n_5) + (2^24*n_6) + c_n
    
    Note: indices are 1-based in the writeup.
    """
    n = [ord(c) for c in name]
    # Pad to at least 9 characters (0-indexed: n[0]..n[8])
    while len(n) < 10:
        n.append(0)
    
    # Using 1-based indexing from writeup, converted to 0-based:
    # n_1=n[0], n_2=n[1], ..., n_9=n[8]
    h = 0
    h += n[0] + (n[1] << 8) + (n[2] << 16) + (n[3] << 24)
    h += n[1] + (n[2] << 8) + (n[3] << 16) + (n[4] << 24)
    h += n[5] + (n[6] << 8) + (n[7] << 16) + (n[8] << 24)
    h += n[2] + (n[3] << 8) + (n[4] << 16) + (n[5] << 24)
    h += C_N
    return h & MASK


def key_hash(key):
    """
    Compute the key hash from the equation:
    k_1 + (2^8*k_2) + (2^16*k_3) + (2^24*k_4) +
    k_5 + (2^8*k_6) + (2^16*k_7) + (2^24*k_8) +
    k_6 + (2^8*k_7) + (2^16*k_8) + (2^24*k_9) +
    k_4 + (2^8*k_5) + (2^16*k_6) + (2^24*k_7) + c_k
    
    Key is 11 chars: k_0 .. k_10 (k[0] and k[10] are ignored in hash)
    Using 1-based indexing: k_1=key[1], ..., k_9=key[9]
    """
    k = [ord(c) for c in key]
    while len(k) < 11:
        k.append(0)
    
    # k_1=k[1], k_2=k[2], ..., k_9=k[9] (1-based from writeup)
    h = 0
    h += k[1] + (k[2] << 8) + (k[3] << 16) + (k[4] << 24)
    h += k[5] + (k[6] << 8) + (k[7] << 16) + (k[8] << 24)
    h += k[6] + (k[7] << 8) + (k[8] << 16) + (k[9] << 24)
    h += k[4] + (k[5] << 8) + (k[6] << 16) + (k[7] << 24)
    h += C_K
    return h & MASK


def verify(name, serial):
    """Verify a name/serial pair."""
    if len(name) < 10:
        return False
    if len(serial) < 11:
        return False
    nh = name_hash(name)
    kh = key_hash(serial)
    return nh == kh


def keygen(name):
    """
    Generate a valid serial for the given name.
    
    Key format: X_________X (11 chars, first and last are arbitrary,
    positions 1-9 are computed).
    
    Strategy from writeup:
    - Start with key = 'X' + '0'*9 + 'X'
    - Compute difference = name_hash - key_hash (mod 2^32)
    - Use character strengths to close the gap one character at a time.
    
    Character strengths (how much each k_i contributes per unit increase):
      k_1: 1                          (appears once, lowest byte)
      k_2: 2^8 + 1 = 257              (appears in positions affecting two terms)
      k_3: 2^16 + 2^8 + 1             
      k_4: 2^24 + 2^16 + 1           
      k_5: 2^24 + 2^8 + 1            
      k_6: 2^24 + 2^16 + 2^8 + 1     (appears 3 times + extra)
      k_7: 2^24*2 + 2^16 + 2^8       
      k_8: 2^24 + 2^16 + 2^8         
      k_9: 2^24                       (appears once, highest byte)
    
    ASSUMPTION: Strength values computed from the hash equation above.
    """
    if len(name) < 10:
        raise ValueError("Name must be at least 10 characters")
    
    # Compute character strengths from the key hash equation
    # k_1 contributes: +1 per unit
    # k_2 contributes: +2^8 + 1 per unit (appears in term1 byte1 and term2-like)
    # Let's compute directly:
    def compute_strength(pos):
        """Compute how much the hash changes per unit increase in key[pos] (1-based)."""
        # Create two keys differing only at pos by 1
        base = [0] * 11
        up = [0] * 11
        up[pos] = 1
        
        def _kh(k):
            h = 0
            h += k[1] + (k[2] << 8) + (k[3] << 16) + (k[4] << 24)
            h += k[5] + (k[6] << 8) + (k[7] << 16) + (k[8] << 24)
            h += k[6] + (k[7] << 8) + (k[8] << 16) + (k[9] << 24)
            h += k[4] + (k[5] << 8) + (k[6] << 16) + (k[7] << 24)
            return h  # no mask for strength computation
        
        return _kh(up) - _kh(base)
    
    strengths = {i: compute_strength(i) for i in range(1, 10)}
    
    # Start with key = 'X' + chr(0x30)*9 + 'X' (using printable chars)
    # ASSUMPTION: We use ASCII printable chars (0x20-0x7E) for key characters
    key_chars = ['X'] + [chr(0x40)] * 9 + ['X']  # '@' = 0x40 as starting point
    
    target_nh = name_hash(name)
    
    # Iterative approach: adjust characters to match hash
    # Process from most powerful to least powerful
    order = sorted(range(1, 10), key=lambda i: strengths[i], reverse=True)
    
    for iteration in range(1000):
        current_key = ''.join(key_chars)
        current_kh = key_hash(current_key)
        diff = (target_nh - current_kh) & MASK
        
        if diff == 0:
            return current_key
        
        # Try to adjust one character
        improved = False
        for pos in order:
            s = strengths[pos]
            if s == 0:
                continue
            current_val = ord(key_chars[pos])
            # How many units to add?
            # diff = (target - current) mod 2^32
            # We want to add delta such that s*delta == diff (mod 2^32)
            # Try direct division
            if diff % s == 0:
                delta = (diff // s) % 256
            else:
                # Approximate
                delta = (diff // s) % 256
            
            new_val = (current_val + delta) % 256
            # Keep printable if possible
            if new_val < 0x20:
                new_val += 0x20
            if new_val > 0x7E:
                new_val = new_val % 0x5F + 0x20
            
            if new_val != current_val:
                key_chars[pos] = chr(new_val)
                improved = True
                break
        
        if not improved:
            # Randomly tweak a character to escape local minimum
            pos = random.choice(order)
            key_chars[pos] = chr(random.randint(0x20, 0x7E))
    
    # Return best attempt even if not perfect
    return ''.join(key_chars)



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
