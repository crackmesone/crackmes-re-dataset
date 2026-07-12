import random

# Based on the writeup by iLovro for samhjn's Lazarus CrackMe
#
# Serial structure:
#   - Exactly 64 characters long
#   - Made of 16 'commands', each 4 characters
#   - Each command is [sourcePair][destPair]
#   - Each pair is [number][letter] where:
#       number is '1', '2', or '3' (ASCII odd positions)
#       letter is 'A', 'B', or 'C' (ASCII even positions)
#
# The matrix (3x3, indexed by letter A/B/C -> 0/1/2 and number 1/2/3 -> 0/1/2):
#   Initial state:
#     row0 (number=1): [2, 0, 2]  (cols A, B, C)
#     row1 (number=2): [0, 0, 0]
#     row2 (number=3): [1, 0, 1]
#
# ASSUMPTION: The matrix is indexed as matrix[number_index][letter_index]
#   where number_index = int(char) - 1  (so '1'->0, '2'->1, '3'->2)
#   and   letter_index = ord(char) - ord('A')  (so 'A'->0, 'B'->1, 'C'->2)
#
# Each command [n1][l1][n2][l2]:
#   1st group check: matrix[n1][l1] != 0  (source must be non-zero)
#   1st group check: matrix[n2][l2] == 0  (dest must be zero)
#   3rd group (move): matrix[n2][l2] = matrix[n1][l1]
#   4th group (zero): matrix[n1][l1] = 0
#
# 2nd group check: always passes if above rules are followed (per writeup)
# ASSUMPTION: We skip the 2nd group check as the author says it always passes.
#
# Final check:
#   row0 (number=1) must equal [1, 0, 1]
#   row2 (number=3) must equal [2, 0, 2]
#   (middle row doesn't matter)
#
# Note: The crackme does NOT use the 'name' input for serial validation.
# ASSUMPTION: Serial is name-independent (pure serial check).

NUMBERS = ['1', '2', '3']
LETTERS = ['A', 'B', 'C']

def make_matrix():
    # matrix[num_idx][let_idx], num_idx: 0='1',1='2',2='3'; let_idx: 0='A',1='B',2='C'
    m = [[0]*3 for _ in range(3)]
    # Initial: row0=[2,0,2], row1=[0,0,0], row2=[1,0,1]
    m[0][0] = 2; m[0][1] = 0; m[0][2] = 2
    m[1][0] = 0; m[1][1] = 0; m[1][2] = 0
    m[2][0] = 1; m[2][1] = 0; m[2][2] = 1
    return m

def matrix_ok(m):
    # row0 must be [1,0,1], row2 must be [2,0,2]
    return (m[0][0]==1 and m[0][1]==0 and m[0][2]==1 and
            m[2][0]==2 and m[2][1]==0 and m[2][2]==2)

def apply_command(m, cmd):
    """Apply a 4-char command string to the matrix.
    Returns True if command is valid and was applied, False otherwise."""
    n1, l1, n2, l2 = cmd[0], cmd[1], cmd[2], cmd[3]
    ni1 = int(n1) - 1
    li1 = ord(l1) - ord('A')
    ni2 = int(n2) - 1
    li2 = ord(l2) - ord('A')
    # source must be non-zero, dest must be zero
    if m[ni1][li1] == 0:
        return False
    if m[ni2][li2] != 0:
        return False
    # move
    m[ni2][li2] = m[ni1][li1]
    # zero source
    m[ni1][li1] = 0
    return True

def verify(name, serial):
    """Verify a serial. Name is not used (ASSUMPTION: name-independent check)."""
    if len(serial) != 64:
        return False
    # Check character validity
    for i in range(64):
        if i % 2 == 0:  # odd position (1-indexed) = even index (0-indexed): number
            if serial[i] not in NUMBERS:
                return False
        else:  # even position (1-indexed) = odd index (0-indexed): letter
            if serial[i] not in LETTERS:
                return False
    # Process commands
    m = make_matrix()
    for i in range(16):
        cmd = serial[i*4:(i+1)*4]
        if not apply_command(m, cmd):
            return False
    return matrix_ok(m)

def get_valid_sources(m):
    """Return list of (ni, li) pairs where m[ni][li] != 0."""
    return [(ni, li) for ni in range(3) for li in range(3) if m[ni][li] != 0]

def get_valid_dests(m):
    """Return list of (ni, li) pairs where m[ni][li] == 0."""
    return [(ni, li) for ni in range(3) for li in range(3) if m[ni][li] == 0]

def pair_to_str(ni, li):
    return NUMBERS[ni] + LETTERS[li]

def keygen(name):
    """Generate a valid 64-char serial using random brute force.
    Name is not used (ASSUMPTION: name-independent)."""
    # ASSUMPTION: The non-zero cells in any intermediate matrix state
    # can always be moved to form the required final state if we pick
    # commands carefully. We use random restarts.
    random.seed()
    for attempt in range(100000):
        m = make_matrix()
        commands = []
        valid = True
        for _ in range(16):
            srcs = get_valid_sources(m)
            dsts = get_valid_dests(m)
            if not srcs or not dsts:
                valid = False
                break
            # pick random source and dest
            src = random.choice(srcs)
            dst = random.choice(dsts)
            cmd = pair_to_str(src[0], src[1]) + pair_to_str(dst[0], dst[1])
            apply_command(m, cmd)
            commands.append(cmd)
        if valid and matrix_ok(m):
            return ''.join(commands)
    # If random fails, try systematic approach
    # ASSUMPTION: A systematic solution always exists
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
