#!/usr/bin/env python3
"""
Reverse-engineered keygen for lord_phoenix Crackme #9

Algorithm (from writeup):
1. Compute CRC32 (custom poly 0xEDB88320) of name
2. Build a knight's tour on 5x5 board using Warnsdorff's rule
3. Pack moves into 3 DWORDs (moveArray[1..3])
4. moveArray[0] = random 32-bit value
5. XOR all 4 DWORDs with CRC32 of name
6. Encrypt the 4 DWORDs with SCOP cipher keyed on name
7. Serial = hex(16 bytes)

Gaps / Assumptions:
- SCOP cipher internals (init_key / encrypt / kt struct) are NOT provided in the writeup
- Warnsdorff start position is assumed to be (0,0) (top-left)
- moveArray[0] is random, so verify() cannot check it without knowing the cipher
  (the cipher presumably mixes moveArray[0] as IV or key material)
- Because the SCOP cipher is unknown, verify() and keygen() are PARTIAL stubs
"""

import struct
import random

# ---------------------------------------------------------------------------
# CRC-32 with poly 0xEDB88320 (standard reflected CRC-32)
# ---------------------------------------------------------------------------

def hash32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        c = byte
        for _ in range(8):
            d = c ^ crc
            crc = (crc >> 1) & 0x7FFFFFFF
            if d & 1:
                crc ^= 0xEDB88320
            c >>= 1
    return (~crc) & 0xFFFFFFFF

# ---------------------------------------------------------------------------
# Warnsdorff's rule knight's tour on 5x5 board
# ---------------------------------------------------------------------------

BOARD = 5
KNIGHT_MOVES = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]

def get_neighbors(x, y, visited):
    """Return unvisited neighbors reachable by knight from (x,y)."""
    result = []
    for dx, dy in KNIGHT_MOVES:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD and 0 <= ny < BOARD and not visited[nx][ny]:
            result.append((nx, ny))
    return result

def warnsdorff(start_x=0, start_y=0):
    """
    Compute a knight's tour on BOARD x BOARD starting at (start_x, start_y)
    using Warnsdorff's rule.
    Returns a list of BOARD*BOARD positions (each as 0..BOARD*BOARD-1 index).
    Returns None if no complete tour found.
    """
    visited = [[False]*BOARD for _ in range(BOARD)]
    path = []
    x, y = start_x, start_y
    visited[x][y] = True
    path.append(x * BOARD + y)
    for _ in range(BOARD * BOARD - 1):
        neighbors = get_neighbors(x, y, visited)
        if not neighbors:
            return None  # No complete tour from this start
        # Pick neighbor with fewest onward moves (Warnsdorff's rule)
        neighbors.sort(key=lambda pos: len(get_neighbors(pos[0], pos[1], visited)))
        x, y = neighbors[0]
        visited[x][y] = True
        path.append(x * BOARD + y)
    return path

