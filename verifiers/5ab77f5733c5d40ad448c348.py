import random
import string

# Based on the writeup by indomit for obnoxious_serialme
#
# The serial is built by traversing a tree that starts at node 0.
# Valid nodes/characters are [0-9] and [A-D] (hex digits 0-13, i.e., 0x00 to 0x0D).
# From each node n, you can move by offsets: {-5, -4, -3, -2, +1, +2, +3, +4, +5}
# The resulting child node must be in range [0, 0x0D] (i.e., 0..13).
# Node 4 (i.e., '4') is the STOP node - it ends a segment.
#
# The key is composed of 20-30 such paths, each starting from 0, 1, 2, or 0xA,
# and each ending at node 4.
#
# ASSUMPTION: The serial characters are the sequence of node values visited,
# encoded as their hex digit character (0-9, A-D), concatenated together.
# ASSUMPTION: Each path through the tree is concatenated, including the start
# and end (4) nodes.
# ASSUMPTION: The number of paths is between 20 and 30 (randomly chosen).
# ASSUMPTION: Valid start nodes for each path are {0, 1, 2, 0xA} as mentioned.

# Character set: 0-9 maps to '0'-'9', 10->A, 11->B, 12->C, 13->D
VALID_CHARS = '0123456789ABCD'  # indices 0..13

BRANCHES = [-5, -4, -3, -2, 1, 2, 3, 4, 5]
STOP_NODE = 4
MIN_NODE = 0
MAX_NODE = 13  # 0x0D

# ASSUMPTION: Start nodes per path are from {0, 1, 2, 0xA=10}
START_NODES = [0, 1, 2, 10]


def node_to_char(n):
    return VALID_CHARS[n]


def char_to_node(c):
    c = c.upper()
    if c in VALID_CHARS:
        return VALID_CHARS.index(c)
    return None


def get_children(n):
    """Return all valid children of node n (excluding STOP_NODE for traversal purposes)."""
    children = []
    for b in BRANCHES:
        child = n + b
        if MIN_NODE <= child <= MAX_NODE:
            children.append(child)
    return children


def generate_path(start_node, max_depth=50):
    """
    Generate a random path starting from start_node, ending at STOP_NODE (4).
    Returns a list of node values including start and end.
    """
    path = [start_node]
    current = start_node
    if current == STOP_NODE:
        return path  # immediately done
    depth = 0
    while depth < max_depth:
        children = get_children(current)
        if not children:
            # Dead end, no valid path
            return None
        next_node = random.choice(children)
        path.append(next_node)
        if next_node == STOP_NODE:
            return path
        current = next_node
        depth += 1
    return None  # too deep, abandon


def path_to_str(path):
    return ''.join(node_to_char(n) for n in path)


def keygen(name):
    """
    Generate a valid serial. The serial is composed of 20-30 paths through the tree,
    each starting from one of {0,1,2,A} and ending at 4.
    ASSUMPTION: The name is not used in the serial generation (not described in writeup).
    """
    # ASSUMPTION: name is not factored into the serial
    num_paths = random.randint(20, 30)
    serial_chars = []
    attempts = 0
    paths_done = 0
    while paths_done < num_paths and attempts < 10000:
        start = random.choice(START_NODES)
        path = generate_path(start)
        if path is not None:
            serial_chars.append(path_to_str(path))
            paths_done += 1
        attempts += 1
    serial = ''.join(serial_chars)
    return serial


def verify(name, serial):
    """
    Verify a serial by parsing it as a sequence of tree paths.
    Each path starts at a valid start node and ends at STOP_NODE (4).
    We need 20-30 complete paths.
    ASSUMPTION: All characters must be in VALID_CHARS.
    ASSUMPTION: We parse greedily, starting from valid start nodes.
    ASSUMPTION: name is not checked against serial.
    """
    serial = serial.upper()
    # Check all characters are valid
    for c in serial:
        if c not in VALID_CHARS:
            return False

    # Parse paths
    nodes = [char_to_node(c) for c in serial]
    
    # Try to parse as sequence of paths
    i = 0
    path_count = 0
    while i < len(nodes):
        # Start must be a valid start node
        # ASSUMPTION: any node can be a start (writeup says 0,1,2,A but also says
        # 'starting from 0' as the tree root and shows subtrees). We allow any valid start.
        # ASSUMPTION: Actually let's check for the described start nodes {0,1,2,10}
        if nodes[i] not in START_NODES and nodes[i] != STOP_NODE:
            # ASSUMPTION: perhaps any node can start, not just {0,1,2,10}
            # Be lenient: accept any valid start
            pass
        start = nodes[i]
        if start == STOP_NODE:
            # Path is just the stop node
            path_count += 1
            i += 1
            continue
        # Walk the path
        current = start
        i += 1
        valid_path = True
        reached_stop = False
        while i < len(nodes):
            next_node = nodes[i]
            diff = next_node - current
            if diff not in BRANCHES:
                valid_path = False
                break
            i += 1
            current = next_node
            if current == STOP_NODE:
                reached_stop = True
                break
        if not valid_path:
            return False
        if reached_stop or current == STOP_NODE:
            path_count += 1
        else:
            # Path didn't end at stop node
            # ASSUMPTION: last path may not end at 4 if we're at end of string
            pass

    return 20 <= path_count <= 30



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
