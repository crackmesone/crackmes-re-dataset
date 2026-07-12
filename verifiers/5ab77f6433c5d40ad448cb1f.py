def verify(name: str, serial: str) -> bool:
    """Check if serial is valid for the given name."""
    expected = keygen(name)
    return serial == expected


def keygen(name: str) -> str:
    """
    Generate the valid serial for the given name.

    Algorithm (from multiple writeups + C keygen):
      mn2 = 0x53  (initial accumulator)
      for i in range(len(name)):
          counter = i + 1
          tmp  = ord(name[i]) * counter          # char * (i+1)
          tmp2 = counter * 0x13                  # (i+1) * 0x13
          tmp2 = tmp2 * 2 + 0x3                  # (tmp2 << 1) + 3
          mn   = tmp * tmp2                      # tmp * tmp2
          mn2 += mn * tmp2                       # accumulate mn * tmp2

      serial = str(mn2) + '-Oc3k'

    Note: The C reference uses unsigned long (32-bit wrap-around).
    We replicate that with & 0xFFFFFFFF.
    The hard-coded serial '13028-31x23e93-z14d20' is a separate check
    not related to the name-based algorithm.
    """
    MASK = 0xFFFFFFFF
    mn2 = 0x53

    for i, ch in enumerate(name):
        counter = i + 1
        tmp = (ord(ch) * counter) & MASK
        tmp2 = (counter * 0x13) & MASK
        tmp2 = ((tmp2 * 2) + 0x3) & MASK
        mn = (tmp * tmp2) & MASK
        mn2 = (mn2 + (mn * tmp2)) & MASK

    return f"{mn2}-Oc3k"



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
