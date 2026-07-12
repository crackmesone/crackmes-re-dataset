def to32(x):
    return x & 0xFFFFFFFF

def to48(x):
    return x & 0xFFFFFFFFFFFF

def javaHash(s):
    h = 0
    for x in map(ord, s):
        h = h * 31 + x
    return to32(h)

class JavaRand:
    def __init__(self, seed):
        # Java Random uses signed 32-bit seed logic
        if seed >= (1 << 31):
            seed -= (1 << 32)
        self.seed = to48(seed ^ 0x5DEECE66D)

    def next(self, bits):
        self.seed = to48(self.seed * 0x5DEECE66D + 0xB)
        return to32(self.seed >> (48 - bits))

    def nextInt(self, n):
        # Power-of-two shortcut
        if (n & -n) == n:
            return to32((n * self.next(31)) >> 31)
        bits = self.next(31)
        val = bits % n
        while bits - val + (n - 1) < 0:
            bits = self.next(31)
            val = bits % n
        return val

# Static char array c.a used by the crackme
CHARS = '01234589abcdefghijklmnopqrstuvwxyz'
# Static string c.b initialised to 'LFalch'
CB = 'LFalch'

def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    seed = to32(javaHash(name) | javaHash(CB))
    r = JavaRand(seed)
    serial = ''.join(CHARS[r.nextInt(len(CHARS))] for _ in range(16))
    return serial

def verify(name: str, serial: str) -> bool:
    """Return True if serial is valid for name."""
    s = serial.lower()
    if len(s) != 16:
        return False
    expected = keygen(name)
    return s == expected


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
