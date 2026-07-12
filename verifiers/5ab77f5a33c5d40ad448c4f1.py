# Reverse-engineered keygen for CrackMe #1 by Haunted
# Based on Solution 3 (chaise) assembly trace
#
# Serial format: HNT-XXXX-YYYY-ZZZZ-CC
# where XXXX, YYYY, ZZZZ are 4-digit decimal groups and CC are 2 capital letters
#
# From the assembly trace (Solution 3 / chaise):
#
# name = e.g. "chaise", length = 6
# Step 1: Compute first group
#   first_char = name[0]
#   last_char  = name[-1]
#   mid_index  = length // 2          (integer division)
#   mid_char   = name[mid_index]
#   val1 = ord(first_char) * ord(last_char) * ord(mid_char)
#   group1 = val1 % 10000  (4-digit decimal via CALL 00401345 which extracts 4 decimal digits)
#
# ASSUMPTION: The 4-digit extraction in CALL 00401345 extracts the last 4 decimal digits (i.e. val % 10000)
#   The assembly does: for i in range(4,0,-1): digit = val % 10; val //= 10
#   So group1 = last 4 decimal digits of val1 (zero-padded)
#
# Step 2: Compute second group via CALL 00401363 + CALL 0040137B
#   CALL 0040137B computes:
#     result = length  (eax = strlen)
#     loop from ecx=length down to 1:
#       edx = name[ecx-1]  (1-indexed from end, ebx is base-1 pointer)
#       edx = edx * ecx
#       result += edx
#     Actually from the disasm:
#       EBX points to name[-1] (DEC EBX before loop)
#       ECX starts at length
#       loop: DL = DS:[EBX+ECX] = name[ecx-1]  (0-indexed)
#             EDX *= ECX
#             EAX += EDX
#             ECX--; if ECX != 0 loop
#     Initial EAX = length
#   ASSUMPTION: group2 is the last 4 decimal digits of that sum
#
# Step 3: The third group
# ASSUMPTION: Not fully traced; from Solution 3 tables, a similar computation.
#   We assume group3 is derived similarly. The writeup is truncated.
#   We use a ASSUMPTION placeholder.
#
# Step 4: The two trailing capital letters
#   From examples:
#     name="thomas"  -> CC=CS  (serial: HNT-4060-5920-3648-CS)
#     name="name"    -> CC=BB  (serial: HNT-0990-1287-5636-BB)
#     name="chaise"  -> CC=XF  (serial: HNT-9895-0549-4960-XF)
#     name="xylitol" -> CC=JJ  (serial: HNT-0800-5907-8736-JJ)
#   ASSUMPTION: not enough info to reverse CC. We mark as unknown.

def _extract4(val):
    """Extract last 4 decimal digits of val (as done by CALL 00401345)."""
    digits = []
    v = val
    for _ in range(4):
        digits.append(v % 10)
        v //= 10
    # digits are stored from least-significant; the loop writes them in reverse
    # assembly: loop 4 times, store digit at [EBX+ECX] for ECX=4,3,2,1
    # so result string is digits[3]digits[2]digits[1]digits[0] (most-sig first)
    return '{}{}{}{}'.format(digits[3], digits[2], digits[1], digits[0])

def _call_137b(name):
    """CALL 0040137B: accumulates weighted sum of characters."""
    n = len(name)
    eax = n
    ecx = n
    # EBX = pointer to name[-1], i.e. DS:[EBX+ECX] = name[ecx-1] (0-indexed)
    while ecx > 0:
        dl = ord(name[ecx - 1])
        dl = (dl * ecx) & 0xFFFFFFFF
        eax = (eax + dl) & 0xFFFFFFFF
        ecx -= 1
    return eax

def _group1(name):
    """Compute first 4-digit group."""
    n = len(name)
    first = ord(name[0])
    last  = ord(name[-1])
    mid   = n // 2
    # ASSUMPTION: mid_index from: PUSH EAX (=n), ECX=2, PUSH EDX (=first*last), IDIV ECX -> EAX=n//2
    mid_char = ord(name[mid])
    val = (first * last * mid_char) & 0xFFFFFFFF
    return _extract4(val), val

def _group2(name):
    """Compute second 4-digit group via CALL 0040137B.
    ASSUMPTION: The value fed to the digit extractor is the result of CALL 0040137B on name.
    The computer name is fetched but per chaise's note 'Don't use for generate' it's not used in the key.
    """
    val = _call_137b(name)
    return _extract4(val), val

def _group3(name):
    """ASSUMPTION: Third group computation not fully traced in write-ups.
    We assume it is a further computation on the name. Placeholder returns '0000'."""
    # ASSUMPTION: unknown algorithm for third group
    # From observed serials we cannot deduce a clear pattern without more disasm.
    return '????', 0

def _suffix(name):
    """ASSUMPTION: Two trailing uppercase letters - algorithm not recovered from write-ups."""
    return '??'

def keygen(name):
    if not name:
        return None
    g1, _ = _group1(name)
    g2, _ = _group2(name)
    g3, _ = _group3(name)
    cc    = _suffix(name)
    return 'HNT-{}-{}-{}-{}'.format(g1, g2, g3, cc)

def verify(name, serial):
    """Verify serial against the crackme's expected serial.
    Since group3 and suffix are not fully recovered, this is a partial check.
    Returns True only if the fully-known parts match.
    ASSUMPTION: partial verification only.
    """
    if not name or not serial:
        return False
    parts = serial.upper().split('-')
    if len(parts) != 5:
        return False
    if parts[0] != 'HNT':
        return False
    # Check group1
    g1, _ = _group1(name)
    if g1 == '????' or parts[1] != g1:
        pass  # ASSUMPTION: skip if not computable
    # Check group2
    g2, _ = _group2(name)
    if g2 == '????' or parts[2] != g2:
        pass  # ASSUMPTION: skip if not computable
    # ASSUMPTION: groups 3 and suffix not fully known, accept any
    # For a full verify we'd need all parts; return partial match
    g1_ok = (parts[1] == g1)
    g2_ok = (parts[2] == g2)
    return g1_ok and g2_ok

# --- Self-test against known name/serial pairs ---
# name="name"   serial="HNT-0990-1287-5636-BB"
# name="chaise" serial="HNT-9895-0549-4960-XF"
# name="xylitol" serial="HNT-0800-5907-8736-JJ"
# name="thomas"  serial="HNT-4060-5920-3648-CS"


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
