import struct
import itertools

# CPUID-based key generation:
# The crackme reads CPUID(EAX=1) and computes:
#   cpu_model  = (EAX >> 4) & 0xF
#   cpu_family = (EAX >> 8) & 0xF
#   ext_model  = (EAX >> 16) & 0xF
#   if family == 15: family += (EAX >> 20) & 0xFF
#   if family == 6 or family == 15: model += ext_model << 4
#   key = family + model  (uint8)
#
# Checksum algorithm (from solution source + MateiM writeup):
#   For each character c at index i (including trailing newline '\n'):
#       checksum += key XOR (i XOR ord(c))
#   Valid if checksum == key + 1505  (i.e. key + 0x5E1)
#
# Note: MG in lexx's solution is 0x5e1 = 1505, confirming the constant.
# The input includes a trailing '\n' (from fgets), so the password string
# fed to the check is the typed characters PLUS '\n' at the end.

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MG = 0x5E1  # 1505


def compute_checksum(password_with_newline: str, key: int) -> int:
    """Compute the checksum over the password string (including trailing newline)."""
    checksum = 0
    for i, c in enumerate(password_with_newline):
        checksum += key ^ (i ^ ord(c))
    return checksum


def verify(name: str, serial: str, key: int = None) -> bool:
    """Verify serial (password). name is ignored; key is the CPU-derived value.
    If key is None, a ASSUMPTION default of 26 (from MateiM's example) is used."""
    # ASSUMPTION: name is not used in validation; only serial/password matters.
    if key is None:
        # ASSUMPTION: default key=26 matches MateiM's example CPU (family=6, model=20 -> 26)
        key = 26
    key = key & 0xFF
    target = key + MG  # key + 1505
    # fgets includes trailing newline
    pwd_with_nl = serial + '\n'
    checksum = compute_checksum(pwd_with_nl, key)
    return checksum == target


def keygen(name: str = "", key: int = None):
    """Generate a valid password for the given CPU key.
    Uses dynamic programming similar to lexx's C++ solution.
    Yields valid password strings (without newline)."""
    # ASSUMPTION: name is not used in the algorithm
    if key is None:
        # ASSUMPTION: default key=26 for MateiM's example
        key = 26
    key = key & 0xFF
    target = key + MG  # total checksum needed

    # We include the trailing newline as the last character.
    # Strategy: fix password length, compute contribution of '\n' at position=length,
    # then find characters at positions 0..length-1 summing to (target - nl_contrib).
    #
    # Use DP over positions. precompute contribution table.
    #
    # Try various lengths.

    def contrib(i, c_val, k):
        return k ^ (i ^ c_val)

    for length in range(1, 50):
        # newline is at index = length
        nl_contrib = contrib(length, ord('\n'), key)
        max_sum = target - nl_contrib
        if max_sum < 0:
            continue

        # DP: dp[sum] = last char index chosen
        # Build forward DP
        # dp[pos] is a dict: sum -> (char_index)
        # To reconstruct, store parent info
        # Use list of dicts for memory efficiency on small lengths

        # precompute per-position contributions
        pos_contribs = []
        for pos in range(length):
            pos_contribs.append([(c, contrib(pos, ord(c), key)) for c in CHARSET])

        # dp[pos][partial_sum] = char chosen at pos-1
        dp = [dict() for _ in range(length + 1)]
        dp[0][0] = None  # sentinel

        for pos in range(length):
            for partial_sum in dp[pos]:
                for (c, cv) in pos_contribs[pos]:
                    new_sum = partial_sum + cv
                    if new_sum <= max_sum and new_sum not in dp[pos + 1]:
                        dp[pos + 1][new_sum] = (c, partial_sum)

        if max_sum not in dp[length]:
            continue  # no solution at this length

        # Reconstruct
        result = []
        cur_sum = max_sum
        for pos in range(length, 0, -1):
            c, prev_sum = dp[pos][cur_sum]
            result.append(c)
            cur_sum = prev_sum
        result.reverse()
        password = ''.join(result)

        # Verify
        if verify(name, password, key):
            yield password
            return  # yield first valid, then stop

    # If no solution found with small lengths
    return


def get_cpu_key_from_eax(eax: int) -> int:
    """Given raw EAX value from CPUID(1), compute the crackme's key byte."""
    model  = (eax >> 4) & 0xF
    family = (eax >> 8) & 0xF
    ext_model = (eax >> 16) & 0xF
    if family == 15:
        family += (eax >> 20) & 0xFF
    if family == 6 or family == 15:
        model += ext_model << 4
    return (family + model) & 0xFF



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
            print(_sv)
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
