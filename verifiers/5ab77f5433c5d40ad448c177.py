# Cube by promix17 - Serial validation algorithm
# Based on the writeup by Dcoder
#
# The algorithm:
# 1. Start with the string "0WGWb0rWbGGbbYW0rYrYrY0G" (24 chars = 2x2x2 Rubik's cube state)
# 2. Apply MixUser(buf, name) - scrambles the cube state using the name
# 3. Apply MixSerial(buf, serial) - scrambles the cube state using the serial
# 4. The result must equal the target key: "WWWWrrrrGGGGbbbbYYYY0000"
#
# The cube state is a 24-character string representing a 2x2x2 Rubik's cube.
# Perm1, Perm2, Perm3 are face rotations on this 2x2x2 cube.
# Serial is limited to 11 characters, each must be >= 'A' (since c = *i - 'A' is used)

import itertools
from copy import deepcopy

# ASSUMPTION: The 24-char string represents 6 faces * 4 stickers of a 2x2x2 cube.
# The face order and sticker indices for Perm1/Perm2/Perm3 are not fully specified
# in the writeup. We define them as standard 2x2x2 cube moves.
# Face layout (4 stickers each, total 24):
# Face 0 (U): indices 0-3
# Face 1 (D): indices 4-7
# Face 2 (F): indices 8-11
# Face 3 (B): indices 12-15
# Face 4 (L): indices 16-19
# Face 5 (R): indices 20-23

# ASSUMPTION: Perm1, Perm2, Perm3 correspond to specific face rotations of a 2x2x2 cube.
# The writeup says there are 9 possible move types (n%3 in {0,1,2} and loops).
# We model 3 base permutations as U, F, R face clockwise rotations on the 2x2x2.
# These are standard permutations for a 2x2x2 cube.

# Sticker layout for a 2x2x2 cube (Jaap's notation-inspired):
# We use a flat list of 24 characters.
# ASSUMPTION: The following permutation cycles are approximations.
# The actual permutations are determined by disassembly of Perm1/Perm2/Perm3.

# Standard 2x2x2 cube permutations (0-indexed, 24 stickers)
# U face: [0,1,2,3], adjacent: F[0,1], R[0,1], B[0,1], L[0,1] (top rows)
# ASSUMPTION: Using a specific well-known sticker mapping

# We represent the cube as a list of 24 chars
# Positions: U=0..3, D=4..7, F=8..11, R=12..15, B=16..19, L=20..23

# ASSUMPTION: Perm1 = U move (rotate U face CW, cycle adjacent top-row stickers)
# Perm2 = R move
# Perm3 = F move
# These are standard 2x2x2 moves.

def apply_perm(state, perm):
    """Apply a permutation (list of cycles) to the state list."""
    new_state = list(state)
    for cycle in perm:
        tmp = new_state[cycle[-1]]
        for i in range(len(cycle)-1, 0, -1):
            new_state[cycle[i]] = new_state[cycle[i-1]]
        new_state[cycle[0]] = tmp
    return new_state

# ASSUMPTION: These permutation cycles approximate Perm1/Perm2/Perm3 for a 2x2x2 cube.
# Actual cycles must be determined by reverse engineering the binary.
# Using standard 2x2x2 cube sticker permutations:
# Sticker numbering:
#   U face:  0  1  2  3
#   D face:  4  5  6  7
#   F face:  8  9 10 11
#   R face: 12 13 14 15
#   B face: 16 17 18 19
#   L face: 20 21 22 23

# U clockwise: U face rotates, adjacent stickers cycle
PERM1 = [
    [0, 2, 3, 1],        # U face CW
    [8, 12, 19, 23],     # F-top-left -> R-top-left -> B-top-right -> L-top-right
    [9, 13, 18, 22],     # F-top-right -> R-top-right -> B-top-left -> L-top-left
    # ASSUMPTION: exact indices
]

# R clockwise: R face rotates, adjacent stickers cycle
PERM2 = [
    [12, 14, 15, 13],    # R face CW
    [1, 9, 4, 16],       # U -> F -> D -> B
    [3, 11, 6, 17],
    # ASSUMPTION: exact indices
]

