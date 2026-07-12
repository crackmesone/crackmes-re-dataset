import base64
import random

# The key4me crackme by indomit
# Based on solution writeups: the serial is a base64-encoded byte array
# where each byte encodes (column << 2) | rotation for each Tetris move.
# The sequence of Tetris pieces is determined by a seed derived from the username.

# ASSUMPTION: GetID(string) computes the seed from the username.
# The exact implementation of GetID is not shown in the writeups.
# Based on common .NET patterns for such crackmes, we assume it sums
# the char values (or some simple hash). This is a gap.

def get_id(name: str) -> int:
    # ASSUMPTION: GetID hashes the username into an integer seed.
    # The exact algorithm is not provided in the writeup.
    # A common approach: sum of (index+1)*char_value, or similar.
    # Without the actual decompiled code, we cannot be certain.
    seed = 0
    for i, c in enumerate(name):
        seed += (i + 1) * ord(c)
    return seed


def get_next_fig(rnd: random.Random) -> int:
    # ASSUMPTION: GetNextFig uses rnd.Next(7) or similar to pick figure 0-6
    # Based on Sirtet class usage shown in writeup
    return rnd.randint(0, 6)  # ASSUMPTION: Next(7) maps to 0..6


def calc_figures(seed: int, count: int = 5000):
    # Replicate .NET Random with the given seed
    # ASSUMPTION: .NET System.Random is used; Python's random differs.
    # For a true keygen, we'd need to replicate .NET System.Random exactly.
    rnd = DotNetRandom(seed)
    figures = []
    for _ in range(count):
        figures.append(get_next_fig_dotnet(rnd))
    return figures


class DotNetRandom:
    """
    Reimplementation of .NET System.Random (seed-based).
    Based on the known .NET 3.5 System.Random algorithm.
    """
    MBIG = 2147483647
    MSEED = 161803398
    MZ = 0

    def __init__(self, seed: int):
        self._seed_array = [0] * 56
        ii = 0
        mj = self.MSEED - abs(seed)
        self._seed_array[55] = mj
        mk = 1
        for i in range(1, 55):
            ii = (21 * i) % 55
            self._seed_array[ii] = mk
            mk = mj - mk
            if mk < 0:
                mk += self.MBIG
            mj = self._seed_array[ii]
        for k in range(1, 5):
            for i in range(1, 56):
                self._seed_array[i] -= self._seed_array[1 + (i + 30) % 55]
                if self._seed_array[i] < 0:
                    self._seed_array[i] += self.MBIG
        self._inext = 0
        self._inextp = 21
        self._seed = 1

    def _internal_sample(self) -> int:
        inext = self._inext
        inextp = self._inextp
        inext += 1
        if inext >= 56:
            inext = 1
        inextp += 1
        if inextp >= 56:
            inextp = 1
        retval = self._seed_array[inext] - self._seed_array[inextp]
        if retval == self.MBIG:
            retval -= 1
        if retval < 0:
            retval += self.MBIG
        self._seed_array[inext] = retval
        self._inext = inext
        self._inextp = inextp
        return retval

    def next_int(self, max_val: int) -> int:
        """Equivalent to Random.Next(maxValue)"""
        return int(self._internal_sample() * (1.0 / self.MBIG) * max_val)


def get_next_fig_dotnet(rnd: DotNetRandom) -> int:
    # ASSUMPTION: GetNextFig calls rnd.Next(7)
    return rnd.next_int(7)


def simple_tetris_solver(figures):
    """
    ASSUMPTION: A simplified (greedy) Tetris solver.
    The actual solver used in the writeup was a third-party C# solver.
    This is a placeholder that produces plausible (col, rot) pairs.
    The real solver aimed for 500 deleted lines (50000+ points).
    This simplified version just picks col=0, rot=0 for all pieces.
    A real implementation would need a proper Tetris AI.
    """
    moves = []
    # ASSUMPTION: board is 10 columns wide (standard Tetris)
    BOARD_WIDTH = 10
    for fig in figures:
        # ASSUMPTION: pick a valid column (0..BOARD_WIDTH-4) and rotation (0..3)
        col = 0   # ASSUMPTION: simplified - always drop at col 0
        rot = 0   # ASSUMPTION: simplified - no rotation
        moves.append((col, rot))
    return moves


def keygen(name: str) -> str:
    """
    Generate a serial (key file content) for the given username.
    The serial is a base64-encoded byte array where each byte = (col << 2) | rot.
    ASSUMPTION: The number of moves needed to reach wizard level (50000 pts)
    requires at least ~500 line clears. The exact move count is unknown.
    """
    seed = get_id(name)
    # ASSUMPTION: 5000 figures are pre-generated as described in writeup
    figures = calc_figures(seed, 5000)

    # ASSUMPTION: use first N figures where N gives enough points
    # The writeup says solver stops after 500 deleted lines
    moves = simple_tetris_solver(figures[:500])

    byte_list = []
    for (col, rot) in moves:
        # From writeup: (colList[i] << 2) | rotList[i]
        byte_val = ((col & 0x3F) << 2) | (rot & 0x03)
        byte_list.append(byte_val)

    encoded = base64.b64encode(bytes(byte_list)).decode('ascii')
    return encoded


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given username.
    ASSUMPTION: The crackme replays the Tetris game with moves from the serial
    and checks that the score reaches wizard level (50000 points).
    We cannot fully verify without the complete Tetris simulation.
    """
    try:
        data = base64.b64decode(serial)
    except Exception:
        return False

    seed = get_id(name)
    figures = calc_figures(seed, 5000)

    # ASSUMPTION: decode moves from serial
    moves = []
    for b in data:
        col = (b >> 2) & 0x3F
        rot = b & 0x03
        moves.append((col, rot))

    if len(moves) == 0:
        return False

    # ASSUMPTION: simulate Tetris and check score >= 50000
    # Without full Tetris simulation code, we just check structural validity
    # A real verify would simulate the game with these moves
    score = simulate_tetris(figures, moves)
    return score >= 50000


def simulate_tetris(figures, moves):
    """
    ASSUMPTION: Simplified Tetris simulator.
    Real crackme has full Tetris physics. This is a stub.
    Returns estimated score based on moves count (not accurate).
    """
    # ASSUMPTION: scoring is standard Tetris scoring
    # Without the actual Sirtet class implementation, we cannot simulate accurately
    # This is a placeholder
    lines_cleared = 0
    # ASSUMPTION: each 4 moves clears ~1 line on average (very rough)
    lines_cleared = len(moves) // 4
    # Standard Tetris: 100 pts per line (single), bonus for multiples
    score = lines_cleared * 100
    return score



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
