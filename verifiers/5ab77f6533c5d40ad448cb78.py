import random
import string

# Valid key lengths for sub_121109 path: odd AND not divisible by 5
# i.e., length in {1, 3, 7, 9, 11, 13, ...} (odd, not multiple of 5)
# Valid key length for sub_1211AB path: exactly 32 (all digits)
VALID_LENGTHS_109 = [l for l in range(1, 64) if (l % 2 == 1) and (l % 5 != 0)]
VALID_LENGTHS_32 = [32]

PRINTABLES = [chr(c) for c in range(0x21, 0x7F)]  # printable non-space ASCII
DIGITS = list('0123456789')


def sub_121109(serial: str) -> bool:
    """
    Returns True (==1) if:
      1. len(serial) is odd AND len(serial) % 5 != 0
      2. sum of ASCII values - 5 <= 500  (initial accumulator is -5)
      3. serial[0] == serial[len-1]  (first char == last char)
    """
    n = len(serial)
    if n == 0:
        return False
    # length must be odd
    if not (n & 1):
        return False
    # length must not be divisible by 5
    if n % 5 == 0:
        return False
    # compute sum starting at -5
    s = -5
    for ch in serial:
        s += ord(ch)
    if s > 500:
        return False
    # first char must equal last char
    if serial[0] != serial[-1]:
        return False
    return True


def sub_1211AB(serial: str) -> bool:
    """
    Returns True (==1) if:
      1. len(serial) == 32
      2. All 32 chars are digits
      3. s1 = sum of digits[0..14] >= 10
      4. s2 = sum of digits[15..29] >= 10
      5. serial[31] == '0'
      6. int(serial[30]) == s2 % s1
    """
    if len(serial) != 32:
        return False
    for ch in serial:
        if not ch.isdigit():
            return False
    s1 = sum(int(serial[i]) for i in range(0, 15))
    s2 = sum(int(serial[i]) for i in range(15, 30))
    if s1 < 10:
        return False
    if s2 < 10:
        return False
    if serial[31] != '0':
        return False
    if int(serial[30]) != s2 % s1:
        return False
    return True


def verify(name: str, serial: str) -> bool:
    """
    The crackme does NOT use the name in validation.
    A serial is valid if sub_121109(serial)==1 XOR sub_1211AB(serial)==1,
    i.e., exactly one of them returns 1 (sum of return values & 1 == 1).
    # ASSUMPTION: the check is (sub_121109 + sub_1211AB) & 1 == 1 meaning
    # exactly one must be True (since both returning 1 would give sum=2, which fails).
    """
    r1 = 1 if sub_121109(serial) else 0
    r2 = 1 if sub_1211AB(serial) else 0
    return (r1 + r2) & 1 == 1


def keygen(name: str) -> str:
    """
    Generate a valid serial. Tries both code paths.
    Default: generate a short key via sub_121109 path (length 1).
    """
    # Path 1: length 1 (single character, sum = ord(c)-5, must be <=500, and serial[0]==serial[0] trivially)
    # Any single printable char works since even ord('~')=126 => 126-5=121 <=500
    # Just return a random printable char
    c = random.choice(PRINTABLES)
    return c


def keygen_full(name: str, length: int = None) -> str:
    """
    Generate a valid serial for a given length.
    length must be in [1,3,7,9,11,13,...] (odd, not multiple of 5) for path1,
    or 32 for path2.
    """
    if length is None:
        length = random.choice([1, 3, 7, 9, 11, 13])

    if length == 32:
        # path2: all digits, s1>=10, s2>=10, serial[30]=str(s2%s1), serial[31]='0'
        while True:
            key = ''
            s1 = 0
            s2 = 0
            for i in range(30):
                c = random.choice(DIGITS)
                key += c
                if i < 15:
                    s1 += int(c)
                else:
                    s2 += int(c)
            if s1 >= 10 and s2 >= 10 and s2 % s1 <= 9:
                key += str(s2 % s1) + '0'
                return key
    else:
        # path1: odd length, not multiple of 5, sum of ASCII -5 <= 500, serial[0]==serial[-1]
        if not ((length & 1) and (length % 5 != 0)):
            raise ValueError(f"Length {length} is not valid for path1")
        while True:
            key = ''
            s = -5
            for i in range(length):
                if length > 1 and i == length - 1:
                    c = key[0]  # last char must equal first
                else:
                    c = random.choice(PRINTABLES)
                key += c
                s += ord(c)
            if s <= 500:
                return key



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
