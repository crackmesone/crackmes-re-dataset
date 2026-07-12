def verify(name: str, serial: str) -> bool:
    """
    Validates a serial against an email/name.
    Serial format: ITS-PPPP-PPPP-PPPP-PPPP  (23 chars total)
    
    Rules reconstructed from the writeup:
    1. Serial length == 23
    2. Serial starts with 'ITS-'
    3. Serial[8]  == '-'  (position 8, 0-indexed)
    4. Serial[13] == '-'
    5. Serial[18] == '-'
    6. Part1 check: sum(ord(c) - 0x30 for c in part1) == 0x10  (== 16)
    7. Part2 check: first char of part2 == 'O' (0x4F)
                   part2[0] + part2[1] + part2[2] - part2[3] == 0x8F  (== 143)
    8. Part3 check: (from pattern) sum(ord(c) - 0x30 for c in part3) == some_value
       # ASSUMPTION: Part3 check mirrors Part1 style.  The writeup was truncated;
       # we set the target to 0x10 as a placeholder.
    9. Part4 check: similar structure, target also assumed.
       # ASSUMPTION: Part4 check mirrors Part1 style with target 0x10.
    
    NOTE: The name/email is used only for format validation (must contain '@'
    and have at least 3 chars before '@').  The serial parts do NOT depend on
    the name in the visible algorithm (the writeup shows no name-derived constant).
    """
    # --- email/name basic check ---
    if '@' not in name:
        return False
    at_pos = name.index('@')
    if at_pos < 3:
        return False

    # --- serial length ---
    if len(serial) != 23:
        return False

    # --- must start with 'ITS-' ---
    if serial[:4] != 'ITS-':
        return False

    # --- dash positions ---
    if serial[8] != '-' or serial[13] != '-' or serial[18] != '-':
        return False

    part1 = serial[4:8]
    part2 = serial[9:13]
    part3 = serial[14:18]
    part4 = serial[19:23]

    # --- Part1: sum of (ord(c) - 0x30) must equal 0x10 ---
    s1 = sum(ord(c) - 0x30 for c in part1)
    if s1 != 0x10:
        return False

    # --- Part2: first char must be 'O' (0x4F) ---
    if ord(part2[0]) != 0x4F:
        return False
    # part2[0] + part2[1] + part2[2] - part2[3] == 0x8F
    val2 = ord(part2[0]) + ord(part2[1]) + ord(part2[2]) - ord(part2[3])
    if val2 != 0x8F:
        return False

    # --- Part3: writeup truncated; assuming same style as Part1 with target 0x10 ---
    # ASSUMPTION: sum(ord(c)-0x30 for c in part3) == 0x10
    s3 = sum(ord(c) - 0x30 for c in part3)
    if s3 != 0x10:
        return False

    # --- Part4: writeup truncated; assuming same style as Part1 with target 0x10 ---
    # ASSUMPTION: sum(ord(c)-0x30 for c in part4) == 0x10
    s4 = sum(ord(c) - 0x30 for c in part4)
    if s4 != 0x10:
        return False

    return True


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name/email.
    
    Strategy:
    - Part1: '5641'  -> (5+6+4+1 = 16 = 0x10)  checksum OK
    - Part2: 'O4ui'  -> O=0x4F, 0x4F+0x34+0x75-0x69 = 0x4F+0xA-0x69+0x75
             Let's verify: 79+52+117-105 = 143 = 0x8F  OK
    - Part3: '5641'  (same as Part1, satisfies assumption)
    - Part4: '5641'  (same as Part1, satisfies assumption)
    """
    if '@' not in name or name.index('@') < 3:
        raise ValueError("name must be a valid email with at least 3 chars before '@'")

    part1 = '5641'
    part2 = 'O4ui'
    part3 = '5641'  # ASSUMPTION
    part4 = '5641'  # ASSUMPTION

    serial = f'ITS-{part1}-{part2}-{part3}-{part4}'
    assert len(serial) == 23, f'length error: {len(serial)}'
    return serial



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
