# Keygen for 'strange_keygenme' by dolem
# Algorithm recovered from the C# keygen source by Zephy
#
# The serial is determined solely by the ASCII value of the first character
# of the name, modulo 10, used as an index into a fixed lookup table.

DATA = [
    "FJJG-NHKK-JJIH-GGGH",  # index 0
    "CJJG-NEKK-JEIH-HGHH",  # index 1
    "JJJG-NLKK-JJIH-IGIH",  # index 2
    "GJJG-NIKK-JEIH-JGJH",  # index 3
    "DJJG-NFKK-JJIH-AGKH",  # index 4
    "AJJG-NCKK-JEIH-BGBH",  # index 5
    "HJJG-NJKK-JJIH-CGCH",  # index 6
    "EJJG-NGKK-JEIH-DGDH",  # index 7
    "BJJG-NDKK-JJIH-EGEH",  # index 8
    "IJJG-NKKK-JEIH-FGFH",  # index 9
]


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if len(name) < 1:
        return ""
    index = ord(name[0]) % 10
    return DATA[index]


def verify(name: str, serial: str) -> bool:
    """Return True if serial is the correct serial for name."""
    expected = keygen(name)
    if not expected:
        return False
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
