def keygen(name: str, nickname: str, age: str) -> str:
    """
    Generate a valid serial for Breaker's Crackme #3.

    Serial format:
        {nlen*nnlen*alen}-{reverse(name[1:4])}{nickname[2:4]}{nlen+nnlen+alen}-{age[1:2]}{nlen}

    Where indices are 0-based (the writeups use 1-based Mid/substring calls).
    """
    nlen  = len(name)
    nnlen = len(nickname)
    alen  = len(age)

    part1 = str(nlen * nnlen * alen)

    # Reverse of name[1..3] (0-based: characters at index 1,2,3)
    # C keygen: nlen==2 -> name[1]; nlen==3 -> name[2]+name[1]; nlen>=4 -> name[3]+name[2]+name[1]
    # Perl/tute: reverse(substr(name, 1, 3))  -- 0-based slice name[1:4] then reversed
    name_part = name[1:4][::-1]  # up to 3 chars, reversed

    # nickname[2:4]  -- 0-based: chars at index 2 and 3 (up to 2 chars)
    # C keygen: nnlen==3 -> nickname[2]; nnlen>=4 -> nickname[2]+nickname[3]
    nick_part = nickname[2:4]  # up to 2 chars

    part2 = name_part + nick_part

    part3 = str(nlen + nnlen + alen)

    # age second character (0-based index 1), only if age has >= 2 chars
    age_part = age[1:2]  # empty string if age is only 1 char long

    part4 = age_part + str(nlen)

    serial = part1 + "-" + part2 + part3 + "-" + part4
    return serial


def verify(name: str, nickname: str, age: str, serial: str) -> bool:
    """
    Verify a serial against the expected value derived from name, nickname, and age.
    Note: the crackme takes name, nickname, AND age -- not just name+serial.
    """
    expected = keygen(name, nickname, age)
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
