def _transform(name, add_length_of):
    """
    Add `add_length_of` (an integer) to each character's ordinal value,
    then apply alternating case: even indices -> lowercase, odd indices -> uppercase.
    """
    result = []
    for i, ch in enumerate(name):
        new_ord = ord(ch) + add_length_of
        new_ch = chr(new_ord)
        if i % 2 == 0:
            new_ch = new_ch.lower()
        else:
            new_ch = new_ch.upper()
        result.append(new_ch)
    return ''.join(result)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Algorithm (from the write-up):
      part1: name reversed, then each char's ordinal += len(name),
             alternating case (even=lower, odd=upper)
      part2: name in normal order, each char's ordinal += 3  (len of 'abd'),
             alternating case (even=lower, odd=upper)
      serial = part1 + '-' + part2
    """
    if not name:
        return ''

    name_len = len(name)

    # Part 1: reverse name, add len(name) to each char
    reversed_name = name[::-1]
    part1 = _transform(reversed_name, name_len)

    # Part 2: normal name, add 3 (len of 'abd') to each char
    # ASSUMPTION: the constant 3 comes from len('abd') as stated in the write-up
    part2 = _transform(name, 3)

    return part1 + '-' + part2


def verify(name: str, serial: str) -> bool:
    """
    Verify whether the given serial is valid for the given name.

    Checks:
      1. Serial must contain exactly one '-' separator.
      2. Both halves must have the same length as the name.
      3. part1 matches transform(reversed(name), len(name)) with alternating case.
      4. part2 matches transform(name, 3) with alternating case.
    """
    if '-' not in serial:
        return False

    parts = serial.split('-')
    if len(parts) != 2:
        return False

    part1, part2 = parts
    expected = keygen(name)

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