# F clockwise: F face rotates, adjacent stickers cycle
PERM3 = [
    [8, 10, 11, 9],      # F face CW
    [2, 12, 5, 23],      # U -> R -> D -> L
    [3, 14, 4, 21],
    # ASSUMPTION: exact indices
]

PERMS = [PERM1, PERM2, PERM3]

def perm_n(state, n):
    """Apply Permute(buf, n): loop n/3+1 times applying perm n%3."""
    perm = PERMS[n % 3]
    count = n // 3 + 1
    for _ in range(count):
        state = apply_perm(state, perm)
    return state

def mix_user(state, name):
    """Apply MixUser to state using name string."""
    # First pass: permute by c % 9 for each char
    for c in name:
        n = ord(c) % 9
        state = perm_n(state, n)
    # Second pass: accumulate x and permute
    x = 0
    for c in name:
        cv = ord(c)
        x = (x + x * cv) ^ (cv * cv)
        # ASSUMPTION: x is treated as a Python int (unbounded), but we need % 9
        # The C code uses 'int x' so we mask to 32-bit signed behavior
        x = x & 0xFFFFFFFF
        if x >= 0x80000000:
            x -= 0x100000000
        n = x % 9
        # Python's % with negative numbers: ensure positive mod
        n = n % 9
        state = perm_n(state, n)
    return state

def mix_serial(state, serial):
    """Apply MixSerial to state using serial string."""
    for c in serial:
        n = ord(c) - ord('A')
        state = perm_n(state, n)
    return state

INITIAL = list("0WGWb0rWbGGbbYW0rYrYrY0G")
TARGET  = list("WWWWrrrrGGGGbbbbYYYY0000")

def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair for Cube by promix17."""
    if not serial or len(serial) > 11:
        return False
    # All serial chars must be >= 'A' (MixSerial does c - 'A')
    for c in serial:
        if ord(c) < ord('A'):
            return False
    state = list(INITIAL)
    state = mix_user(state, name)
    state = mix_serial(state, serial)
    return state == TARGET

def keygen(name: str) -> str:
    """Generate a valid serial for the given name using meet-in-the-middle."""
    # Start state after mixing with name
    state_after_name = mix_user(list(INITIAL), name)

    # Valid serial chars: 'A' and above, printable ASCII, let's use A-Z + a few more
    # ASSUMPTION: serial chars are uppercase A-Z (26 chars, indices 0-25 from 'A')
    # The writeup says 9 possible move types (n%3 * loops), but chars map via c-'A'
    # We restrict to chars that give distinct moves: 'A'..'I' give n=0..8
    # but any char >= 'A' is valid. We'll use A-Z for search.
    CHARS = [chr(i) for i in range(ord('A'), ord('Z')+1)]

    # Meet in the middle: precompute all states reachable from TARGET by applying
    # inverse serial moves of length up to 5 (going backwards).
    # Inverse of perm_n(state, n) applied k times = perm_n(state, n) applied (order-k) times
    # ASSUMPTION: We do forward search from state_after_name for simplicity (BFS up to depth 11)
    # due to the complexity of proper MITM without known inverse permutations.

    # Simple BFS (may be slow for large search spaces - use MITM in production)
    from collections import deque
    
    # State must be hashable
    def to_key(s):
        return tuple(s)
    
    target_key = to_key(TARGET)
    start_key = to_key(state_after_name)
    
    if start_key == target_key:
        return ""
    
    queue = deque()
    queue.append((state_after_name, ""))
    visited = {start_key: ""}
    
    while queue:
        cur_state, cur_serial = queue.popleft()
        if len(cur_serial) >= 11:
            continue
        for c in CHARS:
            n = ord(c) - ord('A')
            new_state = perm_n(list(cur_state), n)
            nk = to_key(new_state)
            if nk == target_key:
                return cur_serial + c
            if nk not in visited and len(cur_serial) + 1 < 11:
                visited[nk] = cur_serial + c
                queue.append((new_state, cur_serial + c))
    
    return None  # No serial found


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
