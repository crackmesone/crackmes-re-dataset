# vm_keygenme by genaytyk - reconstructed from disasm_commented.txt
# algorithm_recovered: partial
# Many sub-functions (call imm2FF, call imm417, call imm36C, call imm458, call imm3F2)
# are only partially described. We implement what is clearly specified and mark gaps.

import struct
import ctypes

# Valid character set for serial segments
VALID_CHARS = 'aAb0cBd1eCf2gDh3jEk4lFm5nGp6qHr7sJt8uKv9w'
BASE = 0x29  # 41 characters == len(VALID_CHARS)


def char_to_offset(c):
    """Convert a serial character to its index in VALID_CHARS."""
    idx = VALID_CHARS.find(c)
    return idx  # -1 if not found


def validate_serial_format(serial):
    """
    Check that serial has format AAAAAA-AAAAAA-AAAAAA:
    - exactly two dashes
    - each segment is exactly 6 chars
    - all non-dash chars are in VALID_CHARS
    Returns (ok, [seg0, seg1, seg2]) or (False, None)
    """
    parts = serial.split('-')
    if len(parts) != 3:
        return False, None
    for p in parts:
        if len(p) != 6:
            return False, None
        for c in p:
            if c not in VALID_CHARS:
                return False, None
    return True, parts


def member_to_dword(member):
    """
    Convert a 6-char member (already validated) to a DWORD by treating
    the offsets as a big-endian base-0x29 number.
    offset[0]*29^5 + offset[1]*29^4 + ... + offset[5]*29^0
    Returns the DWORD (as Python int, truncated to 32 bits).
    """
    result = 0
    for c in member:
        idx = char_to_offset(c)
        result = result * BASE + idx
    return result & 0xFFFFFFFF


def rol32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF


def ror32(val, n):
    val &= 0xFFFFFFFF
    n &= 31
    return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF


def transform_serial_dwords(d0, d1, d2):
    """
    Apply the rotations and XOR/ADD/SUB operations described at 40355B-4035A3.
    """
    d0 = rol32(d0, 7)
    d1 = ror32(d1, 9)
    d2 = ror32(d2, 0xB)

    d0 = (d0 ^ d1) & 0xFFFFFFFF
    d2 = (d2 + d1) & 0xFFFFFFFF
    d2 = (d2 - d0) & 0xFFFFFFFF

    return d0, d1, d2


# ASSUMPTION: The following functions are not fully described in the writeup.
# call imm2FF (4037BD) and call imm417 (4038D5) produce a DWORD from the username
# using a "hash-like operation". We implement a plausible hash but it is NOT confirmed.

def username_hash_step1(name):
    """
    ASSUMPTION: First pass over username bytes, filling a buffer at cmem+0x9D.
    The exact algorithm is not given. We use a simple additive accumulator as placeholder.
    """
    # ASSUMPTION: simple sum-based hash over username bytes
    val = 0
    for ch in name.encode('latin-1'):
        val = (val * 0x1000193 + ch) & 0xFFFFFFFF
    return val


def username_to_dword(name):
    """
    ASSUMPTION: Combines both call imm2FF and call imm417 results.
    The exact algorithm is unknown; this is a placeholder.
    """
    # ASSUMPTION: two-pass hash
    h = 0x811C9DC5  # FNV offset basis
    for ch in name.encode('latin-1'):
        h ^= ch
        h = (h * 0x1000193) & 0xFFFFFFFF
    return h


# ASSUMPTION: call imm36C (40382A) forms a pair of dwords at 403D11, 403D15 from
# the username dword. Exact method unknown. We assume it duplicates or derives.

def form_pair_from_username_dword(udword):
    """
    ASSUMPTION: Produces (pair0, pair1) at 403D11, 403D15.
    Not described in detail; placeholder.
    """
    # ASSUMPTION: pair0 = udword, pair1 = some transformation
    pair0 = udword
    pair1 = ror32(udword, 5) ^ 0xDEADBEEF  # pure assumption
    return pair0, pair1


# ASSUMPTION: call imm458 (403916) is a Feistel-like round function using
# (pair0, pair1) as key and updating (temp0, temp1). Exact algorithm unknown.
# The writeup says it is called in two loops (10 and 15 rounds).
# The constant 0x6B79745F ('_tyk' little-endian, i.e. '_tyk') is used in second loop.

