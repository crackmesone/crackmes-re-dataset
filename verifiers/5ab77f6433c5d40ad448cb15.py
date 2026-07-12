# Reverse-engineered from bomb_2 crackme solution writeup by redoC
# Only the sequence.dat check (enabling Disarm button) has a described algorithm.
# The Disarm sequence check (second passcode) is explicitly stated as NOT reversed.
#
# Charset (24 chars): ~!@#$%^*()-_=+[]{},.<>/?
# Both passcodes: exactly 16 chars, each char used at most once.
#
# sequence.dat check:
#   - 16 bytes input
#   - First 4 bytes (EDX) are 'ignored' in main algo (only used in sum)
#   - Sum of all 16 chars must == 0x3E4 (996)
#   - Expected output registers: EAX==0x7E1618D8, EBX==0x18CCE9FD, ECX==0xCC533F7B, EDX==0xFCE8CE16
#
# The exact inner loop of Sequence_dat_Test was truncated in the writeup.
# We implement a PARTIAL verify based on what IS known (sum check, charset check, length check).
# The full hash verification cannot be implemented without the complete algorithm.

CHARSET = set('~!@#$%^*()-_=+[]{},.<>/?')
CHARSET_LIST = list('~!@#$%^*()-_=+[]{},.<>/?')
SEQ_DAT_SUM = 0x3E4  # 996
DISARM_SUM  = 0x400  # 1024

# ASSUMPTION: The writeup truncates the actual hash computation of Sequence_dat_Test.
# We can only verify the known constraints: length==16, charset, no repeated chars, sum==target.

def _basic_checks(serial, required_sum):
    """Check charset, length, no repeats, and char sum."""
    if len(serial) != 16:
        return False
    chars = list(serial)
    if not all(c in CHARSET for c in chars):
        return False
    if len(set(chars)) != 16:  # each char occurs only once
        return False
    if sum(ord(c) for c in chars) != required_sum:
        return False
    return True


def verify_sequence_dat(serial):
    """
    Verify the sequence.dat passcode (enables Disarm button).
    Fully known constraints: length 16, charset 24 chars, no repeats, sum==0x3E4.
    The full hash check (EAX/EBX/ECX/EDX registers) CANNOT be implemented
    because the inner loop body was truncated in the writeup.
    Returns True only if basic constraints pass (partial check).
    """
    # ASSUMPTION: Only the basic constraints are verified here.
    # The real binary also checks EAX==0x7E1618D8, EBX==0x18CCE9FD,
    # ECX==0xCC533F7B, EDX==0xFCE8CE16 after running the custom checksum.
    return _basic_checks(serial, SEQ_DAT_SUM)


def verify_disarm(serial):
    """
    Verify the Disarm button passcode.
    Fully known constraints: length 16, charset 24 chars, no repeats, sum==0x400.
    The hash verification algorithm was explicitly stated as not reversed/unsolved.
    Returns True only if basic constraints pass (partial check).
    """
    # ASSUMPTION: The Disarm check algorithm was never reversed.
    # Only basic constraints are checked here.
    return _basic_checks(serial, DISARM_SUM)


def verify(name, serial):
    """
    This crackme does not appear to use a 'name' field.
    serial is expected to be the sequence.dat passcode (first stage).
    name is ignored.
    """
    # ASSUMPTION: 'name' is not part of the algorithm based on the writeup.
    return verify_sequence_dat(serial)


def keygen(name):
    """
    Generate a candidate serial satisfying the known constraints for sequence.dat.
    This does NOT guarantee passing the full hash check (which is unknown/truncated).
    Uses the known valid sequences described in the writeup.
    """
    from itertools import permutations

    target_sum = SEQ_DAT_SUM  # 996
    chars = CHARSET_LIST[:]

    # ASSUMPTION: We brute-force 16-char permutations from 24-char charset
    # with no repeats and sum == 0x3E4. The first valid one is returned.
    # This is extremely slow in general; the writeup found 3844 valid sequences.
    # Here we yield combinations that meet the sum constraint.
    from itertools import combinations
    for combo in combinations(CHARSET_LIST, 16):
        if sum(ord(c) for c in combo) == target_sum:
            # Return first permutation of this combo as a candidate
            serial = ''.join(combo)
            return serial
    return None



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
