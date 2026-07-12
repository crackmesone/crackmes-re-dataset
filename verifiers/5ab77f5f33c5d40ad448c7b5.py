def keygen(name: str) -> str:
    """
    Reconstructed from the decompiled .NET source:

    For each character at 1-based index i:
        append the character itself
        append str(Asc(char) * i + i)  [with a leading space from VB6 Conversion.Str]
    Then replace all spaces with '-' and uppercase.

    VB6 Conversion.Str() prefixes positive numbers with a space,
    which is why the separator ends up as '-'.
    """
    if not name:
        return ""
    expression = ""
    for i, ch in enumerate(name, start=1):
        asc_val = ord(ch)
        # Conversion.Str() in VB6 prefixes positive numbers with a space
        num_str = " " + str(asc_val * i + i)
        expression += ch + num_str
    # Replace spaces with '-' and uppercase
    serial = expression.replace(" ", "-").upper()
    return serial


def verify(name: str, serial: str) -> bool:
    return serial == keygen(name)



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
