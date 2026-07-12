# PacMe by kwazy_webbit - Key/Serial Validation Algorithm
# This is a KEYFILE-based crackme. The 'serial' here is the content of the keyfile.
#
# Algorithm Summary (from solution writeups):
# 1. A keyfile named 'PACME!.data' (or similar) must exist.
# 2. The program reads the first byte of the keyfile; if zero, it reads more.
# 3. It reads 18 (0x12) bytes from the keyfile as the 'pathway' (encoded moves).
# 4. It XORs each of those 18 bytes with a value derived from the user's name.
# 5. The XOR value = sum of ASCII values of name characters (mod 256).
# 6. Each XOR'd byte encodes 4 moves (2 bits each): 0=up, 1=right, 2=down, 3=left.
# 7. The moves must navigate a 'C' through a 16-wide maze from start to 'X' without hitting '*'.
# 8. The maze is hardcoded in the binary; we don't have it here.
#
# The maze layout is NOT provided in the writeups, so we cannot fully implement verify().
# We can implement the XOR encoding/decoding and the move extraction.

# ASSUMPTION: The keyfile name is 'PACME!.data' based on the writeup references.
KEYFILE_NAME = 'PACME!.data'

# ASSUMPTION: The maze is 16 columns wide (stride=0x10 as seen in make_move).
# ASSUMPTION: The correct sequence of moves (as 2-bit pairs) through the maze
# is not provided; we mark it as unknown.
# The maze data from the writeup hint (the 'Vindalooo' song bytes):
# 00000000: 56 9D 6F 64 2D 61 6C 6F 6F 2D 6F 6F 2D ... 'Vindalooo'
# But those are the ENCODED bytes; actual moves come after XOR with name-sum.

MAZE_WIDTH = 16  # 0x10

def compute_xor_value(name: str) -> int:
    """Sum all ASCII values of name characters, take low byte."""
    return sum(ord(c) for c in name) & 0xFF

def decode_pathway(encoded_bytes: bytes, xor_val: int) -> list:
    """XOR each byte of the 18-byte pathway with xor_val, then extract 2-bit moves."""
    moves = []
    for b in encoded_bytes:
        decoded = b ^ xor_val
        # Each byte encodes 4 moves, 2 bits each, LSB first
        for _ in range(4):
            moves.append(decoded & 0x03)
            decoded >>= 2
    return moves

def encode_pathway(moves: list, xor_val: int) -> bytes:
    """Encode a list of moves (4 per byte) and XOR with xor_val."""
    encoded = []
    # Pad moves to multiple of 4
    while len(moves) % 4 != 0:
        moves = moves + [0]
    for i in range(0, len(moves), 4):
        byte_val = 0
        for j in range(4):
            byte_val |= (moves[i + j] & 0x03) << (j * 2)
        encoded.append(byte_val ^ xor_val)
    return bytes(encoded)

# ASSUMPTION: The correct move sequence through the maze.
# From the tutorial writeup, for 'Cronos' (xor=0x74), the encoded bytes shown were:
# '56 9D 6F 64 2D 61 6C 6F 6F 2D 6F 6F' (partial, from the 'Vindalooo' hint)
# But this is speculative. The actual maze path is not provided.
# We mark the correct_moves as UNKNOWN.

# ASSUMPTION: correct_moves is the sequence that navigates the maze.
# 0=up(-0x10), 1=right(+1), 2=down(+0x10), 3=left(-1)
# This must be determined by analyzing the maze in the binary.
correct_moves = None  # ASSUMPTION: Unknown - requires maze analysis

def verify(name: str, serial: bytes) -> bool:
    """
    Verify a keyfile's content against a name.
    serial: raw bytes of the keyfile (at least 19 bytes: 1 header + 18 pathway)
    Returns True if valid.
    
    NOTE: Cannot fully verify without the maze layout.
    We can only check that the XOR decoding produces moves that (theoretically)
    traverse the maze correctly.
    """
    if len(serial) < 19:
        return False
    # ASSUMPTION: First byte must be non-zero (or the program checks it's zero as a null-terminator issue?)
    # From writeup: 'if zero, then EAX is zero' - the first byte check.
    # Actually the writeup says: if TEST EAX, EAX comes out as zero, then EAX is zero.
    # So first byte of the file should NOT be zero.
    # ASSUMPTION: The file starts with some header; the 18 pathway bytes start at offset 1.
    # Actually re-reading: the program reads first byte, checks if zero.
    # If zero it jumps. Let's assume the pathway is at offset 1 or 0.
    # From the assembly: it reads 1 byte first, tests it, then reads 18 bytes.
    # ASSUMPTION: offset 0 is a single indicator byte (non-zero), offset 1..18 are pathway.
    
    header_byte = serial[0]
    if header_byte == 0:
        return False  # File starts with null = bad
    
    pathway_bytes = serial[1:19]
    if len(pathway_bytes) < 18:
        return False
    
    xor_val = compute_xor_value(name)
    moves = decode_pathway(pathway_bytes, xor_val)
    
    # ASSUMPTION: We'd simulate maze traversal here, but maze layout is unknown.
    # Return True if moves could be valid (placeholder).
    # In reality, we'd need to simulate the maze.
    if correct_moves is not None:
        return moves[:len(correct_moves)] == correct_moves
    
    # Cannot verify without maze
    raise NotImplementedError("Maze layout unknown - cannot fully verify")

def keygen(name: str) -> bytes:
    """
    Generate keyfile bytes for a given name.
    
    ASSUMPTION: The correct move sequence through the maze is hardcoded here.
    This requires prior analysis of the maze in the binary.
    The move sequence below is a PLACEHOLDER and likely incorrect.
    """
    xor_val = compute_xor_value(name)
    
    # ASSUMPTION: The following move sequence is the correct maze solution.
    # Each value: 0=up, 1=right, 2=down, 3=left
    # 18 bytes = 72 moves total
    # This is a PLACEHOLDER - actual maze path is unknown without the binary.
    # From the writeup hint about 'BoomBox' being the keyfile content before encoding:
    # 'BoomBox' = 42 6F 6F 6D 42 6F 78 (7 bytes, not 18)
    # And 'BoomBox12345678' padded to 18 bytes is also speculative.
    # ASSUMPTION: placeholder moves (all right = 1)
    placeholder_moves = [1] * 72  # 18 bytes * 4 moves/byte
    
    pathway_encoded = encode_pathway(placeholder_moves, xor_val)
    
    # Build keyfile: 1 header byte + 18 pathway bytes
    # ASSUMPTION: header byte is 0x56 ('V') or any non-zero value
    header = bytes([0x56])
    
    return header + pathway_encoded


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