def create_moves_array(rand_val=None):
    """
    Build the 4-DWORD moves array.
    moves[i] are the square indices visited at step i of the knight's tour.
    moveArray[1] packs moves[0..7] (moves[7] in high nibble)
    moveArray[2] packs moves[8..15]
    moveArray[3] packs moves[16..23]
    moveArray[0] = random 32-bit value
    """
    # ASSUMPTION: tour starts at position 0 (square 0 = top-left)
    tour = warnsdorff(0, 0)
    if tour is None:
        raise ValueError("Warnsdorff failed to produce a complete tour")
    # The tour has 25 entries; moves[0..24] = tour[0..24]
    # But moveArray uses moves[0..23] (24 moves after the start)
    # Actually the C code uses moves[0..23] packed into 3 DWORDs of 8 nibbles each
    # moves array in C is BOARD_SIZE*BOARD_SIZE - 1 = 24 entries (the moves, not positions)
    # ASSUMPTION: 'moves' in the C code are the step numbers / square indices visited
    # We'll use tour[1..24] as the 24 moves (excluding starting position)
    moves = tour[1:]  # 24 entries: steps 1..24

    move_array = [0, 0, 0, 0]
    if rand_val is None:
        rand_val = random.getrandbits(32)
    move_array[0] = rand_val & 0xFFFFFFFF

    # Pack moves: for i in 0..7: shift left 4 bits, OR moves[7-i] into moveArray[1]
    # After loop: moveArray[1] = moves[0]<<28 | moves[1]<<24 | ... | moves[7]
    # Wait, the loop does: moveArray[1] <<= 4; moveArray[1] |= moves[7 - i]  for i=0..7
    # So after i=0: val = moves[7]
    # After i=1: val = (moves[7]<<4) | moves[6]
    # ... After i=7: val = moves[7]<<28 | moves[6]<<24 | ... | moves[0]
    # ASSUMPTION: nibble order as described above
    for i in range(8):
        move_array[1] = ((move_array[1] << 4) | (moves[7 - i] & 0xF)) & 0xFFFFFFFF
        move_array[2] = ((move_array[2] << 4) | (moves[15 - i] & 0xF)) & 0xFFFFFFFF
        move_array[3] = ((move_array[3] << 4) | (moves[23 - i] & 0xF)) & 0xFFFFFFFF

    return move_array

# ---------------------------------------------------------------------------
# SCOP cipher stub (NOT available in writeup)
# ---------------------------------------------------------------------------

def scop_init_key(name: bytes):
    """
    ASSUMPTION: SCOP cipher key schedule from name.
    The actual SCOP algorithm is not provided in the writeup.
    This is a placeholder.
    """
    # ASSUMPTION: placeholder - real implementation unknown
    raise NotImplementedError("SCOP cipher (init_key/encrypt) not described in writeup")

def scop_encrypt(data_dwords, kt):
    """
    ASSUMPTION: SCOP encryption of 4 DWORDs.
    Not implemented - algorithm not in writeup.
    """
    raise NotImplementedError("SCOP cipher encrypt not described in writeup")

# ---------------------------------------------------------------------------
# Keygen
# ---------------------------------------------------------------------------

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    NOTE: Requires the SCOP cipher which is not in the writeup.
    Returns a placeholder showing what we can compute.
    """
    name_bytes = name.encode('ascii', errors='replace')
    if len(name_bytes) < 4:
        raise ValueError("Name must be at least 4 characters")

    # Step 1: CRC32 of name
    crc = hash32(name_bytes)

    # Step 2: Create moves array with random seed
    knight_ops = create_moves_array()

    # Step 3: XOR each DWORD with CRC
    for i in range(4):
        knight_ops[i] ^= crc
        knight_ops[i] &= 0xFFFFFFFF

    # Step 4: SCOP encrypt (MISSING - not in writeup)
    # ASSUMPTION: Without SCOP cipher, we cannot produce correct serial
    # kt = scop_init_key(name_bytes)
    # knight_ops = scop_encrypt(knight_ops, kt)

    # Pack to bytes (little-endian DWORDs)
    raw = struct.pack('<4I', *knight_ops)
    serial = raw.hex().upper()
    return serial  # NOTE: This is BEFORE SCOP encryption - incomplete!

def verify(name: str, serial: str) -> bool:
    """
    Verify serial for name.
    PARTIAL: Cannot fully verify without the SCOP cipher.
    We can only check structural properties.
    """
    name_bytes = name.encode('ascii', errors='replace')
    if len(name_bytes) < 4:
        return False
    if len(serial) != 32:
        return False
    # ASSUMPTION: Without SCOP decrypt, we cannot reverse-verify the serial
    # Full verification would require:
    # 1. Hex-decode serial to 16 bytes / 4 DWORDs
    # 2. SCOP decrypt with key derived from name
    # 3. XOR each DWORD with CRC32(name)
    # 4. Check that DWORDs 1,2,3 encode a valid knight's tour on 5x5
    raise NotImplementedError("Cannot verify without SCOP cipher implementation")

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


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
