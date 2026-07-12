import itertools
import string

def verify(name: str, serial: str) -> bool:
    """
    The 'name' parameter is not used in this crackme.
    Validation is purely on the serial/password:
      1. Length must be a multiple of 4.
      2. Every 4-character block must be a palindrome
         (i.e., block[0]==block[3] and block[1]==block[2]).
    """
    if len(serial) == 0:
        return False
    if len(serial) % 4 != 0:
        return False
    for i in range(0, len(serial), 4):
        block = serial[i:i+4]
        if block[0] != block[3]:
            return False
        if block[1] != block[2]:
            return False
    return True

def _palindrome4_generator():
    """Yield every 4-character palindrome from printable non-space ASCII."""
    printable = [chr(c) for c in range(0x21, 0x7f)]
    for a, b in itertools.product(printable, repeat=2):
        yield a + b + b + a

def keygen(name: str, block_count: int = 1) -> str:
    """
    Generate a valid serial made of `block_count` 4-character palindrome blocks.
    The name parameter is not used by the algorithm.
    Returns the first valid serial of the given block length.
    """
    if block_count < 1:
        block_count = 1
    gen = _palindrome4_generator()
    blocks = [next(gen) for _ in range(block_count)]
    return ''.join(blocks)

def keygen_all(name: str, block_count: int = 1):
    """
    Generator that yields every valid serial of exactly block_count*4 characters.
    """
    if block_count < 1:
        block_count = 1
    for combo in itertools.product(_palindrome4_generator(), repeat=block_count):
        yield ''.join(combo)


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
