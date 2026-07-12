# ASSUMPTION: The writeup is largely garbled/encoded text (appears to be UTF-16LE or similar encoding issue).
# The C keygen snippet (FINAL.C) is the clearest description of the algorithm.
# We reconstruct from FINAL.C, with notes on gaps.

# From FINAL.C:
# ch[] = 'nOuKeYs NoM!RyT$*thEp@(/_[S&"ar.=]%'
# The '.' at some index i is replaced with chr(183)
# The 'magic' character is used as an index into ch[]
# Name must be 8 chars long, third letter (index 2) must be 'x'
# magic_off = index of magic char in ch[] + 1
# serial[0] = ch[magic_off - 5]
# serial[1] = name[7]
# serial[2] = magic
# serial[3] = ch[magic_off + 2]
# serial[4] = name[1]
# serial[5] = magic
# serial[6] = name[4]
# serial[7] = magic
# serial[8] = magic
# serial[9] = magic  (but serial has only 9 slots 0..8 in C, serial[9] is overflow - ASSUMPTION: ignore)
# serial[magic_off % 9] = ch[magic_off + 3]  (overwrites one of the above)
# The serial printed is indices 0..9 (10 chars)

# ASSUMPTION: The actual Delphi crackme may differ from this C keygen writeup.
# ASSUMPTION: serial length is 10 (indices 0-9), serial[9] = magic (from loop assignment),
#             then serial[magic_off%9] is overwritten with ch[magic_off+3]

def _build_ch():
    ch = list('nOuKeYs NoM!RyT$*thEp@(/_[S&"ar.=]%')
    # Find '.' and replace with chr(183)
    for i, c in enumerate(ch):
        if c == '.':
            ch[i] = chr(183)
            break
    return ch

def _find_magic_off(ch, magic):
    # Find index of magic in ch, then magic_off = that index + 1
    for i, c in enumerate(ch):
        if c == magic:
            return i + 1
    return None

def verify(name: str, serial: str) -> bool:
    # ASSUMPTION: name must be exactly 8 chars, name[2] == 'x'
    if len(name) != 8:
        return False
    if name[2] != 'x':
        return False
    ch = _build_ch()
    # We need to know the magic character - but the verify function doesn't take it as input.
    # ASSUMPTION: We try all possible magic characters from ch[] and see if any produces the serial.
    for magic_idx in range(len(ch)):
        magic = ch[magic_idx]
        magic_off = magic_idx + 1
        # bounds check
        if magic_off - 5 < 0 or magic_off + 3 >= len(ch):
            continue
        # Build serial of length 10 (indices 0..9)
        s = [''] * 10
        s[0] = ch[magic_off - 5]
        s[1] = name[7]
        s[2] = magic
        s[3] = ch[magic_off + 2]
        s[4] = name[1]
        s[5] = magic
        s[6] = name[4]
        s[7] = magic
        s[8] = magic
        s[9] = magic
        # overwrite
        mod = magic_off % 9
        s[mod] = ch[magic_off + 3]
        candidate = ''.join(s)
        if candidate == serial:
            return True
    return False

def keygen(name: str) -> str:
    # ASSUMPTION: name must be exactly 8 chars, name[2] == 'x'
    if len(name) != 8 or name[2] != 'x':
        raise ValueError("Name must be 8 chars and third char must be 'x'")
    ch = _build_ch()
    # Pick a magic character - try first valid one
    for magic_idx in range(len(ch)):
        magic = ch[magic_idx]
        magic_off = magic_idx + 1
        if magic_off - 5 < 0 or magic_off + 3 >= len(ch):
            continue
        s = [''] * 10
        s[0] = ch[magic_off - 5]
        s[1] = name[7]
        s[2] = magic
        s[3] = ch[magic_off + 2]
        s[4] = name[1]
        s[5] = magic
        s[6] = name[4]
        s[7] = magic
        s[8] = magic
        s[9] = magic
        mod = magic_off % 9
        s[mod] = ch[magic_off + 3]
        return ''.join(s)
    raise ValueError("No valid magic character found")


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
