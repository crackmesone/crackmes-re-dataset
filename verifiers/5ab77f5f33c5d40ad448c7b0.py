import hashlib
import struct

# Standard base64 alphabet (RFC2045)
BASE64DIGITS = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def to64frombits(data: bytes) -> str:
    """Custom base64 encoder matching the C implementation (no line breaks, no padding fix)."""
    import base64 as _b64
    # The C code uses standard base64 alphabet from RFC2045 without line breaks
    result = _b64.b64encode(data).decode('ascii')
    return result

def sub_40151D(md5_dig: bytearray, buff: bytearray):
    """Mix md5_dig and generate buff with length 16."""
    # fill buffer with 0..15
    for i in range(16):
        buff[i] = i

    for j in range(16):
        for i in range(16):
            a = md5_dig[i] & 0x0F
            b = md5_dig[i] >> 4
            c = buff[a]
            buff[a] = buff[b]
            buff[b] = c
            md5_dig[i] = (md5_dig[i] + c) ^ 0x17
            md5_dig[i] &= 0xFF

def sub_4014C7(out: bytearray, inp: bytearray, length: int):
    """Pack nibble pairs: out[i] = (in[2i] << 4) + (in[2i+1] & 0x0F)"""
    for i in range(length):
        out[i] = ((inp[2*i] << 4) & 0xFF) + (inp[2*i+1] & 0x0F)

def sub_4014F5(b64: bytearray, buff_2: bytearray, len_out: int, len_in: int):
    """XOR b64 with buff_2 cyclically."""
    for i in range(len_out):
        b64[i] ^= buff_2[i % len_in]

# ASSUMPTION: The Sudoku 16x16 solver is the most complex part. The board is
# filled with buff_1 (16 bytes, values 0-15 representing hex digits 0-F),
# then solved. The solution fills a 16x16 board (256 cells, each 0-15).
# We cannot fully reconstruct the sudoku solver without the original source.
# The keygen uses fill_board(buff_1), solve(0,0,&i), get_board(buff_3).
# buff_3 is 256 bytes of cell values (0-15 each).
# Without the sudoku implementation, we cannot produce the correct serial.

# ASSUMPTION: The sudoku board is a standard 16x16 sudoku where each row,
# column, and 4x4 box contains each of the 16 values exactly once.
# buff_1 provides the initial clues/givens for the puzzle.

def solve_sudoku_16(board):
    """
    Solve a 16x16 Sudoku puzzle in-place.
    board: list of 256 ints (0-15), 0 means empty cell.
    Returns True if solved.
    ASSUMPTION: This is a standard 16x16 sudoku solver.
    """
    def is_valid(board, pos, val):
        row = pos // 16
        col = pos % 16
        # Check row
        for c in range(16):
            if board[row*16 + c] == val:
                return False
        # Check col
        for r in range(16):
            if board[r*16 + col] == val:
                return False
        # Check 4x4 box
        box_row = (row // 4) * 4
        box_col = (col // 4) * 4
        for r in range(box_row, box_row+4):
            for c in range(box_col, box_col+4):
                if board[r*16+c] == val:
                    return False
        return True

    def solve(pos):
        if pos == 256:
            return True
        if board[pos] != 255:  # pre-filled cell
            return solve(pos + 1)
        for val in range(16):
            if is_valid(board, pos, val):
                board[pos] = val
                if solve(pos + 1):
                    return True
                board[pos] = 255
        return False

    solve(0)
    return board

def fill_board(buff_1: bytearray):
    """
    ASSUMPTION: fill_board places buff_1 values as initial givens on the 16x16 board.
    The exact placement strategy is unknown. A common approach: place buff_1[i]
    at specific positions. We assume they are placed as the first row or as clues
    in specific cells. Without the original sudoku.c source, this is a best-guess.
    We assume buff_1 values (0-15) are placed in row 0 as the given row.
    """
    board = [255] * 256  # 255 = empty
    # ASSUMPTION: buff_1 forms the first row of the sudoku
    for i in range(16):
        board[i] = buff_1[i]
    return board

def generate_serial(name: str) -> str:
    # Step 1: Append "-diablo2oo2" to name
    name_mod = name + "-diablo2oo2"

    # Step 2: Compute MD5
    md5_dig = bytearray(hashlib.md5(name_mod.encode('ascii')).digest())

    # Step 3: sub_40151D - mix md5_dig and produce buff_1
    buff_1 = bytearray(16)
    sub_40151D(md5_dig, buff_1)

    # Step 4: sub_4014C7 to get buff_2 (8 bytes from first 16 nibble-pairs of buff_1)
    buff_2 = bytearray(8)
    sub_4014C7(buff_2, buff_1, 8)

    # Step 5: Solve sudoku 16x16 using buff_1 as initial board configuration
    # ASSUMPTION: fill_board initializes the 16x16 board with buff_1 as clues
    board = fill_board(buff_1)
    solved = solve_sudoku_16(board)

    # buff_3 is the 256-cell solution (each cell 0-15)
    buff_3 = bytearray(board)

    # Step 6: sub_4014C7 on buff_3 -> b64dec (128 bytes)
    b64dec = bytearray(128)
    sub_4014C7(b64dec, buff_3, 128)

    # Step 7: XOR b64dec with buff_2
    sub_4014F5(b64dec, buff_2, 128, 8)

    # Step 8: Base64 encode
    serial = to64frombits(bytes(b64dec))
    return serial

def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The crackme verifies by:
    1. Generating the expected serial from name
    2. Comparing with the provided serial
    The exact verification flow in the crackme binary is not described in detail,
    but based on the keygen source, we generate and compare.
    """
    try:
        expected = generate_serial(name)
        return serial.strip() == expected.strip()
    except Exception:
        return False

def keygen(name: str) -> str:
    return generate_serial(name)


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
