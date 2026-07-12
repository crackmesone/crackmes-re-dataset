#!/usr/bin/env python3
"""
KeygenMe #1 by chaak
Solution reconstructed from the writeup by waganono.

Serial format: CKGM1XY-ABABABAB-ABABABAB-ABABABAB-ABABABAB
where:
  X = first char of P1 (must be in CHARSET1)
  Y = second char of P1 (must be in CHARSET2)
  P2-P5 = 8 chars each, alternating CHARSET1/CHARSET2 chars

The charsets are rotated based on positions of X and Y in the original charsets.
The 32 chars of P2-P5 encode 16 (x,y) moves through a 13x13 labyrinth.
Each pair of chars (odd-indexed in CHARSET1, even-indexed in CHARSET2) gives (col, row) in the maze.
The path must be valid (no walls, each step adjacent to the previous).
"""

CHARSET1_ORIG = "ACEGIKMOQSUWY"
CHARSET2_ORIG = "BDFHYLNPRTVXZ"

# 13x13 labyrinth map, row-major
# map[row][col] == 1 means passable, 0 means wall
MAZE = [
    [1,1,1,1,1,0,1,1,1,1,1,1,1],
    [1,1,0,0,1,1,1,0,0,0,0,1,1],
    [0,1,1,1,1,0,1,1,1,1,1,1,1],
    [1,1,0,0,1,1,1,1,0,1,1,1,1],
    [1,1,0,0,1,0,1,0,0,1,1,1,1],
    [1,1,1,1,1,1,1,0,0,1,1,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,1,0,1,1,1,1,0,0,0,1,1,1],
    [1,1,1,1,0,0,1,1,1,1,1,0,1],
    [1,0,1,1,1,1,1,1,0,1,1,1,1],
    [1,0,1,0,0,0,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,0,1,1,0],
    [1,1,1,1,1,1,1,0,0,0,0,1,1],
]


def rotate_charset(charset, start_pos):
    """Left-rotate charset so that it starts at start_pos."""
    n = len(charset)
    result = []
    for i in range(n):
        result.append(charset[(start_pos + i) % n])
    return ''.join(result)


def get_pos(charset, ch):
    """Return index of ch in charset, or -1 if not found."""
    try:
        return charset.index(ch)
    except ValueError:
        return -1


def is_wall(col, row):
    """Return True if position (col, row) is a wall (0)."""
    if row < 0 or row >= 13 or col < 0 or col >= 13:
        return True
    return MAZE[row][col] == 0


def is_valid_move(prev_col, prev_row, new_col, new_row):
    """
    Check if moving from (prev_col, prev_row) to (new_col, new_row) is valid.
    From writeup: 2nd procedure sub_401588 checks adjacency.
    Initial position is (-1, -1) meaning 'start'.
    When prev is (-1,-1), any non-wall cell is reachable (first move).
    Otherwise, must be adjacent (Manhattan distance == 1).
    # ASSUMPTION: adjacency means Manhattan distance of exactly 1 (no diagonal)
    """
    if prev_col == -1 and prev_row == -1:
        return True
    # ASSUMPTION: valid move = exactly 1 step in a cardinal direction
    dist = abs(new_col - prev_col) + abs(new_row - prev_row)
    return dist == 1


