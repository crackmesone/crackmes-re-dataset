# Reconstruction of the 'lost' crackme by warrantyvoider
# Based on the keygen source (gene.asm + keygen.c)

# ---- RNG & maze generator (from gene.asm) ----

MASK32 = 0xFFFFFFFF

class MazeGen:
    def __init__(self, seed1, seed2):
        self.seed1 = seed1 & MASK32
        self.seed2 = seed2 & MASK32
        self.side_len = 0
        self.x_start = 0
        self.y_start = 0
        self.x_finish = 0
        self.y_finish = 0
        self.maze = None

    def get_block(self, n):
        # seed1 = (seed1 * 0x5DC1) % 0x560B
        self.seed1 = (self.seed1 * 0x5DC1) % 0x560B
        # seed2 = (seed2 * 0x549D) % 0x51A1
        self.seed2 = (self.seed2 * 0x549D) % 0x51A1
        val = (self.seed1 + self.seed2) & MASK32
        return val % n

    def generate(self):
        # side_len = get_block(20) + 20
        self.side_len = self.get_block(20) + 20
        sz = self.side_len * self.side_len
        self.maze = bytearray(sz)

        for i in range(sz):
            v = self.get_block(4)
            if v == 0:
                self.maze[i] = ord('#')  # WALL
            else:
                self.maze[i] = ord(' ')  # FLOOR

        self.x_start = self.get_block(self.side_len)
        self.y_start = self.get_block(self.side_len)

        # x_finish must differ from x_start
        while True:
            self.x_finish = self.get_block(self.side_len)
            if self.x_finish != self.x_start:
                break

        # y_finish must differ from y_start
        while True:
            self.y_finish = self.get_block(self.side_len)
            if self.y_finish != self.y_start:
                break

        # Place 's' at start, 'f' at finish
        self.maze[self.x_start * self.side_len + self.y_start] = ord('s')
        self.maze[self.x_finish * self.side_len + self.y_finish] = ord('f')


# ---- init: name bytes used as seeds (from gene.asm _init) ----
# init receives a pointer to name; reads first 4 bytes as seed1, next 4 as seed2

def init_seeds(name: str):
    # name is 5-8 chars; pad to 8 bytes with zeros
    nb = name.encode('latin-1')
    nb = nb + b'\x00' * 8
    seed1 = int.from_bytes(nb[0:4], 'little')
    seed2 = int.from_bytes(nb[4:8], 'little')
    return seed1, seed2


# ---- Maze solver (from keygen.c solve()) ----
# Returns the serial string if solvable, else None

SMAX = 0x2000
WALL = ord('#')
FLOOR = ord(' ')
PATH = ord('*')
TRAVERSED = ord('.')


def solve_maze(mg: MazeGen):
    side = mg.side_len
    maze = bytearray(mg.maze)  # work on a copy

    fake_wall = WALL

    def maze_XY(x, y):
        if 0 <= x < side and 0 <= y < side:
            return x * side + y
        return None  # out of bounds => wall

    def get_cell(x, y):
        idx = maze_XY(x, y)
        if idx is None:
            return fake_wall
        return maze[idx]

    def set_cell(x, y, v):
        idx = maze_XY(x, y)
        if idx is not None:
            maze[idx] = v

    # Set finish to FLOOR so we can step on it
    set_cell(mg.x_finish, mg.y_finish, FLOOR)

    stack = []
    x = mg.x_start
    y = mg.y_start
    serial_chars = {}
    solved = False

    stack.append(x)
    stack.append(y)
    sptr = len(stack)

    while not solved and sptr > 0:
        if x == mg.x_finish and y == mg.y_finish:
            # serial[sptr/2 - 1] = 0 (null terminator)
            # The serial is built up to index sptr//2 - 1
            solved = True
            break

        set_cell(x, y, PATH)

        if get_cell(x - 1, y) == FLOOR:  # left
            serial_chars[sptr // 2 - 1] = 'l'
            set_cell(x, y, PATH)
            stack.append(x)
            stack.append(y)
            sptr = len(stack)
            x = x - 1
        elif get_cell(x + 1, y) == FLOOR:  # right
            serial_chars[sptr // 2 - 1] = 'r'
            set_cell(x, y, PATH)
            stack.append(x)
            stack.append(y)
            sptr = len(stack)
            x = x + 1
        elif get_cell(x, y + 1) == FLOOR:  # down
            serial_chars[sptr // 2 - 1] = 'd'
            set_cell(x, y, PATH)
            stack.append(x)
            stack.append(y)
            sptr = len(stack)
            y = y + 1
        elif get_cell(x, y - 1) == FLOOR:  # up
            serial_chars[sptr // 2 - 1] = 'u'
            set_cell(x, y, PATH)
            stack.append(x)
            stack.append(y)
            sptr = len(stack)
            y = y - 1
        else:  # dead end
            set_cell(x, y, TRAVERSED)
            if len(stack) < 2:
                break
            y = stack.pop()
            x = stack.pop()
            sptr = len(stack)

    if not solved:
        return None

    # Build serial string: indices 0 .. sptr//2 - 2 (last is null terminator = 0)
    # sptr at solved moment: collect all non-zero entries up to max key
    if not serial_chars:
        return ''
    max_idx = max(serial_chars.keys())
    result = []
    for i in range(max_idx):
        result.append(serial_chars.get(i, ''))
    return ''.join(result)


# ---- verify & keygen ----

def keygen(name: str):
    """Generate serial for a given name (5-8 chars)."""
    if len(name) < 5 or len(name) > 8:
        return None
    s1, s2 = init_seeds(name)
    mg = MazeGen(s1, s2)
    mg.generate()
    serial = solve_maze(mg)
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify that serial is the correct maze solution for the given name."""
    if len(name) < 5 or len(name) > 8:
        return False
    expected = keygen(name)
    if expected is None:
        return False
    return serial == expected



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