def feistel_round(temp0, temp1, key0, key1):
    """
    ASSUMPTION: One round of a Feistel-like cipher.
    (temp0, temp1) are updated using (key0, key1).
    """
    # ASSUMPTION: TEA-like round
    delta = 0x9E3779B9
    temp0 = (temp0 + (((temp1 << 4) ^ (temp1 >> 5)) + temp1) ^ (key0 + delta)) & 0xFFFFFFFF
    temp1 = (temp1 + (((temp0 << 4) ^ (temp0 >> 5)) + temp0) ^ (key1 + delta)) & 0xFFFFFFFF
    return temp0, temp1


def run_loop1(temp0, temp1, pair0, pair1, rounds=10):
    """
    Loop from 4035E2: 10 rounds using pair (pair0, pair1) as keys.
    ASSUMPTION: each iteration calls feistel_round.
    """
    for _ in range(rounds):
        temp0, temp1 = feistel_round(temp0, temp1, pair0, pair1)
    return temp0, temp1


# ASSUMPTION: call imm3F2 (4038B0) computes a sum of dwords from the user bytes buffer.
# Not described in detail. We assume it returns temp1 after loop1.

def get_sum_user_bytes(state):
    """
    ASSUMPTION: Returns some value derived from the user bytes buffer after loop1.
    We just return the second element of state (temp1) as a guess.
    """
    return state[1]  # ASSUMPTION


def run_loop2(temp0, temp1, udword, constant=0x6B79745F, rounds=15):
    """
    Loop from 403659: 15 rounds using [udword][constant] as key pair.
    ASSUMPTION: each iteration calls feistel_round.
    """
    for _ in range(rounds):
        temp0, temp1 = feistel_round(temp0, temp1, udword, constant)
    return temp0, temp1


def pack_dword_le(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


OKAY_GUY = b'OKAY_GUY'


def verify(name, serial):
    """
    Verify name/serial pair.
    NOTE: Large parts of the algorithm (username hash, Feistel rounds) are ASSUMPTIONS.
    Only the serial format check, member->dword conversion, and dword transformations
    are reliably reconstructed.
    """
    # Step 1: Validate serial format
    ok, parts = validate_serial_format(serial)
    if not ok:
        return False

    seg0, seg1, seg2 = parts

    # Step 2: Convert each member to a DWORD (base-0x29 big-endian)
    d0 = member_to_dword(seg0)
    d1 = member_to_dword(seg1)
    d2 = member_to_dword(seg2)

    # Step 3: Transform the three dwords
    d0, d1, d2 = transform_serial_dwords(d0, d1, d2)

    # Step 4: Compute username dword
    # ASSUMPTION: exact hash algorithm unknown
    udword = username_to_dword(name)

    # Step 5: form_pair from username dword
    # ASSUMPTION
    pair0, pair1 = form_pair_from_username_dword(udword)

    # Step 6: Loop 1 (10 rounds) with serial_dword0 and serial_dword1
    # ASSUMPTION: feistel details unknown
    t0, t1 = run_loop1(d0, d1, pair0, pair1, rounds=10)

    # Step 7: Check that after loop1, some derived value equals serial_dword1
    # The writeup says temp1 must equal serial_dword1 after the loop and a sum call
    # ASSUMPTION: sum call returns t1
    sum_val = get_sum_user_bytes((t0, t1))
    # ASSUMPTION: this should equal d1 (the original serial_dword1)
    # Actually from writeup: must equal temp1 stored earlier = serial_dword1
    if sum_val != d1:
        pass  # ASSUMPTION: we can't reliably check this without exact sub-function

    # Step 8: Loop 2 (15 rounds) with serial_dword2, udword, 0x6B79745F
    # ASSUMPTION: start from d0,d2 or t0,d2
    t0_2, t1_2 = run_loop2(d0, d2, udword, 0x6B79745F, rounds=15)

    # Step 9: Final check - [temp0][temp1] bytes must equal "OKAY_GUY"
    result_bytes = pack_dword_le(t0_2) + pack_dword_le(t1_2)
    return result_bytes == OKAY_GUY


def keygen(name):
    """
    Generate a serial for a given name.
    ASSUMPTION: Since the Feistel/hash functions are not reliably known,
    we cannot produce a reliable keygen. This is a structural placeholder only.
    """
    # ASSUMPTION: With full knowledge of the sub-functions, we would:
    # 1. Compute udword from name
    # 2. Run loops in reverse to find d0, d1, d2
    # 3. Invert transform_serial_dwords
    # 4. Convert dwords back to base-0x29 members
    # 5. Join with '-'
    raise NotImplementedError(
        'ASSUMPTION: keygen requires exact knowledge of the Feistel rounds '
        'and username hash which are not fully described in the writeup.'
    )



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