def verify(name, serial):
    """
    Verify a serial for the given name.
    Note: the name does not appear to factor into the serial check
    based on the writeup (no name-based computation shown).
    # ASSUMPTION: name is not used in serial validation
    """
    # Remove dashes and parse
    parts = serial.split('-')
    if len(parts) != 5:
        return False

    p1, p2, p3, p4, p5 = parts

    # P1 must be exactly 2 chars (CKGM1 prefix stripped by sscanf %2s)
    # The format is CKGM1XY-... so P1 from sscanf is the 2 chars after CKGM1
    # We need to handle the full serial string
    if not serial.startswith('CKGM1'):
        return False

    # Re-parse: CKGM1 + 2 chars, then 4 groups of 8
    body = serial[5:]  # strip 'CKGM1'
    body_parts = body.split('-')
    if len(body_parts) != 5:
        return False

    p1_str = body_parts[0]  # 2 chars
    if len(p1_str) != 2:
        return False
    for bp in body_parts[1:]:
        if len(bp) != 8:
            return False

    x_char = p1_str[0]  # must be in CHARSET1
    y_char = p1_str[1]  # must be in CHARSET2

    if get_pos(CHARSET1_ORIG, x_char) == -1:
        return False
    if get_pos(CHARSET2_ORIG, y_char) == -1:
        return False

    # Build rotated charsets
    x_pos = get_pos(CHARSET1_ORIG, x_char)
    y_pos = get_pos(CHARSET2_ORIG, y_char)

    charset1 = rotate_charset(CHARSET1_ORIG, x_pos)
    charset2 = rotate_charset(CHARSET2_ORIG, y_pos)

    # Collect 32 chars from P2-P5
    all_chars = ''.join(body_parts[1:])
    if len(all_chars) != 32:
        return False

    # Check alternating charset membership
    for i, ch in enumerate(all_chars):
        if i % 2 == 0:
            # must be in charset1
            if get_pos(charset1, ch) == -1:
                return False
        else:
            # must be in charset2
            if get_pos(charset2, ch) == -1:
                return False

    # Check labyrinth path: 16 moves
    # Each pair: all_chars[2*i] -> col (index in charset1)
    #             all_chars[2*i+1] -> row (index in charset2)
    cur_col = -1
    cur_row = -1

    for i in range(16):
        col_char = all_chars[2 * i]
        row_char = all_chars[2 * i + 1]

        col = get_pos(charset1, col_char)
        row = get_pos(charset2, row_char)

        if is_wall(col, row):
            return False
        if not is_valid_move(cur_col, cur_row, col, row):
            return False

        cur_col = col
        cur_row = row

    return True


def keygen(name):
    """
    Generate a valid serial for the given name.
    # ASSUMPTION: name does not affect serial; we just generate any valid serial.
    Strategy:
      1. Pick X from CHARSET1, Y from CHARSET2
      2. Build rotated charsets
      3. BFS/DFS for a 16-step path in the maze
      4. Encode path as serial
    """
    from collections import deque

    def encode_path(x_char, y_char, path):
        charset1 = rotate_charset(CHARSET1_ORIG, get_pos(CHARSET1_ORIG, x_char))
        charset2 = rotate_charset(CHARSET2_ORIG, get_pos(CHARSET2_ORIG, y_char))
        chars = []
        for (col, row) in path:
            chars.append(charset1[col])
            chars.append(charset2[row])
        serial_body = ''.join(chars)
        # Split into 4 groups of 8
        groups = [serial_body[i:i+8] for i in range(0, 32, 8)]
        return 'CKGM1{}{}-{}'.format(x_char, y_char, '-'.join(groups))

    # BFS to find a path of exactly 16 steps
    # State: (col, row, path_tuple)
    x_char = CHARSET1_ORIG[0]  # 'A'
    y_char = CHARSET2_ORIG[0]  # 'B'

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    # Find all passable starting cells
    starts = []
    for r in range(13):
        for c in range(13):
            if not is_wall(c, r):
                starts.append((c, r))

    # DFS with depth limit of 16
    def dfs(col, row, path, depth):
        if depth == 16:
            return path[:]
        for dc, dr in directions:
            nc, nr = col + dc, row + dr
            if not is_wall(nc, nr):
                path.append((nc, nr))
                result = dfs(nc, nr, path, depth + 1)
                if result is not None:
                    return result
                path.pop()
        return None

    for start_col, start_row in starts:
        path = [(start_col, start_row)]
        result = dfs(start_col, start_row, path, 1)
        if result is not None:
            serial = encode_path(x_char, y_char, result)
            return serial

    # ASSUMPTION: if no path found (shouldn't happen), return None
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
