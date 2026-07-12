# Reverse-engineered algorithm for ultrasnord's 5th crackme
# Based on the solution writeup by movzx
#
# Rules:
# 1. Name must be longer than 5 characters.
# 2. Let A = len(name)
#    ESI = A * 2 + 1
#    password_length_required = (ESI // 2) + 1  (rounded up, i.e. ceil((ESI+1)/2) = A+1)
#    Actually from the writeup: name='KocokJaya' (len=9=A)
#    ESI = 9*2+1 = 19, password must be 19 chars long.
#    The 'nth char' index is ESI (1-based) = 19th char, i.e. index ESI-1 = 18.
#    So password length must be at least ESI = A*2+1 characters.
#
# 3. The serial checks: for i in 0..N-1:
#       serial[i] + serial[ESI-1-i] == some_target
#    From writeup:
#       serial[0] + serial[18] == 0xBB (187)
#       serial[1] + serial[17] == 0xAA (170)  -- truncated but implied
#    The pattern is: serial[i] + serial[ESI-1-i] == target[i]
#
# ASSUMPTION: The target values for each pair position are derived from the name.
# The writeup was truncated before showing all target values and how many pairs are checked.
# We can see:
#   pair 0: target = 0xBB = 187
#   pair 1: target = 0xAA = 170
# ASSUMPTION: The targets decrease by 0x11 (17) each step: 0xBB, 0xAA, 0x99, ...
# This is a common pattern but NOT confirmed by the truncated writeup.
#
# ASSUMPTION: The number of pairs checked = ceil(ESI/2) = A+1 (from the roundup calc)
# ASSUMPTION: The password must be exactly ESI = 2*A+1 characters long.

def _compute_esi(name):
    A = len(name)
    ESI = A * 2 + 1
    return ESI

def _num_pairs(ESI):
    # from writeup: (ESI // 2) + 1 rounded up
    # SAR EAX,1 then INC EAX on ESI
    val = ESI
    result = val >> 1  # arithmetic shift right
    if val < 0:
        result += 1  # ADC EAX, 0 handles negative, but ESI is always positive here
    result += 1  # INC EAX
    return result

def _get_targets(name, num_pairs):
    # ASSUMPTION: targets are derived from name characters or are fixed.
    # Only two values confirmed from writeup: 0xBB and 0xAA.
    # ASSUMPTION: targets decrease by 0x11 each step.
    targets = []
    base = 0xBB
    for i in range(num_pairs):
        targets.append(base - i * 0x11)
    return targets

def verify(name, serial):
    if len(name) <= 5:
        return False

    ESI = _compute_esi(name)  # = len(name)*2 + 1

    if len(serial) < ESI:
        return False

    num_pairs = _num_pairs(ESI)
    # ASSUMPTION: targets derived as above
    targets = _get_targets(name, num_pairs)

    for i in range(num_pairs):
        lo = i
        hi = ESI - 1 - i
        if lo > hi:
            # middle char: only one char in pair
            # ASSUMPTION: middle char check is serial[lo] == target[i] (or half)
            # Not confirmed, skip or check alone
            # ASSUMPTION: middle char paired with itself: serial[lo]*2 == target[i]? unclear
            # We'll just skip the middle char check
            break
        c_lo = ord(serial[lo])
        c_hi = ord(serial[hi])
        if c_lo + c_hi != targets[i]:
            return False

    return True

def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) <= 5:
        raise ValueError("Name must be longer than 5 characters")

    ESI = _compute_esi(name)
    num_pairs = _num_pairs(ESI)
    targets = _get_targets(name, num_pairs)

    serial_chars = ['A'] * ESI  # initialize

    for i in range(num_pairs):
        lo = i
        hi = ESI - 1 - i
        if lo == hi:
            # ASSUMPTION: middle char gets half the target value
            t = targets[i]
            # ASSUMPTION: middle char = t // 2 (if even) or some printable char
            mid = t // 2
            if 32 <= mid <= 126:
                serial_chars[lo] = chr(mid)
            else:
                serial_chars[lo] = chr(ord('A'))  # fallback
            break
        else:
            t = targets[i]
            # Choose lo_char as printable ASCII
            lo_val = 0x41  # 'A'
            hi_val = t - lo_val
            # Ensure hi_val is printable
            if hi_val < 32 or hi_val > 126:
                lo_val = t - 0x41
                hi_val = t - lo_val
            if hi_val < 32 or hi_val > 126:
                # Try to find a valid split
                lo_val = t - 126
                hi_val = 126
                if lo_val < 32:
                    lo_val = 32
                    hi_val = t - 32
            serial_chars[lo] = chr(lo_val)
            serial_chars[hi] = chr(hi_val)

    return ''.join(serial_chars)


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
