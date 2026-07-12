def verify(name: str, serial: str) -> bool:
    return keygen(name).upper() == serial.upper()


def keygen(name: str) -> str:
    tbl = [0x0, 0x48, 0x65, 0x79, 0x20,
           0x43, 0x72, 0x61, 0x63, 0x6b]
    # tbl = [0, 'H', 'e', 'y', ' ', 'C', 'r', 'a', 'c', 'k']

    name_upper = name.upper()
    name_len = len(name_upper)

    if name_len == 0:
        return '0'

    # Match C types: all values treated as 32-bit unsigned (via masking)
    MASK = 0xFFFFFFFF

    ebp_10 = 0  # running sum related to char values
    ebp_14 = 0  # cumulative sum of ebp_10
    edi = 0     # main accumulator

    str_arr = [0] * 50

    for i in range(name_len):
        c = ord(name_upper[i])
        # ebp_10 += (name[i]*2 - 2)
        ebp_10 = (ebp_10 + (c * 2 - 2)) & MASK
        # str[i] = tbl[ name[i] % 10 ]
        str_arr[i] = tbl[c % 10]
        # ebp_14 += ebp_10
        ebp_14 = (ebp_14 + ebp_10) & MASK

        # inner loop: j from 0 to i (inclusive)
        for j in range(i + 1):
            edi = (edi + (str_arr[j] + c)) & MASK

    # After loops
    edi = (edi + ebp_14) & MASK
    last_char = ord(name_upper[name_len - 1])
    edi = (edi * (last_char % 10) * last_char) & MASK

    return '%X' % edi



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
