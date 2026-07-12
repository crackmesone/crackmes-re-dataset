# KhaNeTe Crackme #1 - Keygen / Verifier
# Based on KC1-K.PAS (Sphinx) and nh-khcm1.pas (nh) writeups
# Serial format: C1 + '0' + C16 + C12 + C11 + '0' + C2 + C7
# Positions 2 and 6 (0-indexed 1 and 5) are wildcards ('0' used here)

# Pascal integer division: truncation toward zero (same as Python // for positives)

def _pascal_div(a, b):
    """Pascal integer division (truncate toward zero)."""
    return int(a / b)


Add = [None,  # 1-indexed, slot 0 unused
       0x03, 0x02, 0x03, 0x05, 0x04, 0x05, 0x07, 0x0E,
       0x09, 0x09, 0x06, 0x01, 0x0D, 0x0A, 0x0A, 0x0F]


def _compute_table(name):
    """Compute the 16-entry table from the name string."""
    S = len(name)
    if S < 6:
        raise ValueError('Name must be at least 6 characters long')

    Table = [0] * 17  # 1-indexed

    # --- Step 1: forward loop (last iteration wins for all assigned slots) ---
    for i in range(1, S + 1):
        c = ord(name[i - 1])  # Pascal Name[i]
        Table[1] = c + 3
        Table[2] = c - 4
        Table[3] = c - 4
        Table[4] = c + 1
        Table[5] = c + 7
        Table[6] = c + 3
        Table[8] = c - 5
        Table[9] = c + 2

    # --- Step 2: backward loop (last iteration = first char = Name[1]) ---
    for i in range(S, 0, -1):
        c = ord(name[i - 1])  # Pascal Name[i]
        Table[7]  = c + 2
        Table[10] = c + 4
        Table[11] = c - 3
        Table[12] = c - 1
        Table[16] = Table[7] + 3
        Table[13] = c + 3
        Table[14] = c + 1
        Table[15] = (Table[14] + 1) - 3

    # After loops, effective values come from the LAST iteration:
    # Step 1 last iter = Name[S], Step 2 last iter = Name[1]

    # --- Step 3: adjustments using specific character positions ---
    # Pascal uses 1-based, S is length
    # Name[S-2] = name[S-3] in 0-based, etc.
    nS   = ord(name[S - 1])   # Name[S]
    nSm1 = ord(name[S - 2])   # Name[S-1]
    nSm2 = ord(name[S - 3])   # Name[S-2]
    nSm3 = ord(name[S - 4])   # Name[S-3]
    nSm4 = ord(name[S - 5])   # Name[S-4]
    # Name[S-5] = name[S-6]  -- only used if S>=6 guaranteed
    nSm5 = ord(name[S - 6])   # Name[S-5]
    n1   = ord(name[0])       # Name[1]

    # Table[7] update
    al = nSm1          # Name[S-1]
    dl = nSm2          # Name[S-2]
    al = al + Table[7] - dl
    Table[7] = al

    # Table[2] update
    al = nSm4          # Name[S-4]
    dl = nSm2          # Name[S-2]
    al = al + Table[2] - dl
    Table[2] = al

    # Table[11] update
    cl = nSm1          # Name[S-1]
    dl = nSm2          # Name[S-2]
    al = nSm1 + Table[7] - dl + cl
    Table[11] = al

    # Table[5] update
    dl = nSm1          # Name[S-1]
    al = nSm5 + Table[7] + dl
    Table[5] = al

    # Table[16] update
    al = nSm1          # Name[S-1]
    al = al - 1
    al = _pascal_div(al, 6)
    dl = al
    al = n1 + Table[16] + dl
    Table[16] = al

    # Table[12] update
    al = Table[16] + 3
    al = _pascal_div(al, 6)
    Table[12] = al

    # Table[10] update
    cl = nSm2          # Name[S-2]
    dl = nSm1          # Name[S-1]
    al = nSm3 + Table[16] - dl + cl
    Table[10] = al

    # Table[1] update
    dl = n1            # Name[1]
    al = nSm2 + Table[2] - dl
    Table[1] = al

    # --- Step 4: range normalization, 10 iterations ---
    for _ in range(10):
        for i in range(1, 17):
            if not (Table[i] <= 0x7A):
                Table[i] = _pascal_div(Table[i], 2)
        for i in range(1, 17):
            if not (Table[i] >= 0x41):
                Table[i] += Add[i]

    return Table


def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) < 6:
        raise ValueError('Name must be at least 6 characters long')
    Table = _compute_table(name)
    # Serial format: T[1] + '0' + T[16] + T[12] + T[11] + '0' + T[2] + T[7]
    # Positions 2 and 6 are wildcards; '0' (ASCII 48) is used here.
    serial = (chr(Table[1]) + '0' +
              chr(Table[16]) + chr(Table[12]) +
              chr(Table[11]) + '0' +
              chr(Table[2]) + chr(Table[7]))
    return serial


def verify(name, serial):
    """Verify a name/serial pair."""
    if len(name) < 6:
        return False
    if len(serial) != 8:
        return False
    try:
        Table = _compute_table(name)
    except Exception:
        return False
    # Checked positions (1-indexed serial chars, 1-indexed Table):
    # serial[1]=Table[1], serial[2]=any, serial[3]=Table[16],
    # serial[4]=Table[12], serial[5]=Table[11], serial[6]=any,
    # serial[7]=Table[2], serial[8]=Table[7]
    checks = [
        (serial[0], Table[1]),   # pos 1
        # serial[1] is wildcard
        (serial[2], Table[16]),  # pos 3
        (serial[3], Table[12]),  # pos 4
        (serial[4], Table[11]),  # pos 5
        # serial[5] is wildcard
        (serial[6], Table[2]),   # pos 7
        (serial[7], Table[7]),   # pos 8
    ]
    for char, expected in checks:
        if ord(char) != expected:
            return False
    return True



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
