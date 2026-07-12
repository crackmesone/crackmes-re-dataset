#!/usr/bin/env python3
"""
Reverse-engineered key validation for NaSS's crackme #2.

Algorithm summary (from writeup):
1. Name must be >= 3 characters.
2. Order flag = 1 if len(name) is even, 2 if odd.
3. name_sum = sum of ord(c) for c in name, then name_sum &= 0x7FFF; if 0 then name_sum = 0x4A80
4. Serial must be exactly 7 characters, all digits '0'-'9'.
5. digit_sum = sum of int(c) for c in serial; digit_sum % 10 == 0
6. The main validation routine plays a Tic-Tac-Toe-like game:
   - There's a 10-slot buffer (indices 0-9, representing digits 0-9).
   - Two players alternate marking slots:
     * Player 1 (order flag=1): uses name_sum to pick a slot via call 0x401508 (unknown mapping)
     * Player 2 (order flag=2): uses serial digits in sequence, each digit picks a slot index
   - A slot cannot be picked twice.
   - After each move, a pattern-check routine (0x40145c) is called:
     * Returns 3 if index >= 9 (board full / exceeded)
     * Returns 0 if no winning pattern found yet
     * Returns non-zero (not 3, not 0) if a winning pattern IS found
   - Good boy: Player 2 (serial) finds a winning pattern.
   - Bad boy: board full without winner, or slot conflict, or Player 1 finds pattern (possible bug noted).

NOTE: The exact slot-selection function for Player 1 (call 0x401508) is not fully described.
We ASSUME it cycles through positions derived from name_sum.
The winning patterns (checked at 0x40145c) are not listed; we ASSUME standard tic-tac-toe
lines on a 3x3 grid mapped to digits 1-9 (like a phone keypad), with slot 0 unused.

Given these uncertainties, we implement what we can and mark assumptions.
"""

from typing import Optional, Generator

# ASSUMPTION: winning pattern lines correspond to a 3x3 tic-tac-toe grid
# where positions 1-9 map as:
#  1 2 3
#  4 5 6
#  7 8 9
WINNING_PATTERNS = [
    {1,2,3}, {4,5,6}, {7,8,9},  # rows
    {1,4,7}, {2,5,8}, {3,6,9},  # cols
    {1,5,9}, {3,5,7},            # diagonals
]

def compute_name_sum(name: str) -> int:
    """Compute the name checksum as described in the writeup."""
    s = sum(ord(c) for c in name) & 0x7FFF
    if s == 0:
        s = 0x4A80
    return s

def order_flag(name: str) -> int:
    """Order flag: 1 if len(name) even, 2 if odd."""
    # From writeup: test eax,1 -> if even -> flag=1, if odd -> flag=2
    return 1 if len(name) % 2 == 0 else 2

# ASSUMPTION: Player 1 picks slots by cycling through positions using name_sum.
# The actual function at 0x401508 is not documented; we model it as:
# it returns (name_sum + move_count) % 9 + 1, cycling through 1-9.
def player1_pick(name_sum: int, move_index: int) -> int:
    """ASSUMPTION: Player 1 picks a slot based on name_sum and current move index."""
    return (name_sum + move_index) % 9 + 1

def check_pattern(marks_p1: set, marks_p2: set, total_moves: int):
    """
    Check winning patterns.
    Returns:
        3  - exceeded 9th position (board full)
        0  - no pattern found
        1  - player1 wins
        2  - player2 wins
    """
    if total_moves > 9:
        return 3
    for pattern in WINNING_PATTERNS:
        if pattern.issubset(marks_p1):
            return 1
        if pattern.issubset(marks_p2):
            return 2
    if total_moves >= 9:
        return 3
    return 0

def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    # Check name length
    if len(name) < 3:
        return False
    # Serial must be exactly 7 digits
    if len(serial) != 7:
        return False
    if not serial.isdigit():
        return False
    # Serial digit sum must be divisible by 10
    digit_sum = sum(int(c) for c in serial)
    if digit_sum % 10 != 0:
        return False

    name_sum = compute_name_sum(name)
    flag = order_flag(name)

    # ASSUMPTION: simulate the game loop
    # Buffer: 10 slots (index 0-9), 0=empty, 1=player1, 2=player2
    board = [0] * 10
    marks_p1 = set()
    marks_p2 = set()
    total_moves = 0
    serial_idx = 0
    p1_move_count = 0

    # The loop alternates: if flag==1 player1 goes first, if flag==2 player2 goes first
    # From disassembly: loop starts by checking if flag==2; if yes, skip to player2 block
    current_flag = flag

    for _ in range(20):  # max iterations guard
        if current_flag != 2:
            # Player 1's turn
            pos = player1_pick(name_sum, p1_move_count)
            p1_move_count += 1
            if pos < 0 or pos > 9:
                return False
            if board[pos] != 0:
                return False  # slot conflict -> bad boy
            board[pos] = 1
            marks_p1.add(pos)
            total_moves += 1
            result = check_pattern(marks_p1, marks_p2, total_moves)
            if result == 3:
                return False  # board full
            if result != 0:
                # pattern found after player1 move -> bad boy (as noted, possibly a bug)
                return False
            current_flag = 2  # now player2's turn
        else:
            # Player 2's turn (serial digit)
            if serial_idx >= len(serial):
                return False
            digit = int(serial[serial_idx])
            serial_idx += 1
            if board[digit] != 0:
                return False  # slot conflict
            board[digit] = 2
            marks_p2.add(digit)
            total_moves += 1
            result = check_pattern(marks_p1, marks_p2, total_moves)
            if result == 3:
                return False  # exceeded
            if result != 0:
                # pattern found after player2 move
                if result == 2:
                    return True  # good boy: player2 wins
                else:
                    return False
            current_flag = 1  # back to player1

    return False


def keygen(name: str) -> Optional[str]:
    """
    Generate a valid serial for the given name.
    Brute-force 7-digit serials with digit_sum % 10 == 0
    that also pass the game simulation.
    """
    from itertools import product

    if len(name) < 3:
        return None

    # Serial is 7 digits, sum of digits % 10 == 0
    # We'll iterate over possible 7-digit combinations
    # To keep it tractable, fix first 6 digits and compute last
    for digits in product(range(10), repeat=6):
        s = sum(digits)
        last = (10 - (s % 10)) % 10
        serial = ''.join(map(str, digits)) + str(last)
        if verify(name, serial):
            return serial
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
